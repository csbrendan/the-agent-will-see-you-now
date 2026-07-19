"""Clinical Planner — persistent clinical reasoning and goal management. Runs
before the Talker; produces structured guidance, never the final message."""
from __future__ import annotations

import os

from api.claude_client import call_structured
from config.settings import settings
from models.agent_outputs import ClinicalPlan, PlannerActionType
from models.encounter_state import EncounterState
from models.workflows import WorkflowDefinition

_PROMPT_VERSION = "v1"
_SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "clinical_planner_system.md")
).read()


def _first_unresolved_item(state: EncounterState, workflow: WorkflowDefinition) -> str:
    for step in sorted(workflow.examination_procedures, key=lambda s: s.sequence_number):
        if step.step_id not in state.items_with_evidence:
            return step.step_id
    return workflow.examination_procedures[0].step_id if workflow.examination_procedures else ""


def _safe_fallback(state: EncounterState, workflow: WorkflowDefinition) -> ClinicalPlan:
    if state.red_flags:
        return ClinicalPlan(
            next_item_id=state.current_item_id or _first_unresolved_item(state, workflow),
            action_type=PlannerActionType.ESCALATE,
            rationale="Planner call failed; red flags already detected in encounter state — escalating rather than guessing.",
            escalation_recommended=True,
            uncertainty_notes="Planner output unavailable; falling back to escalation given prior red flags.",
        )
    return ClinicalPlan(
        next_item_id=state.current_item_id or _first_unresolved_item(state, workflow),
        action_type=PlannerActionType.REQUEST_BETTER_EVIDENCE,
        rationale="Planner call failed; requesting better evidence rather than guessing the next step.",
        uncertainty_notes="Planner output unavailable — safe typed fallback.",
    )


def _summarize_state(state: EncounterState, workflow: WorkflowDefinition) -> str:
    steps = "\n".join(
        f"  - {s.step_id}: {s.display_name} (safety_critical={s.safety_critical}, time_critical={s.time_critical})"
        for s in sorted(workflow.examination_procedures, key=lambda s: s.sequence_number)
    )
    goals = "\n".join(f"  - {g.goal_id} item={g.item_id} status={g.status.value}" for g in state.goals) or "  (none yet)"
    findings = "\n".join(f"  - [{f.source.value}/{f.confidence.value}] {f.finding}" for f in state.findings[-10:]) or "  (none yet)"
    unresolved = "\n".join(f"  - {f.finding}" for f in state.unresolved_findings[-10:]) or "  (none)"

    return (
        f"Workflow items:\n{steps}\n\n"
        f"Current item under discussion: {state.current_item_id or 'none yet'}\n"
        f"Items with confirmed evidence: {state.items_with_evidence or 'none yet'}\n"
        f"Items flagged failed/uncertain: {state.failed_or_uncertain_steps or 'none'}\n"
        f"Goals:\n{goals}\n\n"
        f"Recent findings:\n{findings}\n\n"
        f"Unresolved/uncertain findings:\n{unresolved}\n\n"
        f"Detected red flags so far: {state.red_flags or 'none'}\n"
        f"Evidence-quality limitations so far: {state.evidence_quality_limitations or 'none'}\n"
        f"Emergency status: {state.emergency_status}\n"
    )


def plan_next(state: EncounterState, workflow: WorkflowDefinition) -> tuple[ClinicalPlan, dict]:
    fallback = _safe_fallback(state, workflow)

    result = call_structured(
        model=settings.planner_model,
        system_prompt=_SYSTEM_PROMPT,
        user_content=[{"type": "text", "text": _summarize_state(state, workflow)}],
        output_model=ClinicalPlan,
        tool_name="record_plan",
        tool_description="Record the next clinical goal and structured guidance for the Talker.",
        fallback=fallback,
        high_effort=True,
    )

    audit_meta = {
        "module": "clinical_planner",
        "prompt_version": _PROMPT_VERSION,
        "model": settings.planner_model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "request_id": result.request_id,
        "retried": result.retried,
        "used_fallback": result.used_fallback,
    }
    return result.parsed, audit_meta
