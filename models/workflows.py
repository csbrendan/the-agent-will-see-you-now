"""Clinical workflow definitions — represented as validated config (YAML), not
embedded in prompts. See workflows/nihss_screen.yaml and workflows/loader.py."""
from __future__ import annotations

from pydantic import BaseModel, Field


class EscalationRule(BaseModel):
    red_flag: str
    escalation_level: str  # e.g. "emergency"
    instruction: str


class WorkflowStep(BaseModel):
    """Clinical procedure metadata only — modality/observability/sampling policy
    lives in video.processor.ITEM_PROFILES (the single source of truth), not
    here, so the two can never drift out of sync."""

    step_id: str
    sequence_number: int
    display_name: str
    instruction: str
    expected_visual_evidence: list[str] = Field(default_factory=list)
    expected_capture_confirmation: list[str] = Field(default_factory=list)
    safety_critical: bool = False
    time_critical: bool = False
    prerequisites: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    retry_instruction: str = ""
    escalation_if_failed: str | None = None  # e.g. "emergency_override"


class WorkflowDefinition(BaseModel):
    workflow_id: str
    display_name: str
    intended_user: str
    entry_conditions: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    initial_goals: list[str] = Field(default_factory=list)
    allowed_goal_types: list[str] = Field(default_factory=list)
    examination_procedures: list[WorkflowStep] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    escalation_rules: list[EscalationRule] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(default_factory=list)
    disclaimer: str = ""

    def step_ids(self) -> set[str]:
        return {s.step_id for s in self.examination_procedures}

    def step_by_id(self, step_id: str) -> WorkflowStep | None:
        return next((s for s in self.examination_procedures if s.step_id == step_id), None)
