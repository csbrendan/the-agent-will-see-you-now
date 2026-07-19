import unittest

from pydantic import ValidationError

from models.clinical_goals import ClinicalGoal, GoalStatus
from models.encounter_state import EncounterState, EncounterStatus
from models.media import FrameBundle, Modality, Observability
from models.workflows import WorkflowStep
from workflows.loader import load_workflow


class TestModels(unittest.TestCase):
    def test_encounter_state_defaults(self):
        state = EncounterState(session_id="s1", workflow_id="nihss_screen")
        self.assertEqual(state.status, EncounterStatus.IN_PROGRESS)
        self.assertEqual(state.goals, [])
        self.assertEqual(state.items_with_evidence, [])
        self.assertFalse(state.emergency_status)

    def test_goal_status_enum_rejects_invalid_value(self):
        with self.assertRaises(ValidationError):
            ClinicalGoal(
                goal_id="g1",
                item_id="4",
                description="test",
                status="in_progress",  # not a legal GoalStatus
                created_turn=0,
                updated_turn=0,
            )

    def test_goal_status_enum_accepts_legal_value(self):
        goal = ClinicalGoal(
            goal_id="g1", item_id="4", description="test",
            status=GoalStatus.SUSPENDED, created_turn=0, updated_turn=0,
        )
        self.assertEqual(goal.status, GoalStatus.SUSPENDED)

    def test_frame_bundle_speech_item_has_no_frames(self):
        bundle = FrameBundle(
            item_id="9", item_name="Best Language", source_path="x.mp4",
            modality=Modality.AUDIO, observability=Observability.OBSERVABLE,
            window_start_s=0.0, window_end_s=10.0,
        )
        self.assertEqual(bundle.frames, [])
        self.assertTrue(bundle.is_speech_item)
        self.assertTrue(bundle.assessable_from_video)

    def test_frame_bundle_not_assessable_flag(self):
        bundle = FrameBundle(
            item_id="8", item_name="Sensory", source_path="x.mp4",
            modality=Modality.CONTACT, observability=Observability.NOT_ASSESSABLE,
            window_start_s=0.0, window_end_s=10.0,
        )
        self.assertFalse(bundle.assessable_from_video)

    def test_workflow_loads_and_validates(self):
        wf = load_workflow("nihss_screen")
        self.assertEqual(wf.workflow_id, "nihss_screen")
        self.assertEqual(len(wf.examination_procedures), 13)
        self.assertIsInstance(wf.step_by_id("5"), WorkflowStep)
        self.assertIsNone(wf.step_by_id("nonexistent"))

    def test_workflow_step_ids_are_unique(self):
        wf = load_workflow("nihss_screen")
        ids = [s.step_id for s in wf.examination_procedures]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
