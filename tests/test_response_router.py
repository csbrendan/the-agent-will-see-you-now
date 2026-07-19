import unittest

from models.agent_outputs import SafetyReview, TalkerOutput, VerifierDecision
from services.response_router import route


class TestResponseRouter(unittest.TestCase):
    def setUp(self):
        self.talker_output = TalkerOutput(
            user_message="Original talker message.",
            primary_action="assess_facial_symmetry",
            current_step_id="4",
        )

    def test_approve_displays_talker_message_unchanged(self):
        review = SafetyReview(decision=VerifierDecision.APPROVE, is_safe=True)
        routed = route(self.talker_output, review)
        self.assertEqual(routed.displayed_message, "Original talker message.")
        self.assertFalse(routed.is_emergency)

    def test_revise_displays_corrected_message(self):
        review = SafetyReview(decision=VerifierDecision.REVISE, is_safe=False, corrected_user_message="Corrected message.")
        routed = route(self.talker_output, review)
        self.assertEqual(routed.displayed_message, "Corrected message.")

    def test_block_suppresses_original_message(self):
        review = SafetyReview(decision=VerifierDecision.BLOCK, is_safe=False)
        routed = route(self.talker_output, review)
        self.assertNotEqual(routed.displayed_message, "Original talker message.")
        self.assertIn("suppressed", routed.displayed_message)

    def test_emergency_override_displays_emergency_instruction(self):
        review = SafetyReview(
            decision=VerifierDecision.EMERGENCY_OVERRIDE, is_safe=False, emergency_detected=True,
            corrected_user_message="Call emergency services now.",
        )
        routed = route(self.talker_output, review)
        self.assertEqual(routed.displayed_message, "Call emergency services now.")
        self.assertTrue(routed.is_emergency)

    def test_insufficient_evidence_uses_fallback_when_no_correction_given(self):
        review = SafetyReview(decision=VerifierDecision.INSUFFICIENT_EVIDENCE, is_safe=False)
        routed = route(self.talker_output, review)
        self.assertIn("insufficient", routed.displayed_message.lower())

    def test_original_talker_message_always_retained_for_audit(self):
        review = SafetyReview(decision=VerifierDecision.BLOCK, is_safe=False)
        routed = route(self.talker_output, review)
        self.assertEqual(routed.original_talker_message, "Original talker message.")


if __name__ == "__main__":
    unittest.main()
