import unittest

from models.agent_outputs import ClinicalPlan, GoalUpdateProposal, PlannerActionType
from models.encounter_state import EncounterState, EncounterStatus
from models.evidence import Confidence, EvidenceResponse, EvidenceSource, Observation
from services import state_tracker
from workflows.loader import load_workflow


class TestStateTracker(unittest.TestCase):
    def setUp(self):
        self.workflow = load_workflow("nihss_screen")
        self.state = EncounterState(session_id="s1", workflow_id="nihss_screen")

    def test_merge_evidence_with_usable_finding(self):
        evidence = EvidenceResponse(
            item_id="4",
            observed_actions=[
                Observation(finding="face symmetric", source=EvidenceSource.DIRECTLY_VISIBLE, confidence=Confidence.HIGH, evidence_frame_ids=["4_0"])
            ],
        )
        state_tracker.merge_evidence(self.state, evidence, turn=1)
        self.assertIn("4", self.state.items_with_evidence)
        self.assertEqual(len(self.state.findings), 1)
        self.assertNotIn("4", self.state.failed_or_uncertain_steps)

    def test_merge_evidence_with_no_usable_finding_marks_failed_or_uncertain(self):
        evidence = EvidenceResponse(
            item_id="5",
            uncertain_findings=[
                Observation(finding="cannot assess", source=EvidenceSource.UNKNOWN, confidence=Confidence.UNKNOWN)
            ],
        )
        state_tracker.merge_evidence(self.state, evidence, turn=1)
        self.assertIn("5", self.state.items_with_evidence)
        self.assertIn("5", self.state.failed_or_uncertain_steps)

    def test_reject_unknown_step_id(self):
        plan = ClinicalPlan(
            next_item_id="5", action_type=PlannerActionType.OBSERVE, rationale="",
            goal_updates=[GoalUpdateProposal(item_id="invented_step", new_status="completed")],
        )
        rejections = state_tracker.apply_clinical_plan(self.state, self.workflow, plan, turn=1)
        self.assertTrue(any("unknown step_id" in r for r in rejections))

    def test_reject_completion_without_evidence(self):
        plan = ClinicalPlan(
            next_item_id="5", action_type=PlannerActionType.OBSERVE, rationale="",
            goal_updates=[GoalUpdateProposal(item_id="4", new_status="completed")],
        )
        rejections = state_tracker.apply_clinical_plan(self.state, self.workflow, plan, turn=1)
        self.assertTrue(any("unsupported completion is prohibited" in r for r in rejections))

    def test_allow_completion_with_evidence(self):
        evidence = EvidenceResponse(
            item_id="4",
            observed_actions=[Observation(finding="ok", source=EvidenceSource.DIRECTLY_VISIBLE, confidence=Confidence.HIGH)],
        )
        state_tracker.merge_evidence(self.state, evidence, turn=1)
        plan = ClinicalPlan(
            next_item_id="5", action_type=PlannerActionType.OBSERVE, rationale="",
            goal_updates=[GoalUpdateProposal(item_id="4", new_status="completed")],
        )
        rejections = state_tracker.apply_clinical_plan(self.state, self.workflow, plan, turn=2)
        self.assertEqual(rejections, [])

    def test_reject_invalid_status_string(self):
        plan = ClinicalPlan(
            next_item_id="5", action_type=PlannerActionType.OBSERVE, rationale="",
            goal_updates=[GoalUpdateProposal(item_id="5", new_status="in_progress")],
        )
        rejections = state_tracker.apply_clinical_plan(self.state, self.workflow, plan, turn=1)
        self.assertTrue(any("invalid goal status" in r for r in rejections))

    def test_escalation_recommended_sets_emergency_status(self):
        plan = ClinicalPlan(
            next_item_id="5", action_type=PlannerActionType.ESCALATE, rationale="red flag",
            escalation_recommended=True, suspected_red_flags=["facial droop"],
        )
        state_tracker.apply_clinical_plan(self.state, self.workflow, plan, turn=1)
        self.assertTrue(self.state.emergency_status)
        self.assertEqual(self.state.status, EncounterStatus.EMERGENCY)
        self.assertIn("facial droop", self.state.red_flags)


if __name__ == "__main__":
    unittest.main()
