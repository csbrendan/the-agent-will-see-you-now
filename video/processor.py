"""
MedBridge — Multimodal Evidence Extractor · frame-extraction stage (`video/processor.py`)
=========================================================================================

WHAT THIS MODULE IS
-------------------
The deterministic front door to perception. Given one **NIHSS exam item** (which test)
and the video it was captured in, it decides *what the model is even allowed to look at*
and hands back an ordered, timestamped, quality-checked bundle of frames (or, for speech
items, nothing — because there is nothing to see). It contains **no model calls and makes
no clinical judgement**; it only samples pixels and attaches provenance. Everything
clinical happens downstream in the Extractor → Planner → Talker → Verifier pipeline.

WHY IT IS NOT "just grab N frames" (read before editing)
--------------------------------------------------------
The NIHSS exam is **audiovisual and temporal**, and the three hard facts below are baked
into the sampling policy. Ignore them and the whole co-clinician silently degrades to a
single-image classifier.

  1. TEMPORAL, NOT SNAPSHOTS. For motor items the *signal is motion over time* — arm drift
     is a downward trajectory across a ~10 s hold, not a pose in one still. Three frames
     spread across a 60 s segment (the segmentation-validation sampling in
     `sample_data/ninds/ninds_segmenter.py`) physically cannot capture that and are NOT the
     payload we send the model. Temporal items get a *dense, ordered, timestamp-labelled*
     sequence so the reasoning core can infer the trajectory — and, for the hardest signals
     (drift, tremor), a local pose model should compute the quantity directly (see the
     `pose_recommended` flag and the POSE HOOK below). Ref: research_and_eval/NINDS_dataset.md §4.

  2. ORDER IS NOT FREE. Claude vision has no native video input; it sees a list of images.
     It only knows the temporal order and spacing that WE state. So every frame carries a
     `timestamp_s`, and `to_anthropic_content()` interleaves an explicit textual timeline
     ("frame 3 of 8 · t=6.0s") ahead of the images. Without this, "arms down → up → down"
     is indistinguishable from "up → down → up".

  3. OBSERVABILITY HAS LIMITS — AND WE DECLARE THEM. Some NIHSS items cannot be graded from
     ordinary video at all: **Sensory (8)** grades a *subjective* pinprick sensation, and
     **grip strength** is a *haptic* signal the examiner feels in their hand — no camera
     captures either. For those, the honest output is "not assessable from capture →
     requires a clinician", never a guess. That refusal is a feature, not a gap: it is
     exactly what the Safety Verifier exists to enforce, and it routes to
     `insufficient_evidence`. This module encodes that up front in `ITEM_PROFILES` so a
     never-observable item can never be silently scored.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
-----------------------------------------
  • No diagnosis, no scoring, no "normal/abnormal" — evidence only.
  • No inference of pulse, BP, SpO2, internal injury, or anything not on-screen.
  • No audio: speech items (1b/9/10) return zero frames with `modality == AUDIO`; the
    Listener (Whisper) handles those in a separate stage using the same segment window.

INPUT TIME BASE (a real foot-gun — read this)
---------------------------------------------
`start_s`/`end_s` in the gold manifest are offsets **within the full exam video**. The
per-item clips under `sample_data/.../segmented/<id>/<item>.mp4` are already trimmed to the
item, so their own time base starts at 0. `extract_for_item(..., window=...)` handles both:
pass `window=(start_s, end_s)` when sampling the FULL video; pass `window=None` (default)
for an already-trimmed clip and it samples across the clip's whole duration.

TYPING NOTE
-----------
The Pydantic models here (`ExtractedFrame`, `FrameBundle`) are the module boundary for now.
When `models/media.py` lands they should move there and be imported; the shapes are meant
to be stable, so downstream code should import them from `video.processor` until then.
"""

from __future__ import annotations

import base64
import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# OpenCV + NumPy are the only heavy deps. Fail loudly and usefully if the venv isn't set up,
# rather than with an opaque ImportError three frames into a demo.
try:
    import cv2
    import numpy as np
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "video.processor requires opencv-python-headless and numpy. "
        "Install deps into the venv: `pip install -r requirements.txt`."
    ) from exc


# --------------------------------------------------------------------------------------
# Item taxonomy — the observability + sampling policy, one row per NIHSS item.
# This table is the single source of truth for "what may we look at, and can we even
# assess this item from video?". Downstream code keys off `modality` / `observability`.
# --------------------------------------------------------------------------------------


class Modality(str, Enum):
    """Which sensor channel actually carries the signal for this item."""

    VISUAL = "visual"      # signal is in the frames (motion or asymmetry)
    AUDIO = "audio"        # signal is in speech → Whisper; frames add nothing
    MIXED = "mixed"        # needs frames AND the patient's spoken/pointing response
    CONTACT = "contact"    # graded via physical touch / examiner haptics → not on camera


class Observability(str, Enum):
    """How far ordinary video can be trusted for this item. Drives the Verifier's
    willingness to let a score through vs. routing to `insufficient_evidence`."""

    OBSERVABLE = "observable"          # the graded signal is genuinely on screen / in audio
    PARTIAL = "partial"                # maneuver is visible but the grade needs the
                                       # patient's response (report/pointing) too
    NOT_ASSESSABLE = "not_assessable"  # ordinary video cannot establish this — declare it


class SamplingProfile(str, Enum):
    """Frame-budget class. Concrete budgets live in FRAME_BUDGET so they can be tuned in one
    place. Temporal items use a frame RATE (not a flat total) — see FRAME_BUDGET."""

    NONE = "none"                    # 0 frames (speech items → audio path)
    STATIC = "static"                # a few stills: alertness, resting asymmetry
    SEMI_TEMPORAL = "semi_temporal"  # short maneuver (facial-during-smile): rate, small cap
    TEMPORAL = "temporal"            # motion over time (drift, gaze, ataxia): rate, large cap
    RECORD_ONLY = "record_only"      # a couple frames for the audit log on non-assessable items


class SamplingSpec(BaseModel):
    """How many frames a profile pulls. Either a fixed `count`, or a frame `fps` applied
    across the maneuver window and clamped to [1, max_frames]. Rate-based is the point for
    temporal items: a flat total is too sparse on a long clip (12 frames over 66s ≈ one every
    5.5s can't see a 10s drift), whereas a rate keeps sampling dense regardless of clip length."""

    count: Optional[int] = None      # fixed number of frames (used when fps is None)
    fps: Optional[float] = None      # frames per second across the window
    max_frames: int = 1              # hard cap — also keeps us under Claude's ~100 images/request

    def n_for(self, window_seconds: float) -> int:
        if self.count is not None:
            return max(0, self.count)
        if not self.fps or window_seconds <= 0:
            return 0
        return max(1, min(int(round(self.fps * window_seconds)), self.max_frames))


# Frame budget per profile. GENEROUS BY DESIGN: NINDS frames are ~100 tokens each, so we bias
# toward MORE coverage and accept the small extra API cost — for temporal items it is better to
# send too many frames than to miss the moment the arm hits the bed. Temporal/semi-temporal use
# a rate; the cap stays well under Claude's ~100-images/request ceiling. Tunable via env without
# touching the item table.
_TEMPORAL_FPS = float(os.environ.get("MEDBRIDGE_TEMPORAL_FPS", "2.5"))
_TEMPORAL_CAP = int(os.environ.get("MEDBRIDGE_TEMPORAL_MAX_FRAMES", "60"))

FRAME_BUDGET: dict[SamplingProfile, SamplingSpec] = {
    SamplingProfile.NONE: SamplingSpec(count=0),
    SamplingProfile.STATIC: SamplingSpec(count=4),
    SamplingProfile.SEMI_TEMPORAL: SamplingSpec(fps=2.5, max_frames=16),
    SamplingProfile.TEMPORAL: SamplingSpec(fps=_TEMPORAL_FPS, max_frames=_TEMPORAL_CAP),
    SamplingProfile.RECORD_ONLY: SamplingSpec(count=2),
}


class ItemProfile(BaseModel):
    """Immutable policy row for one NIHSS item."""

    item_id: str
    item_name: str
    modality: Modality
    observability: Observability
    sampling: SamplingProfile
    # True when a local pose/keypoint model should compute the quantitative signal
    # (wrist-height-vs-time = drift, tremor frequency) rather than relying on the vision
    # model to eyeball sub-pixel motion at 320x240. See POSE HOOK in extract_for_item().
    pose_recommended: bool = False
    # Operator-facing one-liner on why this item is limited, surfaced in evidence
    # limitations. Empty when fully observable.
    note: str = ""


# NIHSS item id → policy. `item_id` strings match the gold manifest exactly ("1a", "5", …).
# Rationale for the non-obvious rows is in the `note` field and echoed to the audit log.
ITEM_PROFILES: dict[str, ItemProfile] = {
    "1a": ItemProfile(
        item_id="1a", item_name="Level of Consciousness",
        modality=Modality.MIXED, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.STATIC,
        note="Alertness is visible; the examiner's questions/answers come via audio.",
    ),
    "1b": ItemProfile(
        item_id="1b", item_name="LOC Questions",
        modality=Modality.AUDIO, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.NONE,
        note="Speech item — graded from the transcript (age/month). Frames add nothing.",
    ),
    "1c": ItemProfile(
        item_id="1c", item_name="LOC Commands",
        modality=Modality.VISUAL, observability=Observability.PARTIAL,
        sampling=SamplingProfile.TEMPORAL,
        note="Command-following (open/close eyes, grip) is visible; grip STRENGTH is haptic "
             "and not on camera.",
    ),
    "2": ItemProfile(
        item_id="2", item_name="Best Gaze",
        modality=Modality.VISUAL, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.TEMPORAL,
        note="Gaze tracking is motion over time — needs an ordered sequence.",
    ),
    "3": ItemProfile(
        item_id="3", item_name="Visual Fields",
        modality=Modality.MIXED, observability=Observability.PARTIAL,
        sampling=SamplingProfile.TEMPORAL,
        note="Requires the patient's response (points/blinks to the moving finger); "
             "the maneuver is visible but the grade depends on that response.",
    ),
    "4": ItemProfile(
        item_id="4", item_name="Facial Palsy",
        modality=Modality.VISUAL, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.SEMI_TEMPORAL,
        note="Asymmetry is judged during smile/eyebrow-raise — needs baseline→active frames.",
    ),
    "5": ItemProfile(
        item_id="5", item_name="Motor Arm",
        modality=Modality.VISUAL, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.TEMPORAL, pose_recommended=True,
        note="Drift is a downward wrist trajectory over the ~10 s hold; scored per arm "
             "(5A/5B). Prefer pose keypoints over eyeballing low-res drift.",
    ),
    "6": ItemProfile(
        item_id="6", item_name="Motor Leg",
        modality=Modality.VISUAL, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.TEMPORAL, pose_recommended=True,
        note="Leg drift over the hold; scored per leg (6A/6B). Pose-preferred, as with arm.",
    ),
    "7": ItemProfile(
        item_id="7", item_name="Limb Ataxia",
        modality=Modality.VISUAL, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.TEMPORAL,
        note="Coordination during finger-nose / heel-shin; fine dysmetria is hard at 320x240 "
             "— flag low confidence rather than over-reading.",
    ),
    "8": ItemProfile(
        item_id="8", item_name="Sensory",
        modality=Modality.CONTACT, observability=Observability.NOT_ASSESSABLE,
        sampling=SamplingProfile.RECORD_ONLY,
        note="Grades a SUBJECTIVE pinprick sensation — not establishable from ordinary "
             "video. Emit 'requires clinician', never a guess.",
    ),
    "9": ItemProfile(
        item_id="9", item_name="Best Language",
        modality=Modality.AUDIO, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.NONE,
        note="Speech item — naming/reading graded from the transcript. Frames add nothing.",
    ),
    "10": ItemProfile(
        item_id="10", item_name="Dysarthria",
        modality=Modality.AUDIO, observability=Observability.OBSERVABLE,
        sampling=SamplingProfile.NONE,
        note="Speech item — slurring graded from audio. Frames add nothing.",
    ),
    "11": ItemProfile(
        item_id="11", item_name="Extinction/Inattention",
        modality=Modality.MIXED, observability=Observability.PARTIAL,
        sampling=SamplingProfile.TEMPORAL,
        note="Requires the patient to report which side(s) were touched — grade depends on "
             "that response, not just the maneuver.",
    ),
}


def profile_for(item_id: str) -> ItemProfile:
    """Look up the policy for a NIHSS item id, tolerating per-limb suffixes ('5a' → '5')."""
    key = item_id.strip().lower()
    if key in ITEM_PROFILES:
        return ITEM_PROFILES[key]
    # Motor items are scored per limb (5A/5B, 6A/6B) but share the base item's sampling.
    base = key.rstrip("ab")
    if base in ITEM_PROFILES:
        return ITEM_PROFILES[base]
    raise KeyError(
        f"Unknown NIHSS item id {item_id!r}. Known: {sorted(ITEM_PROFILES)}."
    )


# --------------------------------------------------------------------------------------
# Config knobs (env-overridable). A dedicated config/ module will centralise these later;
# for now they read from the environment with safe defaults so the module is self-contained.
# --------------------------------------------------------------------------------------

# Seconds to skip at the start of a FULL-video segment window to clear the on-screen title
# card / transition before sampling exam frames (mirrors the segmenter's 2 s card-skip).
_CARD_SKIP_S = float(os.environ.get("MEDBRIDGE_CARD_SKIP_SECONDS", "2.0"))
# Small margin trimmed off the tail of any window so we don't land on a cut/transition frame.
_TAIL_TRIM_S = float(os.environ.get("MEDBRIDGE_TAIL_TRIM_SECONDS", "0.3"))
# JPEG quality for the base64 payload. 80 is visually lossless at this resolution and keeps
# the encoded string small.
_JPEG_QUALITY = int(os.environ.get("MEDBRIDGE_JPEG_QUALITY", "80"))
# Quality-flag thresholds. Feed the Extractor's evidence-limitation reporting; they FLAG a
# frame, they never silently drop it (a discarded frame is unlogged evidence).
_DARK_MEAN_THRESHOLD = 40.0      # mean 0–255 luma below this → "too dark"
_BLUR_LAPLACIAN_THRESHOLD = 25.0  # variance-of-Laplacian below this → "blurred/soft"


# --------------------------------------------------------------------------------------
# Output models (module boundary — see TYPING NOTE in the module docstring).
# --------------------------------------------------------------------------------------


class ExtractedFrame(BaseModel):
    """One sampled frame plus its provenance and quality flags.

    `image_b64` is a base64 JPEG ready to drop into an Anthropic image content block. The
    `frame_index`/`timestamp_s` pair is what lets the reasoning core order the sequence."""

    frame_index: int = Field(..., description="0-based position within this bundle (temporal order).")
    timestamp_s: float = Field(..., description="Seconds into the SOURCE FILE this frame was taken.")
    image_b64: str = Field(..., description="Base64-encoded JPEG bytes (no data: URI prefix).")
    media_type: str = "image/jpeg"
    width: int
    height: int
    # Quality limitations for this frame — surfaced as evidence limitations downstream so the
    # Verifier can refuse to call an exam 'normal' on poor-quality capture.
    quality_flags: list[str] = Field(default_factory=list)


class FrameBundle(BaseModel):
    """The complete, source-attributed extraction result for one item.

    A bundle with `frames == []` is normal and expected for speech items (audio path) and is
    the correct shape for a NOT_ASSESSABLE item: the metadata still tells downstream code
    exactly why there is nothing to look at."""

    item_id: str
    item_name: str
    source_path: str
    modality: Modality
    observability: Observability
    pose_recommended: bool
    # Window (seconds, in the source file's own time base) the frames were sampled from.
    window_start_s: float
    window_end_s: float
    frames: list[ExtractedFrame] = Field(default_factory=list)
    # Human-readable limitations for the whole item (policy note + any extraction issues).
    limitations: list[str] = Field(default_factory=list)

    @property
    def assessable_from_video(self) -> bool:
        """False when this item can never be graded from capture (route to a clinician)."""
        return self.observability != Observability.NOT_ASSESSABLE

    @property
    def is_speech_item(self) -> bool:
        """True when the signal lives in audio and the Listener/Whisper stage owns this item."""
        return self.modality == Modality.AUDIO


# --------------------------------------------------------------------------------------
# Frame quality — conservative flags, never silent drops.
# --------------------------------------------------------------------------------------


def _assess_frame_quality(frame_bgr: "np.ndarray") -> list[str]:
    """Return a list of quality-limitation strings for a single BGR frame.

    Deliberately conservative and cheap: mean luma for exposure, variance-of-Laplacian for
    focus. These become evidence limitations — the point is to make poor capture *visible*
    to the Verifier, not to make a clinical call here."""
    flags: list[str] = []
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    mean_luma = float(gray.mean())
    if mean_luma < _DARK_MEAN_THRESHOLD:
        flags.append(f"low_light(mean_luma={mean_luma:.0f})")
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur < _BLUR_LAPLACIAN_THRESHOLD:
        flags.append(f"blurred(laplacian_var={blur:.0f})")
    return flags


def _encode_jpeg_b64(frame_bgr: "np.ndarray") -> str:
    """Encode a BGR frame to a base64 JPEG string (no data: URI prefix)."""
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY])
    if not ok:
        raise RuntimeError("cv2.imencode failed to JPEG-encode a frame.")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _sample_timestamps(start_s: float, end_s: float, n: int, skip_card: bool) -> list[float]:
    """Choose `n` evenly spaced sample times inside [start_s, end_s].

    Interior spacing (the k/(n+1) placement) avoids the very first/last frame of the window,
    which are the most likely to sit on a title card or a cut. `skip_card` adds the fixed
    lead-in used for FULL-video windows (trimmed clips already start on exam content).

    NOTE — uniform sampling is the honest v1. For temporal motor items the *right* thing is
    two-stage: sample densely, then use pose/frame-diff to find the ~10 s hold window and
    concentrate frames there. That is the POSE HOOK in extract_for_item(); until it lands we
    sample uniformly and label timestamps so nothing downstream assumes even spacing == the
    maneuver."""
    lead_in = _CARD_SKIP_S if skip_card else 0.0
    lo = min(start_s + lead_in, end_s)
    hi = max(lo, end_s - _TAIL_TRIM_S)
    if n <= 0 or hi <= lo:
        return []
    span = hi - lo
    return [round(lo + span * (k + 1) / (n + 1), 3) for k in range(n)]


# --------------------------------------------------------------------------------------
# Public API.
# --------------------------------------------------------------------------------------


def extract_for_item(
    video_path: str,
    item_id: str,
    item_name: Optional[str] = None,
    window: Optional[tuple[float, float]] = None,
    max_frames: Optional[int] = None,
) -> FrameBundle:
    """Extract the item-adaptive frame bundle for one NIHSS item.

    Args:
        video_path: Path to the source video — either the FULL exam or a pre-trimmed clip.
        item_id:    NIHSS item id ("1a", "5", "5a", …). Selects the sampling/observability policy.
        item_name:  Optional display name; falls back to the policy table's canonical name.
        window:     (start_s, end_s) in the FULL video's time base. Pass this when reading the
                    full exam. Pass None (default) for an already-trimmed per-item clip — the
                    whole clip is the window and no card-skip is applied.
        max_frames: Optional hard cap (e.g. to bound latency in a live demo). Never raises the
                    policy budget, only lowers it.

    Returns:
        A FrameBundle. For AUDIO/speech items and NOT_ASSESSABLE items it returns with
        `frames == []` and the reason in `limitations` — that empty bundle is the correct,
        expected result, not an error.

    Raises:
        FileNotFoundError: video_path does not exist.
        KeyError:          unknown item_id.
        RuntimeError:      the video could not be opened / decoded.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"video not found: {video_path}")

    profile = profile_for(item_id)
    display_name = item_name or profile.item_name
    limitations: list[str] = []
    if profile.note:
        limitations.append(profile.note)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {video_path}")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_s = (total_frames / fps) if total_frames > 0 else 0.0

        # Resolve the sampling window in the SOURCE FILE's own time base.
        if window is None:
            win_start, win_end = 0.0, duration_s
            skip_card = False  # trimmed clip: already starts on exam content
        else:
            win_start, win_end = float(window[0]), float(window[1])
            skip_card = True   # full video: clear the title card first

        # Decide the frame budget from the item policy (rate applied to the window length for
        # temporal items), then apply any caller cap.
        n_frames = FRAME_BUDGET[profile.sampling].n_for(win_end - win_start)
        if max_frames is not None:
            n_frames = min(n_frames, max_frames)

        bundle = FrameBundle(
            item_id=item_id,
            item_name=display_name,
            source_path=video_path,
            modality=profile.modality,
            observability=profile.observability,
            pose_recommended=profile.pose_recommended,
            window_start_s=round(win_start, 3),
            window_end_s=round(win_end, 3),
            limitations=limitations,
        )

        # Speech items: nothing to sample — the Listener/Whisper stage owns this item.
        if profile.modality == Modality.AUDIO or n_frames == 0:
            bundle.limitations.append("no frames extracted (audio-only item)")
            return bundle

        # POSE HOOK ---------------------------------------------------------------------
        # For pose_recommended temporal items (arm/leg drift, tremor) the reliable path is:
        #   1. sample densely here,
        #   2. run a local pose/keypoint model to get wrist/ankle height vs. time,
        #   3. concentrate frames on the detected hold window and attach the quantitative
        #      trajectory to the evidence.
        # Until the pose stage exists we still return a dense uniform sequence (below) so the
        # vision model can reason over the trajectory; we just flag that the quantitative
        # signal is not yet computed so downstream confidence stays honest.
        if profile.pose_recommended:
            bundle.limitations.append(
                "temporal motor item: quantitative drift/tremor via pose not yet computed — "
                "trajectory inferred from the frame sequence only (lower confidence)."
            )

        timestamps = _sample_timestamps(win_start, win_end, n_frames, skip_card)
        for idx, ts in enumerate(timestamps):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts * fps)))
            ok, frame_bgr = cap.read()
            if not ok or frame_bgr is None:
                # A missed seek is a real evidence gap — record it rather than silently
                # shrinking the sequence (which would misrepresent the maneuver's timing).
                bundle.limitations.append(f"frame_read_failed(t={ts:.2f}s)")
                continue
            h, w = frame_bgr.shape[:2]
            bundle.frames.append(
                ExtractedFrame(
                    frame_index=idx,
                    timestamp_s=ts,
                    image_b64=_encode_jpeg_b64(frame_bgr),
                    width=int(w),
                    height=int(h),
                    quality_flags=_assess_frame_quality(frame_bgr),
                )
            )

        if not bundle.frames:
            bundle.limitations.append("no frames could be read from the sampling window")
        return bundle
    finally:
        cap.release()


def to_anthropic_content(bundle: FrameBundle, instruction: Optional[str] = None) -> list[dict]:
    """Turn a FrameBundle into the `content` list for an Anthropic user message.

    Critically, this emits an explicit **textual timeline before the images** so the model
    knows the order and spacing it is looking at — Claude vision has no native notion of
    frame timing (see fact #2 in the module docstring). Frames are appended in temporal
    order, each preceded by its own "frame k · t=…s" label.

    Returns an empty content list only if you pass an empty bundle with no instruction; a
    speech/non-assessable bundle still yields a text block stating that there is nothing to
    view, so the caller never sends a silently empty turn."""
    content: list[dict] = []

    header_lines = [
        f"NIHSS item {bundle.item_id} — {bundle.item_name}.",
        f"Modality: {bundle.modality.value}. Observability: {bundle.observability.value}.",
    ]
    if not bundle.assessable_from_video:
        header_lines.append(
            "This item CANNOT be graded from video (contact/subjective). Do not infer a "
            "score; report that a clinician is required."
        )
    if bundle.frames:
        header_lines.append(
            f"{len(bundle.frames)} frames follow in temporal order, sampled from "
            f"{bundle.window_start_s:.1f}s–{bundle.window_end_s:.1f}s of the clip. "
            "Reason across the sequence (motion over time), not any single frame."
        )
    else:
        header_lines.append("No frames are attached (audio-only or not assessable from video).")
    if bundle.limitations:
        header_lines.append("Evidence limitations: " + "; ".join(bundle.limitations))
    if instruction:
        header_lines.append(instruction)
    content.append({"type": "text", "text": "\n".join(header_lines)})

    for fr in bundle.frames:
        label = f"frame {fr.frame_index + 1} of {len(bundle.frames)} · t={fr.timestamp_s:.1f}s"
        if fr.quality_flags:
            label += " · quality: " + ",".join(fr.quality_flags)
        content.append({"type": "text", "text": label})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": fr.media_type, "data": fr.image_b64},
        })
    return content


# --------------------------------------------------------------------------------------
# Smoke test — runs against a bundled NINDS clip if present. No API calls, no network.
#   ./.venv/bin/python -m video.processor
# --------------------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import json

    demo_clip = "sample_data/ninds/segmented/gov.hhs.ninds.stroke.1.4/5.mp4"  # Motor Arm, gold 5A=2/5B=1
    print(f"# smoke test — item 5 (Motor Arm) on {demo_clip}\n")

    if not os.path.exists(demo_clip):
        print(f"  (clip not present — regenerate sample_data or point at a real clip)\n"
              f"  showing the item policy table instead:\n")
        for pid, prof in ITEM_PROFILES.items():
            print(f"  {pid:3} {prof.item_name:26} {prof.modality.value:8} "
                  f"{prof.observability.value:15} {prof.sampling.value}")
    else:
        b = extract_for_item(demo_clip, item_id="5")
        # Print everything except the (huge) base64 payloads.
        summary = b.model_dump()
        summary["frames"] = [
            {k: v for k, v in f.items() if k != "image_b64"} for f in summary["frames"]
        ]
        print(json.dumps(summary, indent=2))
        print(f"\n  extracted {len(b.frames)} frames · assessable_from_video={b.assessable_from_video}")

        # Show the sensory item's refusal path (the safety beat).
        s = extract_for_item(demo_clip, item_id="8")  # Sensory — wrong clip on purpose; policy still applies
        print(f"\n  item 8 (Sensory): frames={len(s.frames)} · "
              f"assessable_from_video={s.assessable_from_video} · limitations={s.limitations}")
