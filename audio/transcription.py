"""Whisper (faster-whisper, local, no GPU) transcription for uploaded video, used
when a NINDS-style pre-computed manifest transcript isn't available. Lazily
loads the model since most turns (non-speech items) never need it."""
from __future__ import annotations

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_window(video_path: str, start_s: float, end_s: float) -> str:
    model = _get_model()
    segments, _info = model.transcribe(video_path, language="en", vad_filter=True)
    parts = [s.text.strip() for s in segments if s.end > start_s and s.start < end_s]
    return " ".join(parts).strip()
