"""Streamlit session-state bootstrap — one encounter state + audit logger per
browser session, persisted across turns."""
from __future__ import annotations

import glob
import os

import streamlit as st

from models.encounter_state import EncounterState
from sample_data.ninds.manifest import get_clip_path, load_manifest
from services.audit_logger import AuditLogger
from workflows.loader import load_workflow

_NINDS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "ninds", "segmented")


def available_patients() -> list[str]:
    manifests = sorted(glob.glob(os.path.join(_NINDS_ROOT, "*", "manifest.json")))
    return [os.path.basename(os.path.dirname(m)) for m in manifests]


def init_session(patient_id: str) -> None:
    if st.session_state.get("patient_id") == patient_id and "encounter_state" in st.session_state:
        return

    workflow = load_workflow("nihss_screen")
    manifest = load_manifest(os.path.join(_NINDS_ROOT, patient_id, "manifest.json"))

    # Restrict the workflow to the items this patient actually has a cut clip for.
    # NINDS exams vary — e.g. Demo Patient A (1.3) folds 1b/1c into 1a, so there is no
    # 1b.mp4 — and a fixed 13-item sequence would march the planner into an item with no
    # video (FileNotFoundError in run_turn). "1 clip = 1 test": the session only steps
    # through the tests actually present (with a local clip) in THIS patient's data.
    available_ids = {
        it["item_id"] for it in manifest.get("items", [])
        if get_clip_path(manifest, it["item_id"]) is not None
    }
    available_steps = [s for s in workflow.examination_procedures if s.step_id in available_ids]
    if available_steps:
        workflow = workflow.model_copy(update={"examination_procedures": available_steps})

    first_step = min(workflow.examination_procedures, key=lambda s: s.sequence_number)

    st.session_state["patient_id"] = patient_id
    st.session_state["workflow"] = workflow
    st.session_state["manifest"] = manifest
    st.session_state["encounter_state"] = EncounterState(
        session_id=f"session_{patient_id}",
        workflow_id=workflow.workflow_id,
        current_item_id=first_step.step_id,
    )
    st.session_state["audit_logger"] = AuditLogger(session_id=f"session_{patient_id}")
    st.session_state["turn_count"] = 0
    st.session_state["turn_history"] = []
