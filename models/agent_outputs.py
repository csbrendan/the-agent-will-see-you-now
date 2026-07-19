"""Structured outputs for the Clinical Planner, Talker, and Safety Verifier, plus the
narrow proposal shape a model uses to request an encounter-state change (application
code — not the model — decides whether to commit it)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PlannerActionType(str, Enum):
    ASK = "ask"
    GUIDE_EXAM = "guide_exam"
    OBSERVE = "observe"
    CLARIFY = "clarify"
    SUMMARIZE = "summarize"
    ESCALATE = "escalate"
    REQUEST_BETTER_EVIDENCE = "request_better_evidence"


class GoalUpdateProposal(BaseModel):
    goal_id: str | None = None  # None => propose a new goal
    item_id: str
    new_status: str
    reason: str = ""


class ClinicalPlan(BaseModel):
    """Clinical Planner output — structured guidance for the Talker, not the final
    clinician-facing message."""

    next_item_id: str
    action_type: PlannerActionType
    rationale: str
    goal_updates: list[GoalUpdateProposal] = Field(default_factory=list)
    unresolved_item_ids: list[str] = Field(default_factory=list)
    suspected_red_flags: list[str] = Field(default_factory=list)
    escalation_recommended: bool = False
    uncertainty_notes: str = ""


class TalkerOutput(BaseModel):
    user_message: str
    primary_action: str
    current_step_id: str
    proposed_completed_steps: list[str] = Field(default_factory=list)
    requested_observation: str | None = None
    suspected_red_flags: list[str] = Field(default_factory=list)
    escalation_recommended: bool = False
    evidence_references: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class VerifierDecision(str, Enum):
    APPROVE = "approve"
    REVISE = "revise"
    BLOCK = "block"
    EMERGENCY_OVERRIDE = "emergency_override"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SafetyReview(BaseModel):
    decision: VerifierDecision
    is_safe: bool
    emergency_detected: bool = False
    critical_error_detected: bool = False
    omitted_critical_actions: list[str] = Field(default_factory=list)
    required_corrections: list[str] = Field(default_factory=list)
    corrected_user_message: str | None = None
    escalation_level: str | None = None
    should_interrupt: bool = False
    should_call_emergency_services: bool = False
    rationale: str = ""
