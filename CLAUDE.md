# CLAUDE.md

Operating guide for AI coding assistants (Claude Code) working in this repo.
The canonical product/architecture spec is **[ProjectPlan.md](ProjectPlan.md)** —
read it before making design decisions. This file is the short operational layer
on top of it. See also **[AGENTS.md](AGENTS.md)** for the agent-pipeline contract.

See **[concept.md](concept.md)** for the current hackathon framing and
**[HACKATHON.md](HACKATHON.md)** for the judging rubric + anti-project rules.

## What MedBridge is

An **audiovisual, physician-supervised AI co-clinician** for a hackathon: it observes a short
**video clip — moving-image sequences *and* audio —** of a focused neurological exam, maintains
structured encounter state, plans the NIH Stroke Scale one item at a time, speaks one concise
instruction, and **independently verifies** that instruction before it reaches the user.

**Primary workflow:** audiovisual **acute stroke / NIHSS screening** on the public-domain
**NINDS NIHSS videos** (auto-segmented into 218 gold-labeled item clips — see
[research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md)). ProGait gait is the
secondary scale-eval, used later if time permits.

> **Hackathon positioning — this is NOT (and must never be built/pitched as):** a single-prompt
> **image classifier**, a **basic RAG** app, a **Streamlit-app-as-the-feature**, or a
> **dashboard** — all named anti-projects (HACKATHON.md §2). It is distinguished by being
> **(1) audiovisual** (video + Whisper audio, not stills), **(2) spatio-temporal** (arm drift is a
> *trajectory over ~10s*; reason across ordered frame sequences, add motion features where needed),
> and **(3) agentic + safety-verified** (independent multi-agent pipeline, not one prompt).

It is an **experimental research prototype** — not a medical device, not clinically
validated, not a replacement for emergency services or licensed clinicians.

## Non-negotiable safety rules (never violate in code or output)

MedBridge must **not**: diagnose, rule out a serious condition, prescribe or dose
medication, change/stop medication, tell a user to ignore a clinician, replace
emergency services, or claim medical-device status / clinical validation / production
readiness. It must never conceal uncertainty or evidence limitations.

- Distinguish **observed vs. audible vs. user-reported vs. inferred vs. unknown**
  evidence. Unknown stays unknown — never guess.
- Never infer pulse, BP, SpO₂, compression depth, internal injury, med dose, or a
  definitive diagnosis from ordinary video.
- **An instruction being issued does NOT mean the action was completed.**
- Deterministic application code — not a model — validates every state change and
  decides what reaches the user.
- When evidence is insufficient, request more or escalate rather than guessing.
- When an emergency is plausible, escalate immediately; do not delay to finish the
  normal workflow. **When safety and demo convenience conflict, safety wins.**

## Architecture (five explicit modules, typed interfaces)

```
Audiovisual clip (frame sequences + audio)
  → Multimodal Evidence Extractor   (FUSION: Claude-vision on ordered frame sequences
                                      + Whisper on per-item audio + optional pose/CNN motion
                                      features → source-attributed observations, frame/segment IDs)
  → Encounter State                 (structured, outside the models)
  → Clinical Planner                (persistent NIHSS-item goals; picks next; runs BEFORE Talker)
  → Talker                          (one concise user-facing instruction/question)
  → Safety Verifier                 (independent check of the exact proposed message)
  → Response Router                 (approve / revise / block / emergency_override / insufficient_evidence)
  → UI + structured audit/eval logs
```

Do **not** implement this as one big prompt or one unconstrained agent. Keep
perception, state, planning, communication, verification, routing, and logging as
separate modules. Prompts live in `prompts/` (versioned, separate from code).

**Extractor is temporal + multimodal, not single-image.** Frame budget is **item-adaptive**:
2–4 frames (static items like LOC), 8–15 frames or pose/CNN motion features (temporal items like
arm drift / gaze / ataxia), 0 frames + **Whisper audio** (speech items: LOC-Questions, Language,
Dysarthria). Claude is the reasoning + safety core; Whisper/pose are specialized extractors feeding
it. There is **no Claude-only requirement** — all models must be rights-clean. See
[research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md) §4–5.

## Tech stack

Python · Anthropic Python SDK (Claude Messages API) · **OpenCV** (frame extraction) · **Whisper**
(audio → transcript; MIT, runs local on Apple Silicon — no GPU) · **ocrmac / Apple Vision** (title-card
OCR for NINDS segmentation) · Pillow · Pydantic · PyYAML · python-dotenv · optional pose (MediaPipe)
for motion features. UI kept thin (Streamlit is fine as scaffolding but **must not be "the feature"**
— the agents are). Every module boundary uses a Pydantic model.

## Environment / config

- Secrets and model IDs come from environment (`.env`, git-ignored). Never hard-code
  model identifiers throughout the repo; read them from config.
- Canonical variables (see `.env.example`):
  `ANTHROPIC_API_KEY`, `MEDBRIDGE_EXTRACTOR_MODEL`, `MEDBRIDGE_PLANNER_MODEL`,
  `MEDBRIDGE_TALKER_MODEL`, `MEDBRIDGE_VERIFIER_MODEL`, `MEDBRIDGE_EVALUATOR_MODEL`.
- A faster model config for the Talker; a more capable one for Planner/Verifier when
  latency permits. Architectural separation matters more than using different families.

## Dev commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt   # (requirements.txt TBD)
cp .env.example .env        # then fill ANTHROPIC_API_KEY

# Run the app
streamlit run app.py        # http://localhost:8501

# Tests
python -m unittest discover -s tests    # or: pytest -q

# Offline evaluation
python -m research_and_eval.runner
```

## Structured-output discipline

- Prefer native structured outputs; otherwise force tool calls whose JSON Schema
  mirrors the Pydantic model. **Never regex JSON out of prose.**
- On schema-validation failure: record raw response → retry once with the error +
  schema → if still invalid, return a **safe typed fallback**. Never show malformed
  model content to the user. Use enums for fixed decision/status fields.

## Implementation order (do not skip ahead)

1. **Vertical slice** — config, Pydantic schemas, one **neurological-screening**
   workflow, uploaded-video processing, Extractor, Encounter State, Planner, Talker,
   Verifier, Response Router, basic Streamlit UI. Finish this loop before anything else.
2. **Demo reliability** — bundled synthetic scenario, pre-extracted frames, step
   playback, structured logs, API-failure handling, cached-demo option, and a visible
   Planner course-correction, Verifier revision, and emergency override.
3. **Evaluation** — 5–10 synthetic scenarios, baseline/ablation comparisons,
   deterministic metrics, latency + token reporting, Markdown report.
4. **Optional extensions** — CPR, webcam, STT/TTS, more workflows. Only after 1–3.

First workflow is **audiovisual NIHSS stroke screening** on the NINDS gold clips (best showcase
for multimodal perception + persistent goals). Demo-focus items: **Facial Palsy (asymmetry)** +
**Motor Arm (drift — temporal sequence)** + one **speech item via Whisper**. Use item-adaptive
frame sampling, not a flat count. Implement one workflow deeply before adding another.

## Working style

- Smallest reliable vertical slice first; complete runnable files, not fragments.
- Preserve modular boundaries; keep prompts versioned and separate from code.
- Deterministic code for safety-critical state transitions; make uncertainty visible;
  log important decisions.
- Run available tests after each phase and **report exactly what passed, failed, or is
  untested.** Never claim API success, medical validation, test completion, or
  production readiness without direct evidence.
- Do not add optional features before the core demonstration works.

## Repo hygiene

- `.env` is git-ignored — never commit secrets. Don't log API keys or unnecessary PII.
- Demonstrations use synthetic, staged, consented, or non-patient data only.
- Commit/push only when the user asks.
