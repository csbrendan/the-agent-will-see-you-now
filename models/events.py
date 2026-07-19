"""One structured audit event per processing stage, per turn. Never logs API keys or
unnecessary personal information."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    VALID = "valid"
    RETRIED = "retried"
    FALLBACK = "fallback"


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class AuditEvent(BaseModel):
    session_id: str
    turn_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workflow_id: str
    active_goal_id: str | None = None
    module: str  # e.g. "evidence_extractor", "clinical_planner", "talker", "safety_verifier"
    prompt_version: str
    model: str
    request_id: str | None = None
    input_frame_ids: list[str] = Field(default_factory=list)
    input_transcript_ids: list[str] = Field(default_factory=list)
    raw_output: str = ""
    parsed_output: dict = Field(default_factory=dict)
    validation_status: ValidationStatus = ValidationStatus.VALID
    latency_ms: float = 0.0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    errors: list[str] = Field(default_factory=list)
    original_talker_message: str | None = None
    final_displayed_message: str | None = None
