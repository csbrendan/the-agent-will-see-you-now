"""Typed application settings loaded from environment / .env. No model ID is ever
hardcoded outside this module — every other file reads MEDBRIDGE_* config through here."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    val = os.environ.get(name)
    return float(val) if val else default


def _get_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    return int(val) if val else default


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str

    extractor_model: str
    planner_model: str
    talker_model: str
    verifier_model: str
    evaluator_model: str

    demo_mode: bool
    log_level: str
    frame_interval_seconds: float
    max_video_seconds: int


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=_require("ANTHROPIC_API_KEY"),
        extractor_model=_require("MEDBRIDGE_EXTRACTOR_MODEL"),
        planner_model=_require("MEDBRIDGE_PLANNER_MODEL"),
        talker_model=_require("MEDBRIDGE_TALKER_MODEL"),
        verifier_model=_require("MEDBRIDGE_VERIFIER_MODEL"),
        evaluator_model=os.environ.get("MEDBRIDGE_EVALUATOR_MODEL", ""),
        demo_mode=_get_bool("MEDBRIDGE_DEMO_MODE", True),
        log_level=os.environ.get("MEDBRIDGE_LOG_LEVEL", "INFO"),
        frame_interval_seconds=_get_float("MEDBRIDGE_FRAME_INTERVAL_SECONDS", 1.0),
        max_video_seconds=_get_int("MEDBRIDGE_MAX_VIDEO_SECONDS", 120),
    )


settings = load_settings()
