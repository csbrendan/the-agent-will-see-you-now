# MedBridge Project Instruction

> **Framing — Safety-verified acute stroke screening from an audiovisual neuro exam, for clinical
> use.** A **clinician** (nurse, resident, or attending) performs a focused neurological exam
> normally; MedBridge captures the resulting short **video clip — moving images *and* audio —** and
> its **multimodal Evidence Extractor** fuses **Claude vision over frame *sequences*** (facial
> asymmetry, arm *drift over time*, gaze) with **Whisper over the audio** (speech, naming, commands)
> into source-attributed evidence; the **Clinical Planner** works the NIH Stroke Scale one item at a
> time; the **Safety Verifier** refuses to call an exam "normal" without the evidence to support it
> and fires an **emergency escalation** on red flags. **This is audiovisual, temporal video
> understanding through an independent multi-agent safety architecture — NOT a single-prompt image
> classifier, RAG app, or dashboard** (see the hackathon anti-project rules in
> [HACKATHON.md](HACKATHON.md)). Dataset: the public-domain **NINDS NIHSS videos** (auto-segmented
> into 218 gold-labeled item clips, [research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md)).
> See also [concept.md](concept.md).
>
> *Note: sections below describe the general architecture. Where they say "neurological screening"
> read it as the audiovisual NIHSS workflow above; where they scope frame sampling, apply the
> item-adaptive / temporal budget from NINDS_dataset.md §4 (dense sequences for motion items, audio
> for speech items) rather than a flat frame count.*

> **Product vision — "document what you see, not what you say"** (from clinician/MD advice; full
> framing in [concept.md](concept.md)). The North Star is **ambient visual documentation of the
> physical exam**: a clinician wears smart-glasses and performs the exam *normally* while the agent
> observes, scores, and documents from what it sees — no dictation, no narration. NIHSS is the
> beachhead (structured, scored, gold-labeled), and the agent produces a **standardized preliminary
> score before the stroke team arrives**, which an off-site neurologist can remotely **"pass"**
> against the captured video. **The hackathon prototype runs this pipeline on pre-recorded NINDS
> video, not live glasses;** smart-glasses capture and EHR write-back are the productization path, not
> a claim the demo makes. *(This vision reframes the primary user toward the **clinician** and the
> agent's role toward **observe/score/document + escalate**; the Talker's user-facing guidance is
> being reconciled against it — see the open items tracked with the team.)*

You are the lead technical architect, clinical-safety designer, and implementation engineer for **MedBridge**, a multimodal, physician-supervised clinical guidance prototype being built for an AI hackathon.

MedBridge is inspired by Google DeepMind’s AI co-clinician architecture. It separates fast, natural interaction from slower, persistent clinical planning and adds an independent safety-verification layer. The system uses video, images, speech transcripts, clinician input, and structured encounter state to observe and document a clinician-performed focused clinical assessment.

The primary objective is to build a convincing, reliable, inspectable end-to-end demonstration—not a production medical device.

MedBridge must remain an experimental research prototype. It must not autonomously diagnose, prescribe, change medications, replace emergency services, or represent itself as medically validated.

## Project Independence

MedBridge is an independent project and should be treated as a standalone multimodal clinical-agent prototype.

It may borrow ideas from medication-safety verifiers, clinical RL, refill triage, structured rubrics, and verifier-based training, but it must not be framed as merely an extension of a separate medication or prescribing project.

The hackathon prototype should focus on visual and conversational clinical guidance where multimodal perception provides clear value.

## Core Product Concept

MedBridge observes a simulated clinical encounter through a camera or uploaded video, listens to or receives the user’s statements, maintains a structured encounter state, determines the most important clinical goal, provides one concise instruction or question, and independently checks that instruction before displaying it.

The preferred architecture is:

Camera, uploaded video, image, and transcript
→ multimodal evidence extraction
→ structured encounter-state update
→ Clinical Planner
→ Talker
→ Safety Verifier
→ approved, corrected, blocked, or emergency response
→ user interface
→ structured audit and evaluation logs

Do not implement MedBridge as one large prompt or one unconstrained agent.

Separate perception, state management, planning, communication, verification, response routing, and logging into explicit modules with typed interfaces.

## Architectural Roles

### 1. Multimodal Evidence Extractor

The Multimodal Evidence Extractor converts timestamped video frames, images, speech transcripts, and user statements into conservative, source-attributed observations.

It must distinguish among:

* Directly visible evidence
* Directly audible evidence
* User-reported information
* Model inference
* Unknown or unobservable information
* Contradictory evidence
* Poor-quality or incomplete evidence

Every visual finding should reference the frame IDs supporting it.

The extractor must not diagnose, select treatment, or instruct the user. Its role is evidence extraction only.

It must never infer information such as pulse, blood pressure, oxygen saturation, exact compression depth, internal injury, medication dose, or definitive diagnosis from ordinary video.

When evidence is blocked, blurred, off-camera, too brief, poorly illuminated, or temporally ambiguous, mark it as uncertain or unknown rather than guessing.

### 2. Encounter State

Maintain an explicit, structured encounter state outside the language models.

The state should include:

* Active workflow
* Current clinical concern
* Gathered findings
* Unresolved findings
* User-reported symptoms
* Visible or audible observations
* Active clinical goals
* Completed goals
* Suspended goals
* Failed or uncertain examination steps
* Detected red flags
* Outstanding questions
* Evidence-quality limitations
* Emergency status
* Current user-facing instruction
* Encounter status
* Last update time

Models may propose state changes, but application code must validate all changes before committing them.

Do not allow a model to invent unsupported workflow steps, findings, examination results, or completed actions.

An instruction being issued does not mean the action was completed.

### 3. Clinical Planner

The Clinical Planner is the persistent clinical reasoning and goal-management agent.

It operates before the Talker.

Its responsibilities are to:

* Maintain a compact working model of the encounter
* Identify unresolved and safety-critical information
* Screen for workflow-specific red flags
* Prioritize the next clinical goal
* Decide whether to ask a question, guide an examination, observe, clarify, summarize, or escalate
* Retain incomplete goals across interruptions
* Resume unfinished examinations
* Request better evidence when required
* Recognize when evidence is insufficient
* Recommend escalation when uncertainty or urgency requires it
* Prevent the interaction from drifting outside the selected workflow

The Planner must manage dynamic clinical goals rather than simply advance through a rigid checklist.

Clinical goals may be:

* Added
* Prioritized
* Retained
* Suspended
* Resumed
* Completed
* Abandoned with a documented reason
* Superseded by emergency escalation

The Planner must not directly produce the final patient-facing response. It produces structured guidance for the Talker.

The Planner must make uncertainty explicit and avoid presenting a differential hypothesis as a diagnosis.

### 4. Talker

The Talker is the fast, user-facing conversational agent.

It receives:

* The current Clinical Plan
* Structured encounter state
* Recent evidence
* A short rolling conversation window
* The latest user transcript
* Known evidence limitations
* Previous verifier feedback when relevant

The Talker converts the Planner’s selected goal into a concise, natural instruction or question.

Its messages must be:

* Short
* Direct
* Calm
* Easy to follow under stress
* Focused on one primary action at a time
* Free of unnecessary technical language
* Explicit about uncertainty
* Explicit about emergency escalation when required

The Talker should generally avoid asking several questions at once.

It should request visual repositioning, repetition, or verbal confirmation when evidence is insufficient, unless doing so would delay a critical lifesaving action.

The Talker must never claim that:

* A workflow step was completed merely because it was requested
* A visual finding is confirmed without supporting evidence
* The system can rule out a serious condition
* The system has made a diagnosis
* The system has measured an unobservable vital sign
* Emergency or professional care is unnecessary without adequate evidence

### 5. Safety Verifier

The Safety Verifier is a separate model call with a separate prompt and structured output.

It operates after the Talker proposes a patient-facing response.

It must independently assess the exact proposed response and must not be instructed to agree with the Talker.

The Verifier checks for:

* Failure to recommend emergency help when required
* Delay of a time-critical action
* Dangerous procedural ordering
* Unsupported visual or clinical claims
* Hallucinated completion of steps
* Missing critical questions or instructions
* Failure to acknowledge poor evidence
* Contradiction with the encounter state
* Unsupported reassurance
* Diagnosis or treatment claims outside project scope
* Medication, prescribing, or dosing advice
* Instructions that exceed the selected workflow
* Excessively long instructions during an emergency
* Failure to escalate uncertain or high-risk cases

Allowed Verifier decisions are:

* Approve
* Revise
* Block
* Emergency override
* Insufficient evidence

The application—not the Talker—determines what reaches the user:

* Approve: display the Talker response
* Revise: display the Verifier-corrected response
* Block: suppress the unsafe response
* Emergency override: immediately display the emergency instruction
* Insufficient evidence: request better evidence or professional evaluation

Store the original Talker output, Verifier decision, corrected output, and final displayed response for auditability.

## Medical Direction

The first hackathon workflow should be a focused **neurological emergency screening demonstration**, because it clearly benefits from multimodal perception and persistent clinical goal management.

A strong scenario should include:

* Symptom onset and last-known-well time
* Speech assessment
* Facial symmetry observation
* Arm-drift guidance
* Verification that both arms are visible
* Verification that the test lasted long enough
* Identification of uncertainty or asymmetry
* Recognition of red flags
* Immediate emergency escalation when indicated

The engine is workflow-agnostic, so once the NIHSS workflow is solid the same observe → document →
safety-verify loop extends to other **clinical, visible physical-exam findings** captured during
normal care.

Other acceptable future clinical workflows include:

* Ward-rounds exam documentation
* Skin / wound / lesion observation
* Other structured neurological and physical-exam maneuvers

For the hackathon, implement one workflow deeply before adding another.

Do not attempt general diagnosis or an unrestricted virtual doctor. MedBridge is **assistive** — the
clinician remains the accountable decision-maker.

## Medical Safety Boundaries

MedBridge must not:

* Diagnose a patient
* Rule out a serious condition
* Prescribe medication
* Recommend a medication dose
* Change an existing medication
* Tell a user to stop medication
* Tell a user to ignore clinician advice
* Replace emergency services
* Claim medical-device status
* Claim clinical validation
* Claim production readiness
* Provide autonomous treatment decisions
* Conceal uncertainty or evidence limitations

The system may:

* Ask structured questions
* Guide a simulated examination
* Identify possible red flags
* State what it can and cannot observe
* Recommend contacting emergency services
* Recommend evaluation by a licensed clinician
* Produce a clinician-reviewable encounter summary
* Demonstrate workflow and verifier behavior using synthetic scenarios

All demonstrations should use synthetic, staged, consented, or non-patient data.

## Real-Time Processing Strategy

Do not attempt unrestricted continuous-video understanding during the first prototype.

Use a controlled processing loop:

1. Capture or extract a timestamped frame and transcript window.
2. Run the Multimodal Evidence Extractor.
3. Validate and merge evidence into encounter state.
4. Run the Clinical Planner.
5. Validate the Clinical Plan.
6. Run the Talker.
7. Run the Safety Verifier.
8. Route the approved or corrected response.
9. Update state and logs.
10. Continue to the next turn.

The prototype should be described as a turn-based approximation of a continuous audiovisual co-clinician.

Do not claim equivalence to native low-latency, continuous audiovisual systems.

Use approximately one sampled frame per second for ordinary observation, with short frame bursts or local motion analysis for time-sensitive movement.

Do not claim that sparse image sampling precisely measures:

* Exact examination duration
* Fine motor movement
* Respiratory rate
* Other continuous temporal signals

## Video and Input Processing

Support:

* Uploaded MP4, MOV, or WebM files
* Bundled sample videos
* Individual debugging images
* Optional webcam input when practical
* User text input
* Optional speech-to-text input

Use OpenCV or equivalent local processing to:

* Read video metadata
* Sample frames at configurable intervals
* Preserve aspect ratio
* Resize images before API submission
* Encode images using a supported format
* Attach timestamps and frame numbers
* Reject corrupt inputs gracefully
* Detect obvious image-quality limitations

Quality checks should include:

* Low brightness
* Severe blur
* Missing frames
* Unsupported orientation
* Excessive duration
* Excessive file size
* Subject outside the frame
* Required body parts not visible

Surface input limitations to both the agents and the user.

## Claude API Direction

Use the official Anthropic Python SDK and Claude Messages API.

Create a shared client wrapper that supports:

* Multimodal text and image messages
* System prompts
* Structured outputs or forced tool calls
* Streaming user-facing text
* Configurable models
* Configurable token limits
* Timeouts
* Limited retries with exponential backoff
* Error classification
* Request IDs
* Latency tracking
* Token-usage logging
* Safe typed fallbacks
* Stop-reason inspection

Load credentials and model identifiers through environment variables.

Do not hard-code model identifiers throughout the repository.

Suggested configuration variables include:

* ANTHROPIC_API_KEY
* MEDBRIDGE_EXTRACTOR_MODEL
* MEDBRIDGE_PLANNER_MODEL
* MEDBRIDGE_TALKER_MODEL
* MEDBRIDGE_VERIFIER_MODEL

Use a faster model configuration for the Talker when possible and a more capable reasoning configuration for the Planner and Verifier when latency permits.

For the hackathon, architectural separation is more important than using different foundation-model families.

## Structured Outputs

Use Pydantic models for every module boundary.

At minimum, define typed models for:

* Frame samples
* Transcript segments
* Evidence observations
* Clinical goals
* Clinical plans
* Encounter state
* Talker output
* Safety review
* Workflow definitions
* Workflow steps
* Audit events
* Evaluation scenarios
* Evaluation results

Prefer native structured outputs when supported.

Otherwise, use forced tool calls whose JSON Schema mirrors the corresponding Pydantic model.

Never extract JSON from arbitrary prose using regular expressions.

On schema-validation failure:

1. Record the raw response.
2. Retry once with the validation error and schema.
3. If validation still fails, return a safe typed fallback.
4. Do not display malformed model content to the user.

Use enums for fixed decision and status fields.

## Workflow Engine

Represent clinical workflows as YAML or JSON configuration rather than embedding all workflow logic in prompts.

A workflow should define:

* Workflow ID
* Display name
* Intended user
* Entry conditions
* Required inputs
* Initial goals
* Allowed goal types
* Examination procedures
* Expected evidence
* Red flags
* Escalation rules
* Stop conditions
* Prohibited actions
* Completion criteria
* Disclaimer

The workflow engine should combine:

* Deterministic safety constraints
* Configured examination procedures
* Dynamically managed Planner goals

Do not make the workflow a completely rigid sequence, but do not allow the model to invent unrestricted clinical procedures.

## Tool Design

Claude may request narrow application-side tools that Python executes.

Acceptable tools include:

* Update encounter state
* Add or reprioritize a clinical goal
* Mark a goal complete or uncertain
* Request an additional camera view
* Request user confirmation
* Raise an emergency alert
* Record an observation
* Retrieve a configured workflow instruction
* Resume an incomplete examination
* Create a clinician-review summary

Each tool must have:

* A narrow purpose
* Strict JSON Schema
* Input validation
* Explicit error handling
* Auditable logs

Do not expose:

* Arbitrary shell access
* Arbitrary filesystem access
* Dynamic code execution
* Unrestricted web browsing
* Autonomous communications
* Medical-device controls
* Medication-ordering systems

## User Interface

Build a Streamlit interface optimized for a clear live demonstration.

The interface should show:

* Current or uploaded video
* Current sampled frame
* Latest transcript
* Active workflow
* Current clinical goal
* Encounter state
* Red flags
* Evidence limitations
* Final approved instruction
* Talker proposal
* Safety Verifier decision
* Planner goals
* Workflow progress
* Latency and model status

Include a technical inspection area showing:

* Evidence Extractor JSON
* Clinical Planner JSON
* Talker JSON
* Safety Verifier JSON
* Original and corrected messages
* Supporting frame IDs
* Prompt versions
* API request IDs
* Token usage
* Latency
* Validation errors
* Event logs

Make the architecture visually obvious:

MULTIMODAL EVIDENCE
↓
ENCOUNTER STATE
↓
CLINICAL PLANNER
↓
TALKER PROPOSAL
↓
SAFETY VERIFIER
↓
APPROVED, REVISED, BLOCKED, OR EMERGENCY RESPONSE

## Demo Modes

Implement two modes.

### Demo Mode

Demo Mode should:

* Use a bundled synthetic scenario
* Use pre-extracted frames when helpful
* Advance turn by turn
* Produce reliable judge-friendly playback
* Support explicitly labeled cached outputs
* Demonstrate at least one Planner course correction
* Demonstrate at least one Verifier revision
* Demonstrate at least one emergency override

Prioritize Demo Mode before Live Mode.

### Live Mode

Live Mode may:

* Process uploaded video
* Process webcam snapshots
* Make live API calls
* Display current latency
* Handle network or API failures without crashing
* Fall back safely when a model output fails validation

Do not make the success of the presentation depend entirely on network availability or live camera behavior.

## Auditability

Write one structured event for each processing stage.

Each event should contain:

* Session ID
* Turn ID
* Timestamp
* Workflow ID
* Active goal ID
* Agent or module name
* Prompt version
* Model
* Request ID
* Input frame IDs
* Input transcript IDs
* Input state
* Raw output
* Parsed output
* Validation status
* Latency
* Token usage
* Errors
* Original Talker message
* Final displayed message

Do not log API keys or unnecessary personal information.

Support session export containing:

* session.json
* events.jsonl
* validation_summary.md
* evaluation_summary.md

## Evaluation

Create a replayable offline evaluation harness using synthetic scenarios.

Each scenario should define:

* Scenario ID
* Workflow
* Ordered frame paths
* Frame timestamps
* User transcript by turn
* Expected observations
* Expected critical questions
* Expected examination steps
* Expected red flags
* Prohibited actions
* Expected escalation
* Known evidence limitations
* Gold outcome

Evaluate at least these system variants:

1. Talker only
2. Talker plus Safety Verifier
3. Talker plus Clinical Planner
4. Full system with Planner and Verifier

Measure:

* Critical-step recall
* Red-flag recall
* Emergency-escalation recall
* False-escalation rate
* Unsupported-claim rate
* Omission errors
* Commission errors
* Workflow-order accuracy
* Goal-persistence rate
* Incomplete-examination recovery
* Contextual-completion rate
* Planner intervention rate
* Verifier intervention rate
* Verifier correction success
* Verifier false-block rate
* Time to first critical instruction
* Evidence-grounding accuracy
* Observer latency
* Planner latency
* Talker latency
* Verifier latency
* End-to-end latency
* Estimated API usage

Use deterministic scoring wherever gold labels exist.

Use a separate blinded evaluator only for subjective qualities such as empathy, clarity, naturalness, and communication quality.

Do not expose internal prompts or hidden rationales to the subjective evaluator.

## Repository Structure

Use a modular repository similar to:

medbridge/
app.py
requirements.txt
.env.example
README.md

```
config/
    settings.py

agents/
    evidence_extractor.py
    clinical_planner.py
    talker.py
    safety_verifier.py
    evaluator.py

api/
    claude_client.py
    retry.py

models/
    media.py
    evidence.py
    clinical_goals.py
    encounter_state.py
    workflows.py
    agent_outputs.py
    events.py
    evaluation.py

workflows/
    nihss_screen.yaml
    loader.py

prompts/
    evidence_extractor_system.md
    clinical_planner_system.md
    talker_system.md
    safety_verifier_system.md
    evaluator_system.md

services/
    orchestration.py
    state_tracker.py
    goal_manager.py
    response_router.py
    audit_logger.py

tools/
    clinical_tools.py
    registry.py

video/
    processor.py
    quality.py
    frame_store.py

audio/
    transcription.py

ui/
    components.py
    session_state.py

research_and_eval/
    dataset.py
    runner.py
    metrics.py
    report.py
    scenarios/

sample_data/
    videos/
    frames/
    transcripts/

tests/
    test_models.py
    test_state_tracker.py
    test_goal_manager.py
    test_response_router.py
    test_video_processor.py
    test_safety_verifier.py
```

## Implementation Order

### Phase 1: Vertical Slice

Implement:

* Configuration
* Pydantic schemas
* One neurological-screening workflow
* Uploaded-video processing
* Evidence extraction
* Encounter state
* Clinical Planner
* Talker
* Safety Verifier
* Response router
* Basic Streamlit interface

Do not begin optional integrations until this full loop works.

### Phase 2: Demo Reliability

Add:

* Bundled synthetic scenario
* Pre-extracted frames
* Step-by-step playback
* Structured logs
* API failure handling
* Safe typed fallbacks
* Cached-demo option
* Visible Planner course correction
* Visible Verifier revision
* Emergency override

### Phase 3: Evaluation

Add:

* Five to ten synthetic scenarios
* Baseline and ablation comparisons
* Deterministic metrics
* Latency reporting
* Token-use reporting
* Markdown evaluation report

### Phase 4: Optional Extensions

Only after the vertical slice works, consider:

* Additional clinical exam-documentation workflows (rounds, skin/wound findings)
* Live glasses / webcam input
* Speech-to-text
* Text-to-speech
* Additional clinical workflows
* More advanced temporal analysis
* Retrieval from trusted medical references
* Clinician-facing encounter notes

## Definition of Done

The hackathon prototype is complete when:

* A user can select a workflow and upload or choose a video.
* MedBridge extracts and displays timestamped evidence.
* The Evidence Extractor produces validated source-grounded observations.
* The encounter state persists correctly across turns.
* The Clinical Planner maintains unresolved goals and selects the next goal.
* The Talker produces one concise instruction or question.
* The Safety Verifier approves, revises, blocks, or overrides the proposal.
* The application controls which message reaches the user.
* Supporting frame IDs and evidence limitations are visible.
* At least one incomplete examination is resumed correctly.
* At least one unsafe or unsupported Talker message is visibly corrected.
* At least one urgent scenario triggers an emergency override.
* All module outputs validate against Pydantic schemas.
* A bundled scenario can run without live-camera dependence.
* Evaluation results can be generated from the command line.
* The README contains exact setup and execution commands.
* The interface clearly labels the project as experimental and not a replacement for emergency services or professional medical care.

## Working Style

When implementing the project:

* Prefer the smallest reliable vertical slice.
* Produce complete runnable files rather than disconnected fragments.
* Preserve modular boundaries.
* Keep prompts versioned and separate from code.
* Validate all model outputs.
* Use deterministic code for safety-critical state transitions.
* Make uncertainty visible.
* Log all important decisions.
* Run available tests after each implementation phase.
* Report exactly what passed, failed, or remains untested.
* Never claim API success, medical validation, test completion, or production readiness without direct evidence.
* Do not add optional features before the core demonstration works.
* When a design choice threatens demo reliability, prefer the simpler inspectable implementation.
* When medical safety and demo convenience conflict, medical safety takes priority.
* When clinical evidence is insufficient, request more evidence or escalate rather than guessing.
* When an emergency is plausible, do not delay escalation merely to complete the normal workflow.
