"""Clinical goal lifecycle management — pure, deterministic, no model calls.
Enforces the legal state-transition graph so a goal can't jump straight from
completed back to added, etc."""
from __future__ import annotations

import uuid

from models.clinical_goals import ClinicalGoal, GoalStatus
from models.encounter_state import EncounterState

_TERMINAL = {GoalStatus.COMPLETED, GoalStatus.ABANDONED, GoalStatus.SUPERSEDED_BY_EMERGENCY}

ALLOWED_TRANSITIONS: dict[GoalStatus, set[GoalStatus]] = {
    GoalStatus.ADDED: {GoalStatus.PRIORITIZED, GoalStatus.RETAINED, GoalStatus.SUSPENDED} | _TERMINAL,
    GoalStatus.PRIORITIZED: {GoalStatus.RETAINED, GoalStatus.SUSPENDED} | _TERMINAL,
    GoalStatus.RETAINED: {GoalStatus.PRIORITIZED, GoalStatus.SUSPENDED} | _TERMINAL,
    GoalStatus.SUSPENDED: {GoalStatus.RESUMED} | _TERMINAL,
    GoalStatus.RESUMED: {GoalStatus.PRIORITIZED, GoalStatus.RETAINED, GoalStatus.SUSPENDED} | _TERMINAL,
    GoalStatus.COMPLETED: set(),
    GoalStatus.ABANDONED: set(),
    GoalStatus.SUPERSEDED_BY_EMERGENCY: set(),
}


class IllegalGoalTransition(ValueError):
    pass


def is_legal_transition(current: GoalStatus, new: GoalStatus) -> bool:
    if current == new:
        return True
    return new in ALLOWED_TRANSITIONS.get(current, set())


def find_goal(state: EncounterState, goal_id: str) -> ClinicalGoal | None:
    return next((g for g in state.goals if g.goal_id == goal_id), None)


def find_goal_by_item(state: EncounterState, item_id: str) -> ClinicalGoal | None:
    return next((g for g in state.goals if g.item_id == item_id), None)


def add_goal(state: EncounterState, item_id: str, description: str, turn: int) -> ClinicalGoal:
    existing = find_goal_by_item(state, item_id)
    if existing is not None:
        return existing
    goal = ClinicalGoal(
        goal_id=f"goal_{uuid.uuid4().hex[:8]}",
        item_id=item_id,
        description=description,
        status=GoalStatus.ADDED,
        created_turn=turn,
        updated_turn=turn,
    )
    state.goals.append(goal)
    return goal


def transition_goal(state: EncounterState, goal_id: str, new_status: GoalStatus, turn: int, reason: str = "") -> ClinicalGoal:
    goal = find_goal(state, goal_id)
    if goal is None:
        raise IllegalGoalTransition(f"Unknown goal_id '{goal_id}'")
    if not is_legal_transition(goal.status, new_status):
        raise IllegalGoalTransition(f"Cannot transition goal '{goal_id}' from {goal.status} to {new_status}")
    goal.status = new_status
    goal.updated_turn = turn
    if new_status == GoalStatus.ABANDONED:
        goal.abandon_reason = reason
    return goal
