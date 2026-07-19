"""Safety Verifier — a separate model call with a separate prompt, run after the
Talker, never instructed to agree with it. Sonnet 5 by design (not the same
model as Extractor/Planner) to decorrelate failure modes and keep the per-turn
latency chain shorter, at high effort given the safety stakes."""
from __future__ import annotations

import os

from api.claude_client import call_structured
from config.settings import settings
from models.agent_outputs import SafetyReview, TalkerOutput, VerifierDecision
from models.encounter_state import EncounterState

_PROMPT_VERSION = "v1"
_SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "safety_verifier_system.md")
).read()


def _safe_fallback(state: EncounterState) -> SafetyReview:
    if state.red_flags or state.emergency_status:
        return SafetyReview(
            decision=VerifierDecision.EMERGENCY_OVERRIDE,
            is_safe=False,
            emergency_detected=True,
            corrected_user_message="Call emergency services now. This may require urgent evaluation.",
            escalation_level="emergency",
            should_interrupt=True,
            should_call_emergency_services=True,
            rationale="Safety Verifier call failed while red flags were already present in the encounter state — "
            "escalating rather than silently displaying an unverified message.",
        )
    return SafetyReview(
        decision=VerifierDecision.BLOCK,
        is_safe=False,
        critical_error_detected=True,
        rationale="Safety Verifier call failed — the Talker's message cannot be shown without independent review, "
        "so it is blocked rather than displayed unverified.",
    )


def review_message(
    talker_output: TalkerOutput,
    state: EncounterState,
    planner_rationale: str,
) -> tuple[SafetyReview, dict]:
    findings_summary = "\n".join(f"  - [{f.source.value}/{f.confidence.value}] {f.finding}" for f in state.findings[-10:]) or "  (none)"
    unresolved_summary = "\n".join(f"  - {f.finding}" for f in state.unresolved_findings[-10:]) or "  (none)"

    user_text = (
        f"Exact proposed clinician-facing message:\n\"{talker_output.user_message}\"\n\n"
        f"Talker's stated primary_action: {talker_output.primary_action}\n"
        f"Talker's proposed_completed_steps: {talker_output.proposed_completed_steps or 'none'}\n"
        f"Talker's suspected_red_flags: {talker_output.suspected_red_flags or 'none'}\n"
        f"Talker's escalation_recommended: {talker_output.escalation_recommended}\n"
        f"Talker's confidence: {talker_output.confidence}\n\n"
        f"Clinical Planner rationale that produced this: {planner_rationale}\n\n"
        f"Encounter state — recent findings:\n{findings_summary}\n\n"
        f"Encounter state — unresolved/uncertain findings:\n{unresolved_summary}\n\n"
        f"Encounter state — evidence-quality limitations: {state.evidence_quality_limitations or 'none'}\n"
        f"Encounter state — detected red flags: {state.red_flags or 'none'}\n"
        f"Encounter state — emergency_status: {state.emergency_status}\n"
    )

    fallback = _safe_fallback(state)

    result = call_structured(
        model=settings.verifier_model,
        system_prompt=_SYSTEM_PROMPT,
        user_content=[{"type": "text", "text": user_text}],
        output_model=SafetyReview,
        tool_name="record_safety_review",
        tool_description="Record the independent safety decision for the exact proposed message.",
        fallback=fallback,
        high_effort=True,
    )

    audit_meta = {
        "module": "safety_verifier",
        "prompt_version": _PROMPT_VERSION,
        "model": settings.verifier_model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "request_id": result.request_id,
        "retried": result.retried,
        "used_fallback": result.used_fallback,
    }
    return result.parsed, audit_meta
