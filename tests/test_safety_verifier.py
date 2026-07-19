import unittest

from agents.safety_verifier import _safe_fallback
from models.agent_outputs import VerifierDecision
from models.encounter_state import EncounterState


class TestSafetyVerifierFallback(unittest.TestCase):
    """Covers the safe-typed-fallback path used when the Verifier API call itself
    fails validation twice — this must never silently approve a message."""

    def test_fallback_blocks_when_no_red_flags_present(self):
        state = EncounterState(session_id="s1", workflow_id="nihss_screen")
        review = _safe_fallback(state)
        self.assertEqual(review.decision, VerifierDecision.BLOCK)
        self.assertFalse(review.is_safe)

    def test_fallback_escalates_when_red_flags_already_present(self):
        state = EncounterState(session_id="s1", workflow_id="nihss_screen")
        state.red_flags = ["new facial droop"]
        review = _safe_fallback(state)
        self.assertEqual(review.decision, VerifierDecision.EMERGENCY_OVERRIDE)
        self.assertTrue(review.should_call_emergency_services)
        self.assertTrue(review.emergency_detected)

    def test_fallback_escalates_when_emergency_status_already_set(self):
        state = EncounterState(session_id="s1", workflow_id="nihss_screen")
        state.emergency_status = True
        review = _safe_fallback(state)
        self.assertEqual(review.decision, VerifierDecision.EMERGENCY_OVERRIDE)

    def test_fallback_never_approves(self):
        state_no_flags = EncounterState(session_id="s1", workflow_id="nihss_screen")
        state_with_flags = EncounterState(session_id="s2", workflow_id="nihss_screen", red_flags=["x"])
        for state in (state_no_flags, state_with_flags):
            review = _safe_fallback(state)
            self.assertNotEqual(review.decision, VerifierDecision.APPROVE)
            self.assertFalse(review.is_safe)


if __name__ == "__main__":
    unittest.main()
