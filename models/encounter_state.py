"""Explicit encounter state — lives OUTSIDE the models. Application code is the only
thing that commits changes to this (see services/state_tracker.py); a model may only
propose a StateChangeProposal, never write here directly."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from models.clinical_goals import ClinicalGoal, GoalStatus
from models.evidence import Observation


class EncounterStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EMERGENCY = "emergency"
    ABORTED = "aborted"


class EncounterState(BaseModel):
    session_id: str
    workflow_id: str
    turn: int = 0

    current_item_id: str | None = None
    goals: list[ClinicalGoal] = Field(default_factory=list)

    findings: list[Observation] = Field(default_factory=list)
    unresolved_findings: list[Observation] = Field(default_factory=list)
    user_reported_symptoms: list[str] = Field(default_factory=list)
    failed_or_uncertain_steps: list[str] = Field(default_factory=list)
    # item_ids with at least one merged Evidence Extractor response — a goal may
    # only be marked completed if its item_id appears here (see services/state_tracker.py).
    items_with_evidence: list[str] = Field(default_factory=list)

    red_flags: list[str] = Field(default_factory=list)
    outstanding_questions: list[str] = Field(default_factory=list)
    evidence_quality_limitations: list[str] = Field(default_factory=list)

    emergency_status: bool = False
    current_instruction: str | None = None
    status: EncounterStatus = EncounterStatus.IN_PROGRESS
    last_update_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def goals_by_status(self, status: GoalStatus) -> list[ClinicalGoal]:
        return [g for g in self.goals if g.status == status]

    def active_goals(self) -> list[ClinicalGoal]:
        return [
            g
            for g in self.goals
            if g.status in (GoalStatus.ADDED, GoalStatus.PRIORITIZED, GoalStatus.RETAINED, GoalStatus.RESUMED)
        ]

    def known_item_ids(self) -> set[str]:
        return {g.item_id for g in self.goals}
