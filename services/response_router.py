"""Response Router — deterministic application code, not a model. Decides what
actually reaches the clinician based on the Verifier's decision. This is the
enforcement point for 'the application, not any model, decides what reaches
the user.'"""
from __future__ import annotations

from dataclasses import dataclass

from models.agent_outputs import SafetyReview, TalkerOutput, VerifierDecision

_BLOCKED_PLACEHOLDER = (
    "The proposed guidance did not pass independent safety review and has been suppressed. "
    "Please continue the exam manually and consult another clinician if uncertain."
)
_INSUFFICIENT_EVIDENCE_PLACEHOLDER = (
    "Available evidence is insufficient to proceed safely. Please recapture with better visibility, "
    "or obtain a professional evaluation."
)


@dataclass
class RoutedResponse:
    decision: VerifierDecision
    displayed_message: str
    original_talker_message: str
    corrected_message: str | None
    is_emergency: bool


def route(talker_output: TalkerOutput, review: SafetyReview) -> RoutedResponse:
    if review.decision == VerifierDecision.APPROVE:
        displayed = talker_output.user_message
    elif review.decision == VerifierDecision.REVISE:
        displayed = review.corrected_user_message or talker_output.user_message
    elif review.decision == VerifierDecision.BLOCK:
        displayed = _BLOCKED_PLACEHOLDER
    elif review.decision == VerifierDecision.EMERGENCY_OVERRIDE:
        displayed = review.corrected_user_message or "Call emergency services now. This may be a medical emergency."
    elif review.decision == VerifierDecision.INSUFFICIENT_EVIDENCE:
        displayed = review.corrected_user_message or _INSUFFICIENT_EVIDENCE_PLACEHOLDER
    else:
        displayed = _BLOCKED_PLACEHOLDER

    return RoutedResponse(
        decision=review.decision,
        displayed_message=displayed,
        original_talker_message=talker_output.user_message,
        corrected_message=review.corrected_user_message,
        is_emergency=review.decision == VerifierDecision.EMERGENCY_OVERRIDE or review.emergency_detected,
    )
