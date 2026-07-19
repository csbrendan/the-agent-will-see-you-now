"""Bounded retry helper for schema-validation failures. The Anthropic SDK already
retries transient network/429/5xx errors on its own (max_retries on the client) —
this module only covers the "model returned invalid JSON for our schema" case,
which ProjectPlan.md requires handling with exactly one retry before falling back."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class SchemaRetryExhausted(RuntimeError):
    pass


@dataclass
class AttemptResult:
    value: object
    raw_response_text: str
    retried: bool


def call_with_one_retry(
    attempt: Callable[[str | None], T],
) -> tuple[T, bool]:
    """Call `attempt(error_hint)` once with error_hint=None; on ValueError (schema
    validation failure), call it a second time with the error message as a hint.
    Raises SchemaRetryExhausted if the second attempt also fails."""
    try:
        return attempt(None), False
    except ValueError as first_error:
        try:
            return attempt(str(first_error)), True
        except ValueError as second_error:
            raise SchemaRetryExhausted(str(second_error)) from second_error
