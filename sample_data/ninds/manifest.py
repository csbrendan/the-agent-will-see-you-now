"""Reader/adapter for the gold manifest.json format written by ninds_segmenter.py,
ninds_clips.py, and ninds_audio.py. video/processor.py is deliberately dataset-agnostic
(it takes a video_path + item_id + window, not a manifest) — this module is the one
place that knows the NINDS manifest JSON schema, so that genericity isn't compromised."""
from __future__ import annotations

import json
import os
import re

# Leakage guard. In the two NINDS DEMONSTRATION exams, the examiner narrates the NIHSS
# score for the camera ("Nine is scored as a two", "total NIH stroke scale score is a
# 17"). That narration lands in the item's Whisper transcript. If it reached Claude, the
# model could read the answer straight off the audio instead of assessing the exam — and
# any score eval would be meaningless. `strip_scoring_narration()` removes ONLY those
# examiner scoring sentences, keeping the exam interaction (instructions + the patient's
# own responses, which speech items genuinely need). Certification-patient transcripts
# contain no score narration, so they pass through unchanged. The RAW transcript is left
# intact in the manifest — it is the eval gold; sanitization happens only on the way to
# the model (see get_transcript(..., for_model=True), used by the Evidence Extractor).
_SCORE_SENTENCE = re.compile(
    r"[^.?!]*\b(?:"
    r"scored?\s+(?:as\s+)?(?:a|an|him|her)?\s*(?:zero|one|two|three|four|\d)"   # "scored as a two"
    r"|scores?\s+(?:a|an|him|her)?\s*(?:zero|one|two|three|four|\d)"            # "he scores a one"
    r"|would\s+(?:get|score|be)\s+(?:a|an)?\s*(?:zero|one|two|three|four|\d)"   # "would score a zero"
    r"|got\s+(?:a|an)\s+(?:zero|one|two|three|four)\b"                          # "he got a zero" (not "got home")
    r"|nih\s+stroke\s+scale\s+score"                                            # "total NIH stroke scale score is a 17"
    r")[^.?!]*[.?!]",
    re.IGNORECASE,
)


def strip_scoring_narration(text: str) -> str:
    """Remove the examiner's post-hoc score commentary from an item transcript so the
    numeric NIHSS score (and its rationale) is never handed to the model. Sentence-level:
    a sentence is dropped only if it explicitly states/awards a score. Everything else —
    the examiner's instructions and the patient's responses — is preserved."""
    if not text:
        return text
    cleaned = _SCORE_SENTENCE.sub(" ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def load_manifest(manifest_path: str) -> dict:
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    # ninds_clips.py stores clip_path/audio_path relative to sample_data/ninds/segmented/
    manifest["_manifest_dir"] = os.path.dirname(os.path.dirname(os.path.abspath(manifest_path)))
    return manifest


def find_item(manifest: dict, item_id: str) -> dict | None:
    return next((it for it in manifest.get("items", []) if it["item_id"] == item_id), None)


def get_clip_path(manifest: dict, item_id: str) -> str | None:
    """Absolute path to the item's pre-cut video clip (ninds_clips.py cuts one per
    item, speech items included). Returns None rather than raising — callers
    should degrade gracefully if a clip is missing."""
    item = find_item(manifest, item_id)
    if item is None:
        return None
    clip_path = item.get("clip_path")
    seg_root = manifest.get("_manifest_dir")
    if clip_path and seg_root:
        candidate = os.path.join(seg_root, clip_path)
        if os.path.exists(candidate):
            return candidate
    return None


def get_transcript(manifest: dict, item_id: str, for_model: bool = False) -> str:
    """Whisper transcript text for the item's time window (ninds_audio.py slices
    the full-exam transcript by item timestamps for every item, not just speech
    items, as a byproduct of transcribing the whole video once).

    for_model=True strips the examiner's score narration (strip_scoring_narration) so the
    model never sees the answer — this is what the Evidence Extractor is fed. The default
    (for_model=False) returns the RAW transcript, which is the eval gold and audit record."""
    item = find_item(manifest, item_id)
    if item is None:
        return ""
    text = item.get("transcript", "") or ""
    return strip_scoring_narration(text) if for_model else text
