"""Talker — fast, clinician-facing conversational agent. Converts the Planner's
selected goal into one concise instruction/question. Haiku 4.5: no adaptive
thinking / effort parameter (both error on this model tier), which is fine —
this is a narrow conversion task, not a reasoning-heavy one."""
from __future__ import annotations

import os

from api.claude_client import call_structured
from config.settings import settings
from models.agent_outputs import ClinicalPlan, TalkerOutput
from models.workflows import WorkflowDefinition

_PROMPT_VERSION = "v1"
_SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "talker_system.md")
).read()


def _safe_fallback(plan: ClinicalPlan) -> TalkerOutput:
    return TalkerOutput(
        user_message="I'm having trouble generating guidance right now — please pause and involve another clinician.",
        primary_action="pause_and_involve_clinician",
        current_step_id=plan.next_item_id,
        escalation_recommended=plan.escalation_recommended,
        confidence="low",
    )


def generate_message(
    plan: ClinicalPlan,
    workflow: WorkflowDefinition,
    verifier_feedback: str | None = None,
) -> tuple[TalkerOutput, dict]:
    step = workflow.step_by_id(plan.next_item_id)
    step_desc = f"{step.display_name}: {step.instruction}" if step else plan.next_item_id

    user_text = (
        f"Planner action_type: {plan.action_type.value}\n"
        f"Target NIHSS item: {step_desc}\n"
        f"Planner rationale: {plan.rationale}\n"
        f"Escalation recommended: {plan.escalation_recommended}\n"
        f"Suspected red flags: {plan.suspected_red_flags or 'none'}\n"
        f"Uncertainty notes: {plan.uncertainty_notes or 'none'}"
    )
    if verifier_feedback:
        user_text += f"\n\nPrevious Safety Verifier feedback on your last message: {verifier_feedback}"

    fallback = _safe_fallback(plan)

    result = call_structured(
        model=settings.talker_model,
        system_prompt=_SYSTEM_PROMPT,
        user_content=[{"type": "text", "text": user_text}],
        output_model=TalkerOutput,
        tool_name="record_talker_output",
        tool_description="Record the one concise clinician-facing instruction or question.",
        fallback=fallback,
        high_effort=False,
    )

    audit_meta = {
        "module": "talker",
        "prompt_version": _PROMPT_VERSION,
        "model": settings.talker_model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "request_id": result.request_id,
        "retried": result.retried,
        "used_fallback": result.used_fallback,
    }
    return result.parsed, audit_meta
