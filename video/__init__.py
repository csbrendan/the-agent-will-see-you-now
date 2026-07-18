"""MedBridge video subsystem: item-adaptive frame extraction for the NIHSS workflow.

Public surface is intentionally small — most callers only need:

    from video.processor import extract_for_item, to_anthropic_content

See `video/processor.py` for the full contract and the per-item sampling policy.
"""
