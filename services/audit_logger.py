"""Structured audit/event logging — one AuditEvent per processing stage per
turn, retaining both the original Talker output and the final displayed
message for auditability. Never logs API keys or unnecessary PII."""
from __future__ import annotations

import json
import os

from models.events import AuditEvent, TokenUsage, ValidationStatus


class AuditLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: list[AuditEvent] = []

    def log_stage(
        self,
        turn_id: int,
        workflow_id: str,
        module: str,
        meta: dict,
        active_goal_id: str | None = None,
        original_talker_message: str | None = None,
        final_displayed_message: str | None = None,
        errors: list[str] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            session_id=self.session_id,
            turn_id=turn_id,
            workflow_id=workflow_id,
            active_goal_id=active_goal_id,
            module=module,
            prompt_version=meta.get("prompt_version", ""),
            model=meta.get("model", ""),
            request_id=meta.get("request_id"),
            input_frame_ids=meta.get("input_frame_ids", []),
            input_transcript_ids=meta.get("input_transcript_ids", []),
            raw_output=meta.get("raw_response_text", "") or "",
            latency_ms=meta.get("latency_ms", 0.0),
            token_usage=TokenUsage(
                input_tokens=meta.get("input_tokens", 0),
                output_tokens=meta.get("output_tokens", 0),
            ),
            validation_status=(
                ValidationStatus.FALLBACK
                if meta.get("used_fallback")
                else ValidationStatus.RETRIED
                if meta.get("retried")
                else ValidationStatus.VALID
            ),
            errors=errors or [],
            original_talker_message=original_talker_message,
            final_displayed_message=final_displayed_message,
        )
        self.events.append(event)
        return event

    def to_jsonl(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            for event in self.events:
                f.write(event.model_dump_json() + "\n")
