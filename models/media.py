"""Frame/evidence-bundle shapes for the perception layer. Canonical home for
Modality/Observability/ExtractedFrame/FrameBundle — video/processor.py defines
the sampling *policy* (ItemProfile, SamplingProfile) and imports these output
shapes from here rather than owning them, so there is one module boundary
between "how frames were chosen" and "what the agent pipeline consumes"."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Modality(str, Enum):
    """Which sensor channel actually carries the signal for a NIHSS item."""

    VISUAL = "visual"      # signal is in the frames (motion or asymmetry)
    AUDIO = "audio"        # signal is in speech -> Whisper; frames add nothing
    MIXED = "mixed"        # needs frames AND the patient's spoken/pointing response
    CONTACT = "contact"    # graded via physical touch / examiner haptics -> not on camera


class Observability(str, Enum):
    """How far ordinary video can be trusted for this item. Drives the
    Verifier's willingness to let a score through vs. routing to
    insufficient_evidence."""

    OBSERVABLE = "observable"          # the graded signal is genuinely on screen / in audio
    PARTIAL = "partial"                # maneuver is visible but the grade needs the
                                        # patient's response (report/pointing) too
    NOT_ASSESSABLE = "not_assessable"  # ordinary video cannot establish this -- declare it


class TranscriptSegment(BaseModel):
    segment_id: str
    start_s: float
    end_s: float
    text: str


class ExtractedFrame(BaseModel):
    """One sampled frame plus its provenance and quality flags. `image_b64` is
    a base64 JPEG ready to drop into an Anthropic image content block."""

    frame_index: int = Field(..., description="0-based position within this bundle (temporal order).")
    timestamp_s: float = Field(..., description="Seconds into the SOURCE FILE this frame was taken.")
    image_b64: str = Field(..., description="Base64-encoded JPEG bytes (no data: URI prefix).")
    media_type: str = "image/jpeg"
    width: int
    height: int
    quality_flags: list[str] = Field(default_factory=list)


class FrameBundle(BaseModel):
    """The complete, source-attributed extraction result for one NIHSS item.

    A bundle with `frames == []` is normal and expected for speech items
    (audio path) and is the correct shape for a NOT_ASSESSABLE item: the
    metadata still tells downstream code exactly why there is nothing to look
    at. Audio/transcript content is NOT carried here — it's a separate
    concern (see TranscriptSegment) combined by the caller for AUDIO/MIXED
    items."""

    item_id: str
    item_name: str
    source_path: str
    modality: Modality
    observability: Observability
    pose_recommended: bool = False
    window_start_s: float
    window_end_s: float
    frames: list[ExtractedFrame] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @property
    def assessable_from_video(self) -> bool:
        """False when this item can never be graded from capture (route to a clinician)."""
        return self.observability != Observability.NOT_ASSESSABLE

    @property
    def is_speech_item(self) -> bool:
        """True when the signal lives in audio and the Listener/Whisper stage owns this item."""
        return self.modality == Modality.AUDIO
