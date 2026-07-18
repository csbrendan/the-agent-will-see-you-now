# AGENTS.md

The agent-pipeline contract for **MedBridge**. Canonical source of truth is
**[ProjectPlan.md](ProjectPlan.md)**; this file is the focused reference for the five
modules, their I/O, and the routing rules. Operational/build guidance for AI coding
tools lives in **[CLAUDE.md](CLAUDE.md)**.

MedBridge separates fast interaction from slower clinical planning and adds an
independent safety-verification layer. Perception, state, planning, communication,
verification, routing, and logging are **explicit modules with typed (Pydantic)
interfaces** — never one large prompt or one unconstrained agent.

> **Framing & positioning.** MedBridge is an **audiovisual, temporal** co-clinician — it reasons
> over **moving-image sequences + audio** (not stills), for the primary workflow of **NIHSS acute
> stroke screening** on the public-domain NINDS videos (see
> [research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md); ProGait gait is the
> secondary scale-eval). This is deliberately **not** a single-prompt image classifier, RAG app, or
> dashboard (hackathon anti-projects — [HACKATHON.md](HACKATHON.md)). See [concept.md](concept.md).

## Pipeline

```
Audiovisual clip (ordered frame sequences + audio)
        │
        ▼
1. Multimodal Evidence Extractor   → FUSION: Claude-vision (frame sequences) + Whisper (audio)
                                     + optional pose/CNN motion → source-attributed observations
        │
        ▼
2. Encounter State                 → validated, structured, lives OUTSIDE the models
        │
        ▼
3. Clinical Planner                → selects the next clinical goal (runs BEFORE Talker)
        │
        ▼
4. Talker                          → one concise user-facing instruction / question
        │
        ▼
5. Safety Verifier                 → independent check of the EXACT proposed message
        │
        ▼
   Response Router (app code)       → approve · revise · block · emergency_override · insufficient_evidence
        │
        ▼
   UI  +  structured audit / evaluation logs
```

The **application**, not any model, decides what reaches the user.

---

## 1. Multimodal Evidence Extractor  (fusion — audiovisual + temporal)

A **fusion module**, not a single vision call. Converts an audiovisual exam segment into
**conservative, source-attributed observations**, each referencing its supporting **frame IDs**
(and/or audio segment). Three input channels feed one unified evidence output:

```
VISUAL EXTRACTOR: frames (ordered SEQUENCE) → Claude Opus 4.8 vision → observations (asymmetry, drift, gaze)
LISTENER:         audio (per-item window)   → Whisper (MIT, local)   → transcript → assessment (naming, dysarthria)
(motion, if needed): pose/CNN features       → local                → quantitative drift/tremor summary
```

Named sub-agents: the **Visual Evidence Extractor** (Claude vision) and the **Listener** (Whisper)
run in parallel; their outputs merge into one source-attributed evidence set. Downstream models:
Clinical Planner + Safety Verifier = Claude Opus 4.8 (high effort); Talker = Claude Haiku 4.5.

**Temporal + item-adaptive** — the exam is motion + speech, not snapshots. Frame budget:
- **Static-ish** (LOC, resting asymmetry): 2–4 frames.
- **Temporal/motion** (arm drift, gaze, ataxia, facial-during-smile): **8–15 ordered frames**
  (with timestamps so the model can infer the trajectory) or pose/CNN motion features.
- **Speech** (LOC-Questions, Language, Dysarthria): **0 frames → Whisper transcript.**

Must distinguish: directly visible · directly audible · user-reported · model inference ·
unknown/unobservable · contradictory · poor-quality/incomplete evidence.

Must **not** diagnose, choose treatment, or instruct the user (evidence only). Must **never**
infer pulse, BP, SpO₂, internal injury, med dose, or a definitive diagnosis from ordinary video.
Blocked/blurred/off-camera/too-brief/poorly lit/temporally ambiguous evidence is marked
**uncertain or unknown**, never guessed. A single still **cannot** establish a temporal sign
(e.g. arm drift) — say so rather than guessing from one frame.

Models: `MEDBRIDGE_EXTRACTOR_MODEL` (Claude vision) + Whisper (audio) + optional pose/CNN. Claude
is the reasoning core; the others are specialized extractors. No Claude-only requirement; all
models must be rights-clean.

## 2. Encounter State

Explicit structured state maintained **outside** the language models. Includes: active
workflow, current concern, gathered/unresolved findings, user-reported symptoms,
visible/audible observations, active/completed/suspended goals, failed-or-uncertain
exam steps, detected red flags, outstanding questions, evidence-quality limitations,
emergency status, current user-facing instruction, encounter status, last-update time.

Models may **propose** state changes; **application code validates** all changes before
committing. No model may invent unsupported steps, findings, exam results, or completed
actions. **Issuing an instruction ≠ the action was completed.**

## 3. Clinical Planner

Persistent clinical reasoning and goal-management agent; runs **before** the Talker.
Maintains a compact encounter model, identifies unresolved/safety-critical info,
screens for workflow red flags, prioritizes the next goal, and decides whether to ask,
guide an exam, observe, clarify, summarize, or escalate. Retains incomplete goals
across interruptions and resumes unfinished exams. Requests better evidence when
needed; recommends escalation when uncertainty/urgency requires it; keeps the
interaction inside the selected workflow.

Manages **dynamic goals** (added · prioritized · retained · suspended · resumed ·
completed · abandoned-with-reason · superseded by emergency) — not a rigid checklist.
Produces **structured guidance for the Talker**, not the final patient-facing response.
Makes uncertainty explicit; never presents a differential as a diagnosis.

Model: `MEDBRIDGE_PLANNER_MODEL` (capable reasoning config when latency permits).

## 4. Talker

Fast, user-facing conversational agent. Receives the current plan, encounter state,
recent evidence, a short rolling conversation window, the latest transcript, known
evidence limitations, and prior verifier feedback when relevant. Converts the Planner's
selected goal into a concise, natural instruction/question.

Messages are short · direct · calm · easy to follow under stress · **one primary action
at a time** · jargon-free · explicit about uncertainty · explicit about emergency
escalation. Generally avoids multiple questions at once. Requests repositioning,
repetition, or verbal confirmation when evidence is insufficient — unless that would
delay a critical lifesaving action.

Must never claim: a step was completed just because it was requested · a visual finding
is confirmed without evidence · a serious condition is ruled out · a diagnosis · a
measured unobservable vital sign · that emergency/professional care is unnecessary
without adequate evidence.

Model: `MEDBRIDGE_TALKER_MODEL` (faster config when possible).

## 5. Safety Verifier

A **separate** model call with a separate prompt and structured output, running **after**
the Talker. Independently assesses the **exact** proposed response and is **not**
instructed to agree with the Talker.

Checks for: failure to recommend emergency help when required · delay of a time-critical
action · dangerous procedural ordering · unsupported visual/clinical claims ·
hallucinated step completion · missing critical questions/instructions · failure to
acknowledge poor evidence · contradiction with encounter state · unsupported
reassurance · diagnosis/treatment outside scope · medication/prescribing/dosing advice ·
instructions exceeding the workflow · overly long instructions during an emergency ·
failure to escalate uncertain/high-risk cases.

Model: `MEDBRIDGE_VERIFIER_MODEL` (capable reasoning config when latency permits).

### Verifier decisions → Response Router behavior

| Decision | What reaches the user |
|---|---|
| `approve` | Display the Talker response |
| `revise` | Display the **Verifier-corrected** response |
| `block` | Suppress the unsafe response |
| `emergency_override` | Immediately display the emergency instruction |
| `insufficient_evidence` | Request better evidence or professional evaluation |

Store the **original Talker output, Verifier decision, corrected output, and final
displayed response** for auditability.

---

## Evaluator (offline)

Not in the live turn loop. A blinded evaluator scores subjective qualities (empathy,
clarity, naturalness) only; deterministic scoring is used wherever gold labels exist.
Internal prompts/rationales are never exposed to the subjective evaluator.
Model: `MEDBRIDGE_EVALUATOR_MODEL`.

## Application-side tools (narrow, schema-validated)

Claude may request narrow tools that Python executes — e.g. update encounter state,
add/reprioritize a goal, mark a goal complete/uncertain, request another camera view,
request user confirmation, raise an emergency alert, record an observation, retrieve a
configured workflow instruction, resume an incomplete exam, create a clinician-review
summary. Each has a narrow purpose, strict JSON Schema, input validation, explicit
error handling, and auditable logs.

**Never expose:** arbitrary shell/filesystem access, dynamic code execution,
unrestricted web browsing, autonomous communications, medical-device controls, or
medication-ordering systems.

## Turn loop

1. Capture/extract a timestamped frame + transcript window.
2. Run the Evidence Extractor.
3. Validate and merge evidence into encounter state.
4. Run the Clinical Planner.
5. Validate the Clinical Plan.
6. Run the Talker.
7. Run the Safety Verifier.
8. Route the approved/corrected response (app code decides).
9. Update state and write structured logs.
10. Continue to the next turn.

Turn-based approximation of a continuous audiovisual co-clinician — not equivalent to a
native low-latency continuous system. ~1 sampled frame/second for ordinary observation,
with short frame bursts for time-sensitive movement.
