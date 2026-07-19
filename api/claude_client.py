"""Shared Anthropic Messages API wrapper used by every agent. Centralizes: forced
tool-call structured output + Pydantic validation, vision content blocks, latency
and token-usage tracking, and the schema-validation retry-then-fallback contract
required by ProjectPlan.md. Never regex JSON out of prose — every structured call
goes through a forced tool call whose schema mirrors the Pydantic model."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Type, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from api.retry import SchemaRetryExhausted, call_with_one_retry
from config.settings import settings

T = TypeVar("T", bound=BaseModel)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


@dataclass
class StructuredCallResult:
    parsed: BaseModel
    raw_response_text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    request_id: str | None
    retried: bool
    used_fallback: bool


def frame_image_block(base64_data: str, media_type: str = "image/jpeg") -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": base64_data},
    }


def _pydantic_tool_schema(model: Type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)
    schema["additionalProperties"] = False
    return schema


def call_structured(
    *,
    model: str,
    system_prompt: str,
    user_content: list[dict],
    output_model: Type[T],
    tool_name: str,
    tool_description: str,
    fallback: T,
    high_effort: bool = False,
    max_tokens: int = 4096,
) -> StructuredCallResult:
    """Force a single tool call whose schema mirrors `output_model`, validate the
    result, retry once on validation failure with the error appended, and fall
    back to `fallback` (a pre-built safe typed instance) if both attempts fail.
    `high_effort` must only be set for models that support adaptive thinking /
    effort (Opus 4.8, Sonnet 5) — Haiku 4.5 errors on those parameters."""

    tool = {
        "name": tool_name,
        "description": tool_description,
        "input_schema": _pydantic_tool_schema(output_model),
    }

    request_kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool_name},
    )
    if high_effort:
        request_kwargs["thinking"] = {"type": "adaptive"}
        request_kwargs["output_config"] = {"effort": "high"}

    last_usage = {"input_tokens": 0, "output_tokens": 0}
    last_raw_text = ""
    last_request_id: str | None = None

    def attempt(error_hint: str | None):
        nonlocal last_usage, last_raw_text, last_request_id
        messages = [{"role": "user", "content": user_content}]
        if error_hint:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous response did not validate against the required schema: "
                        f"{error_hint}\nCall {tool_name} again with corrected input."
                    ),
                }
            )

        start = time.monotonic()
        response = _client.messages.create(messages=messages, **request_kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        last_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        last_request_id = response._request_id
        last_raw_text = str(response.content)

        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is None:
            raise ValueError(f"Model did not call {tool_name}; stop_reason={response.stop_reason}")

        try:
            parsed = output_model.model_validate(tool_use.input)
        except ValidationError as e:
            raise ValueError(str(e)) from e

        return parsed, latency_ms

    try:
        (parsed, latency_ms), retried = call_with_one_retry(lambda hint: attempt(hint))
        return StructuredCallResult(
            parsed=parsed,
            raw_response_text=last_raw_text,
            input_tokens=last_usage["input_tokens"],
            output_tokens=last_usage["output_tokens"],
            latency_ms=latency_ms,
            request_id=last_request_id,
            retried=retried,
            used_fallback=False,
        )
    except SchemaRetryExhausted:
        return StructuredCallResult(
            parsed=fallback,
            raw_response_text=last_raw_text,
            input_tokens=last_usage["input_tokens"],
            output_tokens=last_usage["output_tokens"],
            latency_ms=0.0,
            request_id=last_request_id,
            retried=True,
            used_fallback=True,
        )
