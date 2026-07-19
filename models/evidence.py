"""Source-attributed evidence produced by the Multimodal Evidence Extractor."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EvidenceSource(str, Enum):
    DIRECTLY_VISIBLE = "directly_visible"
    DIRECTLY_AUDIBLE = "directly_audible"
    USER_REPORTED = "user_reported"
    MODEL_INFERENCE = "model_inference"
    UNKNOWN = "unknown"
    CONTRADICTORY = "contradictory"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Observation(BaseModel):
    finding: str
    source: EvidenceSource
    confidence: Confidence
    evidence_frame_ids: list[str] = Field(default_factory=list)
    evidence_audio_segment_id: str | None = None
    notes: str = ""


class EvidenceResponse(BaseModel):
    """Structured output of the Evidence Extractor for one clinical item."""

    item_id: str
    observed_actions: list[Observation] = Field(default_factory=list)
    possible_clinical_findings: list[Observation] = Field(default_factory=list)
    uncertain_findings: list[Observation] = Field(default_factory=list)
    image_quality_limitations: list[str] = Field(default_factory=list)
    both_required_body_parts_visible: bool | None = None
    maneuver_duration_sufficient: bool | None = None
    evidence_frame_ids: list[str] = Field(default_factory=list)
