"""Clinical goal lifecycle managed by the Clinical Planner / Goal Manager."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GoalStatus(str, Enum):
    ADDED = "added"
    PRIORITIZED = "prioritized"
    RETAINED = "retained"
    SUSPENDED = "suspended"
    RESUMED = "resumed"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    SUPERSEDED_BY_EMERGENCY = "superseded_by_emergency"


class ClinicalGoal(BaseModel):
    goal_id: str
    item_id: str
    description: str
    status: GoalStatus = GoalStatus.ADDED
    priority: int = 0
    abandon_reason: str | None = None
    created_turn: int
    updated_turn: int
