"""The turn loop from AGENTS.md: extract -> merge -> plan -> validate -> talk ->
verify -> route -> log. Wires the five agents + Response Router together; no
model here decides what the clinician sees."""
from __future__ import annotations

from dataclasses import dataclass

from agents.clinical_planner import plan_next
from agents.evidence_extractor import extract_evidence
from agents.safety_verifier import review_message
from agents.talker import generate_message
from models.agent_outputs import ClinicalPlan, SafetyReview, TalkerOutput
from models.encounter_state import EncounterState
from models.evidence import EvidenceResponse
from models.media import FrameBundle
from models.workflows import WorkflowDefinition
from sample_data.ninds.manifest import get_clip_path, get_transcript
from services import state_tracker
from services.audit_logger import AuditLogger
from services.response_router import RoutedResponse, route
from video.processor import extract_for_item


@dataclass
class TurnResult:
    turn_id: int
    item_id: str
    item_display_name: str
    frame_bundle: FrameBundle
    evidence: EvidenceResponse
    plan: ClinicalPlan
    plan_rejections: list[str]
    talker_output: TalkerOutput
    review: SafetyReview
    routed: RoutedResponse


def run_turn(
    state: EncounterState,
    workflow: WorkflowDefinition,
    manifest: dict,
    turn_id: int,
    logger: AuditLogger,
) -> TurnResult:
    item_id = state.current_item_id or _first_step_id(workflow)
    step = workflow.step_by_id(item_id)
    if step is None:
        raise ValueError(f"current_item_id '{item_id}' is not a known workflow step")

    clip_path = get_clip_path(manifest, item_id)
    if clip_path is None:
        raise FileNotFoundError(
            f"No cut clip available for item '{item_id}' — run sample_data/ninds/ninds_clips.py"
        )

    # window=None: our clips are already trimmed per-item by ninds_clips.py, so
    # the whole clip file is the sampling window (see extract_for_item's docstring).
    bundle = extract_for_item(clip_path, item_id=item_id, item_name=step.display_name, window=None)
    # for_model=True strips the examiner's spoken NIHSS score from the transcript so the
    # model never reads the answer off the audio (leakage guard). The raw transcript stays
    # in the manifest as eval gold.
    transcript_text = get_transcript(manifest, item_id, for_model=True)

    evidence, extractor_meta = extract_evidence(bundle, transcript_text)
    logger.log_stage(turn_id, workflow.workflow_id, "evidence_extractor", extractor_meta)
    state_tracker.merge_evidence(state, evidence, turn_id)

    plan, planner_meta = plan_next(state, workflow)
    logger.log_stage(turn_id, workflow.workflow_id, "clinical_planner", planner_meta)
    rejections = state_tracker.apply_clinical_plan(state, workflow, plan, turn_id)

    talker_output, talker_meta = generate_message(plan, workflow)
    logger.log_stage(turn_id, workflow.workflow_id, "talker", talker_meta, original_talker_message=talker_output.user_message)

    review, verifier_meta = review_message(talker_output, state, plan.rationale)
    logger.log_stage(turn_id, workflow.workflow_id, "safety_verifier", verifier_meta)

    routed = route(talker_output, review)
    state.current_instruction = routed.displayed_message
    logger.log_stage(
        turn_id,
        workflow.workflow_id,
        "response_router",
        {"model": "", "prompt_version": ""},
        original_talker_message=talker_output.user_message,
        final_displayed_message=routed.displayed_message,
        errors=rejections,
    )

    return TurnResult(
        turn_id=turn_id,
        item_id=item_id,
        item_display_name=step.display_name,
        frame_bundle=bundle,
        evidence=evidence,
        plan=plan,
        plan_rejections=rejections,
        talker_output=talker_output,
        review=review,
        routed=routed,
    )


def _first_step_id(workflow: WorkflowDefinition) -> str:
    steps = sorted(workflow.examination_procedures, key=lambda s: s.sequence_number)
    if not steps:
        raise ValueError(f"workflow '{workflow.workflow_id}' has no examination_procedures")
    return steps[0].step_id
