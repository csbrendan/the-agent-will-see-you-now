import unittest

from models.clinical_goals import GoalStatus
from models.encounter_state import EncounterState
from services import goal_manager


class TestGoalManager(unittest.TestCase):
    def setUp(self):
        self.state = EncounterState(session_id="s1", workflow_id="nihss_screen")

    def test_add_goal_creates_new_goal(self):
        goal = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        self.assertEqual(goal.status, GoalStatus.ADDED)
        self.assertEqual(len(self.state.goals), 1)

    def test_add_goal_is_idempotent_per_item(self):
        g1 = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        g2 = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=2)
        self.assertEqual(g1.goal_id, g2.goal_id)
        self.assertEqual(len(self.state.goals), 1)

    def test_legal_transition_chain(self):
        goal = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.PRIORITIZED, turn=2)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.SUSPENDED, turn=3)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.RESUMED, turn=4)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.COMPLETED, turn=5)
        self.assertEqual(goal.status, GoalStatus.COMPLETED)

    def test_illegal_transition_from_terminal_state_rejected(self):
        goal = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.ABANDONED, turn=2)
        with self.assertRaises(goal_manager.IllegalGoalTransition):
            goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.RESUMED, turn=3)

    def test_illegal_transition_added_directly_to_resumed_rejected(self):
        goal = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        with self.assertRaises(goal_manager.IllegalGoalTransition):
            goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.RESUMED, turn=2)

    def test_transition_unknown_goal_id_rejected(self):
        with self.assertRaises(goal_manager.IllegalGoalTransition):
            goal_manager.transition_goal(self.state, "goal_does_not_exist", GoalStatus.COMPLETED, turn=1)

    def test_abandon_records_reason(self):
        goal = goal_manager.add_goal(self.state, "5", "Motor Arm", turn=1)
        goal_manager.transition_goal(self.state, goal.goal_id, GoalStatus.ABANDONED, turn=2, reason="patient left")
        self.assertEqual(goal.abandon_reason, "patient left")


if __name__ == "__main__":
    unittest.main()
