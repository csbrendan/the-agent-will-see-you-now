# MedBridge: The Agent Will See You Now

**An audiovisual AI co-clinician for time-critical neurological screening and clinical workflow verification—from bedside to field.**

```text
              AUDIOVISUAL CLIP  (frame sequences + audio)
                    │                            │
              audio │                            │ frames
                    ▼                            ▼
        ┌────────────────────┐      ┌───────────────────────────┐
        │  LISTENER          │      │  VISUAL EVIDENCE EXTRACTOR │
        │  Whisper (local)   │      │  Claude Opus 4.8 (vision)  │
        │  speech→transcript │      │  frame seq → observations  │
        └─────────┬──────────┘      └─────────────┬─────────────┘
                  └───────────►  EVIDENCE  ◄───────┘   (source-attributed)
                                    │
                                    ▼
                          ENCOUNTER STATE   (validated by app code)
                                    │
                                    ▼
              CLINICAL PLANNER   ·  Claude Opus 4.8    → next NIHSS item / goal
                                    │
                                    ▼
              TALKER             ·  Claude Haiku 4.5   → one concise instruction
                                    │
                                    ▼
              SAFETY VERIFIER    ·  Claude Opus 4.8    → independent safety check
                                    │
                                    ▼
      approve · revise · block · EMERGENCY OVERRIDE · insufficient-evidence
                                    ▼
              clinician-reviewable guidance   +   escalation to a human
```

**Multi-agent safety architecture.** MedBridge is not one prompt — it is a pipeline of specialized
agents, each a **separate model call with its own prompt and typed (Pydantic) I/O**:

| Agent | Role | Model |
|---|---|---|
| **Listener** | audio → transcript for speech items (age/month questions, commands, naming, dysarthria) | **Whisper** — `faster-whisper base`, local, no GPU |
| **Visual Evidence Extractor** | frame **sequences** → source-attributed visual observations (facial asymmetry, arm drift *over time*, gaze) | **Claude Opus 4.8** (vision) · optional pose/CNN motion features |
| **Clinical Planner** | works the NIHSS one item at a time; tracks goals; picks the next step | **Claude Opus 4.8** (high effort) |
| **Talker** | turns the plan into one concise, calm instruction/question | **Claude Haiku 4.5** (fast) |
| **Safety Verifier** | independently checks the exact message; blocks unsupported "normal" calls; escalates red flags | **Claude Opus 4.8** (high effort) |
| **Response Router** | deterministic app code — decides what actually reaches the user | *(no model)* |

> **Safety-verified acute stroke screening from an audiovisual neuro exam.** A patient, bedside
> responder, or tele-neurology nurse captures a short **video clip — moving images *and* audio —**
> of a focused neurological exam. MedBridge's **multimodal Evidence Extractor** fuses **Claude vision
> over frame *sequences*** (facial asymmetry, arm *drift over time*, gaze tracking) with **Whisper
> over the audio** (speech clarity, naming, commands) into source-attributed evidence; the
> **Clinical Planner** works the NIH Stroke Scale one item at a time; the **Safety Verifier** refuses
> to call an exam "normal" without the evidence to support it and fires an **emergency escalation**
> on stroke red flags. Time-critical ✓ ("time is brain"), patient/responder-facing ✓, *safer* (a
> missed or over-claimed stroke finding is the liability the Verifier prevents) ✓ — grounded on the
> public-domain **NINDS NIHSS videos**, auto-segmented into **218 gold-labeled item clips**.
>
> **This is video understanding, not image classification.** The exam is inherently **audiovisual
> and temporal** — arm drift is a *trajectory over ~10s*, dysarthria is *speech*, gaze is *motion* —
> reasoned across ordered frame sequences + audio (plus spatio-temporal motion features where an item
> needs them) through an **independent multi-agent safety architecture**, not a single-prompt image
> analyzer or dashboard. See [concept.md](concept.md) and
> [research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md).

MedBridge is an open-source research prototype that uses multimodal AI to observe a simulated clinical encounter, maintain a structured encounter state, plan the next clinical goal, guide a patient or responder through one action at a time, and independently review its own instructions for safety before they are shown.

The system is inspired by AI co-clinician research that separates fast, natural interaction from slower, persistent clinical planning, and adds an independent safety-verification layer. It uses video frames, images, speech transcripts, user input, and structured encounter state to guide a focused clinical assessment.

MedBridge separates perception, state management, planning, communication, verification, response routing, and logging into **explicit, typed modules** rather than a single unconstrained clinical prompt:

- **Multimodal Evidence Extractor:** Converts frames, images, and transcripts into conservative, source-attributed observations.
- **Encounter State:** A structured record maintained outside the models; all changes are validated by application code.
- **Clinical Planner:** Persistent clinical reasoning and goal management; selects the next clinical goal (runs *before* the Talker).
- **Talker:** Gives concise, calm, one-action-at-a-time guidance to the user.
- **Safety Verifier:** Independently checks the exact proposed response for omissions, unsupported claims, unsafe instructions, and emergency red flags.
- **Response Router:** Approves, revises, blocks, or replaces the proposed response with an emergency override.

> **Canonical spec:** [`ProjectPlan.md`](ProjectPlan.md) is the authoritative product and architecture specification. Operational guidance for AI coding assistants lives in [`CLAUDE.md`](CLAUDE.md), and the agent-pipeline contract in [`AGENTS.md`](AGENTS.md). Where any document disagrees, ProjectPlan.md wins.

MedBridge is intended to support visual, time-sensitive workflows in both clinical and field environments, including hospitals, ambulances, remote locations, disaster-response settings, and advanced emergency kits.

> **Important:** MedBridge is an experimental hackathon and research prototype. It is not a medical device, has not been clinically validated, and must not replace emergency services, trained responders, or licensed medical professionals.

---

## Why MedBridge?

Most AI assistants generate an answer and send it directly to the user. That is not sufficient for safety-critical clinical workflows.

MedBridge separates fast user-facing guidance from persistent clinical planning and from independent safety review:

```text
Camera, uploaded video, image, and transcript
            │
            ▼
   Multimodal Evidence Extractor
     Source-attributed evidence (+ frame IDs)
            │
            ▼
        Encounter State
   Structured, validated by app code
            │
            ▼
       Clinical Planner
   Persistent goals · next clinical goal
            │
            ▼
         Talker Agent
   Proposed next action / question
            │
            ▼
       Safety Verifier
  Independent review of the exact message
            │
            ▼
 Approve · Revise · Block
   or Emergency Override
            │
            ▼
      Final user guidance
```

The central principle is:

> A clinically reasonable answer is not considered fully safe unless the system obtained the evidence required to support it.

For example, MedBridge should not report that a neurological examination is normal merely because no abnormality was obvious in a low-quality video. It must distinguish among:

- Directly observed (visible or audible) evidence
- User-reported information
- Model inference
- Uncertain or unavailable evidence

---

## Hackathon Scope

The initial prototype focuses on one visual, time-sensitive workflow implemented deeply rather than many workflows implemented superficially.

The **primary demonstration is neurological emergency screening**, because it clearly benefits from multimodal perception and persistent clinical goal management. A secondary CPR workflow may follow, but CPR is not the sole primary demonstration—it offers less opportunity to show persistent reasoning, dynamic goal selection, examination recovery, and multimodal evidence integration.

### Basic neurological and stroke screening (primary)

- Symptom onset and last-known-well time
- Speech assessment / speech clarity
- Facial symmetry observation
- Arm-drift guidance, with verification that both arms are visible
- Verification that the test lasted long enough
- Ability to follow simple commands
- Level of alertness
- Identification of uncertainty or asymmetry
- Recognition of red flags
- Immediate emergency escalation when indicated

### CPR support (secondary)

- Recognizing when emergency escalation is required
- Guiding responsiveness and breathing checks without unnecessary delay
- Prompting emergency-service activation and AED retrieval
- Assessing visible hand position and rescuer posture
- Detecting obvious interruptions in compressions
- Providing concise, one-action-at-a-time guidance
- Avoiding unsupported claims about pulse, exact compression depth, or physiological effectiveness

Future workflow definitions may cover:

- Respiratory-distress observation
- Inhaler-technique verification
- Recovery-position guidance
- Bleeding control
- Choking response
- Epinephrine autoinjector verification
- Trauma, burn, heat illness, or hypothermia assessment
- Emergency equipment verification

Implement one workflow deeply before adding another. MedBridge does not attempt general diagnosis or an unrestricted virtual doctor.

---

## Architecture

MedBridge uses explicit, typed modules rather than a single unconstrained clinical prompt.

```text
medbridge/
├── app.py
├── requirements.txt
├── .env.example
├── LICENSE
├── README.md
├── ProjectPlan.md
├── CLAUDE.md
├── AGENTS.md
│
├── config/
│   └── settings.py
│
├── agents/
│   ├── evidence_extractor.py
│   ├── clinical_planner.py
│   ├── talker.py
│   ├── safety_verifier.py
│   └── evaluator.py
│
├── api/
│   ├── claude_client.py
│   └── retry.py
│
├── models/
│   ├── media.py
│   ├── evidence.py
│   ├── clinical_goals.py
│   ├── encounter_state.py
│   ├── workflows.py
│   ├── agent_outputs.py
│   ├── events.py
│   └── evaluation.py
│
├── workflows/
│   ├── neurological_screen.yaml
│   ├── cpr.yaml
│   └── loader.py
│
├── prompts/
│   ├── evidence_extractor_system.md
│   ├── clinical_planner_system.md
│   ├── talker_system.md
│   ├── safety_verifier_system.md
│   └── evaluator_system.md
│
├── services/
│   ├── orchestration.py
│   ├── state_tracker.py
│   ├── goal_manager.py
│   ├── response_router.py
│   └── audit_logger.py
│
├── tools/
│   ├── clinical_tools.py
│   └── registry.py
│
├── video/
│   ├── processor.py
│   ├── quality.py
│   └── frame_store.py
│
├── audio/
│   └── transcription.py
│
├── ui/
│   ├── components.py
│   └── session_state.py
│
├── research_and_eval/
│   ├── dataset.py
│   ├── runner.py
│   ├── metrics.py
│   ├── report.py
│   └── scenarios/
│
├── sample_data/
│   ├── videos/
│   ├── frames/
│   └── transcripts/
│
└── tests/
    ├── test_models.py
    ├── test_state_tracker.py
    ├── test_goal_manager.py
    ├── test_response_router.py
    ├── test_video_processor.py
    └── test_safety_verifier.py
```

---

## Agent Pipeline

Each processing turn follows this sequence:

1. Capture or extract a timestamped frame and transcript window.
2. Evaluate basic image-quality limitations.
3. Send selected frames and workflow context to the Multimodal Evidence Extractor.
4. Convert the Extractor response into validated, source-attributed structured evidence.
5. Validate and merge evidence into the encounter state using deterministic application logic.
6. Run the Clinical Planner to select the next clinical goal.
7. Validate the Clinical Plan.
8. Ask the Talker for one clear next action or question.
9. Send the Talker proposal to the independent Safety Verifier.
10. Route the final response based on the Verifier decision.
11. Display the final guidance and supporting safety state.
12. Save structured events for replay and evaluation.

### Safety Verifier decisions

The Safety Verifier independently assesses the exact proposed response and returns one of the following. The **application**—not the Talker—determines what reaches the user:

| Decision | Behavior |
|---|---|
| `approve` | Display the Talker response |
| `revise` | Display the Verifier-corrected response |
| `block` | Suppress the unsafe response |
| `emergency_override` | Immediately display emergency guidance |
| `insufficient_evidence` | Request better evidence or human evaluation |

Both the original Talker proposal and the final displayed response are retained for auditability.

---

## Technology

- **Python**
- **Streamlit**
- **Anthropic Python SDK**
- **Claude multimodal Messages API**
- **OpenCV**
- **Pillow**
- **Pydantic**
- **Pandas**
- **PyYAML**
- **python-dotenv**

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/csbrendan/MedBridge.git
cd MedBridge
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Set the required values:

```dotenv
ANTHROPIC_API_KEY=your_api_key_here

MEDBRIDGE_EXTRACTOR_MODEL=your_extractor_model
MEDBRIDGE_PLANNER_MODEL=your_planner_model
MEDBRIDGE_TALKER_MODEL=your_talker_model
MEDBRIDGE_VERIFIER_MODEL=your_verifier_model
MEDBRIDGE_EVALUATOR_MODEL=your_evaluator_model

MEDBRIDGE_DEMO_MODE=true
MEDBRIDGE_LOG_LEVEL=INFO
MEDBRIDGE_FRAME_INTERVAL_SECONDS=1.0
MEDBRIDGE_MAX_VIDEO_SECONDS=120
```

Use a faster model configuration for the Talker when possible, and a more capable reasoning configuration for the Planner and Verifier when latency permits. Do not commit `.env` or API credentials.

---

## Running MedBridge

Start the Streamlit application:

```bash
streamlit run app.py
```

Then open the local address shown by Streamlit, commonly:

```text
http://localhost:8501
```

The interface supports:

- Workflow selection
- Sample or uploaded video
- Turn-by-turn frame processing
- Current clinical goal and Planner goals
- Talker guidance
- Safety Verifier review status
- Encounter state and workflow-step progress
- Red-flag and emergency alerts
- Evidence limitations and supporting frame IDs
- Raw structured agent outputs
- Latency and token-usage inspection
- Session-log export

---

## Demo Mode

Demo Mode uses a bundled, prerecorded synthetic scenario and advances through it one turn at a time.

It is designed to:

- Provide reliable, judge-friendly hackathon playback
- Make the multi-agent architecture easy to understand
- Demonstrate at least one Planner course correction
- Demonstrate at least one visible Verifier revision
- Demonstrate at least one emergency override
- Avoid depending entirely on live-camera quality or network timing

Demo Mode is prioritized before Live Mode. Any cached or prerecorded model output must be visibly labeled as cached. The application must not imply that cached output was generated live.

---

## Live Mode

Live Mode processes uploaded video, images, or webcam frames using active API calls, displays current latency, and handles network or API failures without crashing—falling back safely when a model output fails validation.

Because the current prototype operates on sampled images rather than continuous physiological sensing, it must not claim to reliably measure:

- Pulse
- Blood pressure
- Oxygen saturation
- Exact CPR compression depth or cadence
- Internal injury
- Neurological diagnosis
- Clinical stability
- Treatment effectiveness

The prototype is a **turn-based approximation** of a continuous audiovisual co-clinician and does not claim equivalence to native low-latency, continuous systems. Poor lighting, camera placement, occlusion, low frame rate, and network latency can substantially limit performance.

---

## Structured Workflows

Clinical procedures are represented as YAML configuration rather than being embedded entirely in prompts. The workflow engine combines deterministic safety constraints, configured examination procedures, and dynamically managed Planner goals—neither a completely rigid sequence nor an unrestricted model-invented procedure.

A workflow includes:

```yaml
workflow_id: neurological_screen
display_name: Neurological Emergency Screening
intended_user: bystander_or_responder
entry_conditions: []
required_inputs: []
initial_goals: []
allowed_goal_types: []
examination_procedures: []
expected_evidence: []
red_flags: []
escalation_rules: []
stop_conditions: []
prohibited_actions: []
completion_criteria: []
disclaimer: ""
```

Each examination step can specify:

```yaml
step_id: assess_arm_drift
sequence_number: 4
instruction: Ask the patient to hold both arms straight out, palms up, for ten seconds.
expected_visual_evidence: []
expected_user_confirmation:
  - Both arms are visible in frame
safety_critical: true
time_critical: false
prerequisites: []
failure_conditions: []
retry_instruction: Reposition the camera so both arms are fully visible, then repeat.
escalation_if_failed: emergency_override
```

Claude may propose workflow-state changes, but application code validates those changes before applying them.

---

## Structured Outputs

All module boundaries use Pydantic models. Prefer native structured outputs when supported; otherwise use forced tool calls whose JSON Schema mirrors the corresponding Pydantic model. Never extract JSON from arbitrary prose using regular expressions.

The Multimodal Evidence Extractor returns evidence such as:

```json
{
  "observed_actions": [],
  "possible_clinical_findings": [],
  "uncertain_findings": [],
  "image_quality_limitations": [],
  "confidence_by_finding": {},
  "evidence_frame_ids": []
}
```

The Talker returns:

```json
{
  "user_message": "Ask them to smile so we can see if both sides of the face move evenly.",
  "primary_action": "assess_facial_symmetry",
  "current_step_id": "assess_facial_symmetry",
  "proposed_completed_steps": [],
  "requested_observation": "face_centered_in_frame",
  "suspected_red_flags": [],
  "escalation_recommended": false,
  "evidence_references": [],
  "confidence": "medium"
}
```

The Safety Verifier returns:

```json
{
  "decision": "emergency_override",
  "is_safe": false,
  "emergency_detected": true,
  "critical_error_detected": true,
  "omitted_critical_actions": [
    "Immediate emergency-service activation"
  ],
  "required_corrections": [],
  "corrected_user_message": "Call emergency services now. This may be a stroke.",
  "escalation_level": "emergency",
  "should_interrupt": true,
  "should_call_emergency_services": true
}
```

On schema-validation failure: record the raw response, retry once with the validation error and schema, and if validation still fails return a safe typed fallback. Malformed or schema-invalid model output is never displayed directly to the user. Use enums for fixed decision and status fields.

---

## Evaluation

MedBridge includes an offline, replayable benchmark suite using synthetic scenarios.

Run it with:

```bash
python -m research_and_eval.runner
```

The benchmark suite should include:

- Correct workflow execution
- Missing critical steps
- Incorrect procedural order
- Ambiguous visual evidence
- Poor lighting or camera angle
- Conflicting video and user statements
- Multiple simultaneous errors
- Emergency red flags
- Sudden deterioration
- Hallucination traps
- Cases requiring a Verifier override
- Cases where no reliable visual conclusion is possible

Evaluate at least these system variants: (1) Talker only, (2) Talker plus Safety Verifier, (3) Talker plus Clinical Planner, and (4) the full system with Planner and Verifier.

Metrics include:

- Critical-step recall
- Red-flag recall
- Emergency-escalation recall
- False-escalation rate
- Unsupported-claim rate
- Errors of omission and commission
- Workflow-order accuracy
- Goal-persistence rate
- Incomplete-examination recovery
- Planner intervention rate
- Verifier intervention rate
- Verifier correction success and false-block rate
- Required-evidence / evidence-grounding accuracy
- Time to first critical instruction
- Extractor, Planner, Talker, Verifier, and end-to-end latency
- Estimated API usage

Deterministic scoring is used wherever gold labels exist. A separate blinded evaluator may score subjective qualities such as empathy, clarity, and naturalness, but LLM-as-a-judge results are not treated as clinical validation.

Reports are written to:

```text
research_and_eval/results/
├── scenario_results.jsonl
├── aggregate_metrics.json
└── validation_report.md
```

---

## Testing

Run the unit tests with:

```bash
python -m unittest discover -s tests
```

Or, when configured for `pytest`:

```bash
pytest -q
```

Tests should cover:

- Pydantic model validation
- Workflow loading
- Legal encounter-state transitions
- Clinical-goal management (add, suspend, resume, complete)
- Rejection of invented step IDs
- Response-routing decisions
- Safety Verifier emergency overrides
- Video-frame sampling
- Image-quality flags
- Safe fallback behavior
- API-error handling

---

## Privacy and Data Handling

The hackathon prototype should use synthetic, staged, de-identified, or explicitly consented demonstration data only.

Do not submit real patient information, protected health information, medical records, identifying images, or confidential clinical video unless the full deployment has appropriate authorization, contracts, privacy controls, retention settings, and security review.

Session logs may contain images, dialogue, inferred findings, and model output. Treat them as sensitive, even when created for demonstration purposes.

Recommended safeguards include:

- Local-only session storage by default
- No API keys or credentials in logs
- Configurable log retention
- Explicit consent before recording
- Session deletion controls
- Synthetic benchmark data
- No public release of identifiable patient media

---

## Safety Principles

MedBridge follows these implementation principles:

1. Emergency services and qualified human help take priority.
2. The system must not delay urgent lifesaving action while waiting for model analysis.
3. The system must distinguish observations from inference.
4. Unknown findings remain unknown.
5. Poor visual evidence must be surfaced explicitly.
6. The Talker should provide one primary action at a time.
7. The Safety Verifier independently evaluates every proposed instruction.
8. Unsupported completion of a clinical step is prohibited.
9. Correct outcomes reached without required evidence are not counted as fully safe.
10. The system must stop or escalate when the workflow exceeds its defined scope.

---

## Current Limitations

MedBridge is an early research prototype with significant limitations:

- It has not undergone clinical trials or prospective evaluation.
- It has not been cleared or approved as a medical device.
- Multimodal model output may be inaccurate or inconsistent.
- Ordinary video cannot establish many clinically important findings.
- Sparse frames may miss short or subtle events.
- API latency may make some emergency use cases impractical.
- The Safety Verifier is also model-based and may fail to detect unsafe output.
- Multi-agent agreement does not establish correctness.
- Benchmark results may not generalize to real patients or environments.
- The system is not suitable for autonomous diagnosis or treatment.

---

## Roadmap

- [ ] Complete the neurological-screening vertical slice
- [ ] Add structured multimodal evidence extraction
- [ ] Add persistent Clinical Planner goal management
- [ ] Add visible Verifier correction and emergency override
- [ ] Add deterministic encounter-state validation
- [ ] Add bundled sample videos and pre-extracted frames
- [ ] Add offline benchmark scenarios and ablation comparisons
- [ ] Add session replay and export
- [ ] Add a secondary CPR workflow
- [ ] Add speech-to-text
- [ ] Add text-to-speech
- [ ] Evaluate temporal video models
- [ ] Conduct clinician review
- [ ] Develop a formal safety case
- [ ] Explore edge-device and offline inference

---

## Contributing

Contributions are welcome, particularly in:

- Multimodal clinical evaluation
- Workflow definition and validation
- Human-factors design
- Emergency medicine
- Neurological assessment
- Model reliability and calibration
- Video understanding
- Privacy and security
- Edge inference
- Accessibility

Please open an issue before making major architectural or clinical-workflow changes.

Contributors must not add identifiable patient data, proprietary clinical media, or copyrighted benchmark material without documented permission.

---

## Responsible Use

Do not use MedBridge:

- As a replacement for emergency services or qualified medical care
- For autonomous diagnosis or treatment
- To make unsupervised medication or dosing decisions
- To falsely claim that a patient has been medically evaluated
- To provide reassurance that serious illness has been excluded
- In a production clinical setting without appropriate validation, governance, security, privacy, and regulatory review
- With real patient data unless the deployment is authorized and properly configured

---

## License

Copyright 2026 Brendan P. Murphy

Licensed under the Apache License, Version 2.0.

See [`LICENSE`](LICENSE) for the complete license text.

---

## Acknowledgments

MedBridge is inspired by research into multimodal AI co-clinicians, dual-agent safety architectures, visual clinical reasoning, and evidence-grounded clinical decision support.

MedBridge is an independent open-source research prototype and is not affiliated with or endorsed by Google DeepMind, Anthropic, any hospital, or any emergency-response organization.
