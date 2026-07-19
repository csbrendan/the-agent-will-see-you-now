"""Multimodal Evidence Extractor — fusion module. Claude vision reasons over the
ordered frame sequence built by video.processor.extract_for_item(); the Whisper
transcript is appended for AUDIO/MIXED items. Not a single vision call in
isolation — the input shape adapts to the item's modality and observability."""
from __future__ import annotations

import os

from api.claude_client import call_structured
from config.settings import settings
from models.evidence import Confidence, EvidenceResponse, EvidenceSource, Observation
from models.media import FrameBundle, Modality
from video.processor import to_anthropic_content

_PROMPT_VERSION = "v2"
_SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "evidence_extractor_system.md")
).read()


def _not_assessable_response(bundle: FrameBundle) -> tuple[EvidenceResponse, dict]:
    """NOT_ASSESSABLE is a deterministic clinical-policy fact (e.g. Sensory grades a
    subjective sensation no camera can capture), not something to ask a model to
    judge — so this never makes an API call. Matches the same principle as
    item-adaptive sampling: a model doesn't get to decide what it's allowed to
    look at or claim about something the policy already knows is unobservable."""
    response = EvidenceResponse(
        item_id=bundle.item_id,
        uncertain_findings=[
            Observation(
                finding=f"{bundle.item_name} is not assessable from ordinary video/audio.",
                source=EvidenceSource.UNKNOWN,
                confidence=Confidence.UNKNOWN,
                notes="Requires direct clinician evaluation — routed here by policy (video.processor.ITEM_PROFILES), "
                "not a model judgment.",
            )
        ],
        image_quality_limitations=list(bundle.limitations),
    )
    audit_meta = {
        "module": "evidence_extractor",
        "prompt_version": _PROMPT_VERSION,
        "model": "none (deterministic policy — NOT_ASSESSABLE)",
        "latency_ms": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "request_id": None,
        "retried": False,
        "used_fallback": False,
        "input_frame_ids": [],
        "input_transcript_ids": [],
    }
    return response, audit_meta


def extract_evidence(bundle: FrameBundle, transcript_text: str | None = None) -> tuple[EvidenceResponse, dict]:
    if not bundle.assessable_from_video:
        return _not_assessable_response(bundle)

    content = to_anthropic_content(bundle)
    if bundle.modality in (Modality.AUDIO, Modality.MIXED) and transcript_text:
        content.append({"type": "text", "text": f"Audio transcript for this item's window:\n{transcript_text}"})

    fallback = EvidenceResponse(
        item_id=bundle.item_id,
        image_quality_limitations=list(bundle.limitations) or ["extractor_call_failed"],
    )

    result = call_structured(
        model=settings.extractor_model,
        system_prompt=_SYSTEM_PROMPT,
        user_content=content,
        output_model=EvidenceResponse,
        tool_name="record_evidence",
        tool_description="Record conservative, source-attributed evidence for this NIHSS item.",
        fallback=fallback,
        high_effort=True,
    )

    parsed = result.parsed
    if isinstance(parsed, EvidenceResponse):
        parsed.item_id = bundle.item_id

    audit_meta = {
        "module": "evidence_extractor",
        "prompt_version": _PROMPT_VERSION,
        "model": settings.extractor_model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "request_id": result.request_id,
        "retried": result.retried,
        "used_fallback": result.used_fallback,
        "input_frame_ids": [f"{bundle.item_id}_{f.frame_index}" for f in bundle.frames],
        "input_transcript_ids": [f"{bundle.item_id}_audio"] if (bundle.modality in (Modality.AUDIO, Modality.MIXED) and transcript_text) else [],
    }
    return parsed, audit_meta
