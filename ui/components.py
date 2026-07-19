"""Thin rendering helpers. The agent pipeline and the Verifier's catch/correct
behavior are the visible substance here — the UI itself stays minimal."""
from __future__ import annotations

import base64

import streamlit as st

from models.agent_outputs import VerifierDecision
from services.orchestration import TurnResult

_DECISION_STYLE = {
    VerifierDecision.APPROVE: ("Approved", "success"),
    VerifierDecision.REVISE: ("Revised by Verifier", "warning"),
    VerifierDecision.BLOCK: ("Blocked", "error"),
    VerifierDecision.EMERGENCY_OVERRIDE: ("EMERGENCY OVERRIDE", "error"),
    VerifierDecision.INSUFFICIENT_EVIDENCE: ("Insufficient Evidence", "warning"),
}


def render_pipeline_diagram() -> None:
    st.code(
        "MULTIMODAL EVIDENCE\n"
        "  -> ENCOUNTER STATE\n"
        "  -> CLINICAL PLANNER\n"
        "  -> TALKER PROPOSAL\n"
        "  -> SAFETY VERIFIER\n"
        "  -> APPROVED / REVISED / BLOCKED / EMERGENCY",
        language=None,
    )


def render_clip(result: TurnResult) -> None:
    st.caption("Real NINDS exam footage — the item segment this turn's evidence was drawn from:")
    st.video(result.frame_bundle.source_path)


def render_frames(result: TurnResult) -> None:
    bundle = result.frame_bundle
    if not bundle.assessable_from_video:
        st.warning(
            f"Not assessable from video/audio ({bundle.observability.value}) — routed to a clinician "
            "by deterministic policy; no frames were sent to the model for this item."
        )
        return
    if not bundle.frames:
        st.caption("Speech item — no frames, audio transcript only.")
        return
    st.caption(f"{len(bundle.frames)} frames sampled from the clip above for the Evidence Extractor's vision call (showing first 5):")
    cols = st.columns(min(5, len(bundle.frames)))
    for i, frame in enumerate(bundle.frames[:5]):
        cols[i % len(cols)].image(
            base64.b64decode(frame.image_b64),
            caption=f"t={frame.timestamp_s:.1f}s" + (f" · {', '.join(frame.quality_flags)}" if frame.quality_flags else ""),
            width="stretch",
        )


def render_turn(result: TurnResult) -> None:
    st.subheader(f"Turn {result.turn_id} — {result.item_display_name} (item {result.item_id})")
    render_clip(result)
    render_frames(result)

    label, kind = _DECISION_STYLE.get(result.review.decision, ("Unknown", "error"))
    getattr(st, kind)(f"Verifier decision: **{label}**")

    st.markdown("**Final message shown to clinician:**")
    st.info(result.routed.displayed_message)

    with st.expander("Clinical Planner"):
        st.write("Next item:", result.plan.next_item_id, "| Action:", result.plan.action_type.value)
        st.write("Rationale:", result.plan.rationale)
        if result.plan.suspected_red_flags:
            st.error(f"Suspected red flags: {result.plan.suspected_red_flags}")
        if result.plan_rejections:
            st.warning(f"Rejected goal-update proposals (app-code safety net): {result.plan_rejections}")

    with st.expander("Talker proposal (before Verifier review)"):
        st.write(result.talker_output.user_message)

    with st.expander("Safety Verifier — full review"):
        st.json(result.review.model_dump(mode="json"))

    with st.expander("Evidence Extractor — raw structured output"):
        st.json(result.evidence.model_dump(mode="json"))

    with st.expander("Frame bundle metadata (sampling policy for this item)"):
        bundle = result.frame_bundle
        st.write(
            f"Modality: **{bundle.modality.value}** · Observability: **{bundle.observability.value}** · "
            f"Pose recommended: **{bundle.pose_recommended}**"
        )
        st.write(f"Window: {bundle.window_start_s:.1f}s – {bundle.window_end_s:.1f}s")
        if bundle.limitations:
            st.write("Limitations:", bundle.limitations)
