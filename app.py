"""MedBridge — thin Streamlit shell around the five-agent safety pipeline.
The UI is deliberately minimal: it steps through NIHSS items on real NINDS exam
video and shows what each agent decided. The agents are the feature, not the UI."""
import streamlit as st

from services.orchestration import run_turn
from ui.components import render_pipeline_diagram, render_turn
from ui.session_state import available_patients, init_session

st.set_page_config(page_title="MedBridge — NIHSS Screening", layout="wide")

st.title("MedBridge — Audiovisual NIHSS Screening")
st.caption(
    "Experimental research prototype. Not a medical device, not clinically validated, "
    "and not a replacement for emergency services or licensed clinical judgment."
)

patients = available_patients()
if not patients:
    st.error(
        "No segmented NINDS exam data found under sample_data/ninds/segmented/. "
        "Run sample_data/ninds/ninds_segmenter.py, ninds_clips.py, and ninds_audio.py first."
    )
    st.stop()

patient_id = st.sidebar.selectbox("Patient exam", patients)
init_session(patient_id)

render_pipeline_diagram()

state = st.session_state["encounter_state"]
workflow = st.session_state["workflow"]
manifest = st.session_state["manifest"]
logger = st.session_state["audit_logger"]

if state.emergency_status:
    st.error("ENCOUNTER STATUS: EMERGENCY")

if st.button("Run next turn", type="primary"):
    st.session_state["turn_count"] += 1
    with st.spinner("Running Evidence Extractor -> Planner -> Talker -> Safety Verifier..."):
        result = run_turn(state, workflow, manifest, st.session_state["turn_count"], logger)
    st.session_state["turn_history"].insert(0, result)

col1, col2 = st.columns([1, 1])
col1.metric("Current item", state.current_item_id)
col2.metric("Turn", st.session_state["turn_count"])

st.divider()

for result in st.session_state["turn_history"]:
    render_turn(result)
    st.divider()

with st.sidebar.expander("Encounter state (raw)"):
    st.json(state.model_dump(mode="json"))

with st.sidebar.expander("Audit log"):
    st.write(f"{len(logger.events)} events logged this session.")
    if st.download_button(
        "Export session log (JSONL)",
        data="\n".join(e.model_dump_json() for e in logger.events),
        file_name=f"{state.session_id}_events.jsonl",
    ):
        pass
