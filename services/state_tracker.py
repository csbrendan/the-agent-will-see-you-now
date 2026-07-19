"""The Encounter State lives outside the models. This module is the only place
that commits changes to it: it merges Evidence Extractor output deterministically,
and validates every Clinical Planner goal proposal before applying it — rejecting
invented step IDs, illegal status transitions, and unsupported completions."""
from __future__ import annotations

from models.agent_outputs import ClinicalPlan
from models.clinical_goals import GoalStatus
from models.encounter_state import EncounterState, EncounterStatus
from models.evidence import EvidenceResponse
from models.workflows import WorkflowDefinition
from services import goal_manager


def merge_evidence(state: EncounterState, evidence: EvidenceResponse, turn: int) -> None:
    state.findings.extend(evidence.observed_actions)
    state.findings.extend(evidence.possible_clinical_findings)
    state.unresolved_findings.extend(evidence.uncertain_findings)

    for limitation in evidence.image_quality_limitations:
        if limitation not in state.evidence_quality_limitations:
            state.evidence_quality_limitations.append(limitation)

    if evidence.item_id not in state.items_with_evidence:
        state.items_with_evidence.append(evidence.item_id)

    has_usable_finding = bool(evidence.observed_actions or evidence.possible_clinical_findings)
    if not has_usable_finding and evidence.item_id not in state.failed_or_uncertain_steps:
        state.failed_or_uncertain_steps.append(evidence.item_id)
    elif has_usable_finding and evidence.item_id in state.failed_or_uncertain_steps:
        state.failed_or_uncertain_steps.remove(evidence.item_id)

    state.turn = turn


def apply_clinical_plan(
    state: EncounterState,
    workflow: WorkflowDefinition,
    plan: ClinicalPlan,
    turn: int,
) -> list[str]:
    """Validate and apply the Planner's proposed goal updates. Returns a list of
    human-readable rejection reasons for any proposal that was refused — the
    plan is never trusted blindly."""
    rejections: list[str] = []
    known_step_ids = workflow.step_ids()

    for proposal in plan.goal_updates:
        if proposal.item_id not in known_step_ids:
            rejections.append(f"rejected: unknown step_id '{proposal.item_id}' not in workflow")
            continue

        try:
            new_status = GoalStatus(proposal.new_status)
        except ValueError:
            rejections.append(f"rejected: invalid goal status '{proposal.new_status}' for item '{proposal.item_id}'")
            continue

        if new_status == GoalStatus.COMPLETED and proposal.item_id not in state.items_with_evidence:
            rejections.append(
                f"rejected: cannot mark '{proposal.item_id}' completed without merged evidence "
                f"(unsupported completion is prohibited)"
            )
            continue

        if proposal.goal_id is None:
            goal = goal_manager.add_goal(state, proposal.item_id, proposal.reason or proposal.item_id, turn)
            if new_status != GoalStatus.ADDED:
                try:
                    goal_manager.transition_goal(state, goal.goal_id, new_status, turn, proposal.reason)
                except goal_manager.IllegalGoalTransition as e:
                    rejections.append(f"rejected: {e}")
            continue

        try:
            goal_manager.transition_goal(state, proposal.goal_id, new_status, turn, proposal.reason)
        except goal_manager.IllegalGoalTransition as e:
            rejections.append(f"rejected: {e}")

    if plan.next_item_id in known_step_ids:
        state.current_item_id = plan.next_item_id

    for red_flag in plan.suspected_red_flags:
        if red_flag not in state.red_flags:
            state.red_flags.append(red_flag)

    if plan.escalation_recommended:
        state.emergency_status = True
        state.status = EncounterStatus.EMERGENCY

    state.turn = turn
    return rejections
