# MedBridge — Concept & Framing Summary

> **Safety-verified acute stroke screening from an audiovisual neuro exam — for clinical use.** A
> **clinician** (nurse, resident, or attending) wearing smart-glasses performs a focused
> neurological exam normally; MedBridge captures the resulting **video clip — moving images *and*
> audio —** and its **multimodal Evidence Extractor** fuses **Claude vision over frame *sequences***
> (facial asymmetry, arm *drift over time*, gaze tracking) with **Whisper over the audio** (speech
> clarity, naming, commands) into source-attributed evidence; the **Clinical Planner** works the NIH
> Stroke Scale one item at a time; the **Safety Verifier** refuses to call an exam "normal" without
> the evidence to support it and fires an **emergency escalation** on stroke red flags. Time-critical
> ✓ ("time is brain"), clinician-facing ✓ (the physician stays the accountable decision-maker),
> *safer* (a missed or over-claimed stroke finding is the liability the Verifier prevents) ✓ — and
> the **NINDS NIHSS videos** (public-domain, clinician-produced, auto-segmented into **218
> gold-labeled item clips**) are the real product substrate + validation, **not** a side eval.
>
> **This is video understanding, not image classification.** The exam is inherently **audiovisual
> and temporal**: arm drift is a *trajectory over ~10s*, dysarthria is *speech*, gaze is *motion*.
> MedBridge reasons across **ordered frame sequences + audio** (plus spatio-temporal motion features
> where an item needs them), through an **independent multi-agent safety architecture** —
> categorically distinct from a single-prompt image analyzer or a dashboard.

Judging guidance: [HACKATHON.md](HACKATHON.md) · Dataset:
[research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md) (the NINDS NIHSS videos).

## Concept — "document what you see, not what you say"

The core insight is simple: **the glasses see the exam, so nothing has to be spoken aloud to be
captured.** A physician, nurse, resident, or attending wears the glasses and performs the exam
normally. The agent observes, scores, and documents from what it sees — no dictation, no narration.

We're starting with the **NIH Stroke Scale (NIHSS)** as the wedge, then expanding to visual ambient
documentation of the whole physical exam.

> **Prototype vs. product vision — kept honest.** The 7-hour hackathon build runs the pipeline on
> **pre-recorded, gold-labeled NINDS NIHSS video** (uploaded clips), not live smart-glasses. The
> glasses + EHR write-back are the **productization path / North Star** the architecture is designed
> for; the demo proves the hard part — *scoring a structured neuro exam from video, safety-verified* —
> on real footage. We never claim glasses hardware or clinical validation we don't have.

### The stroke use case (the beachhead)

Whoever reaches the patient first — nurse, resident, whoever — wears the glasses and performs the
NIHSS. The agent scores it immediately, so a preliminary, standardized score is ready before the
stroke team even arrives. On a clock where minutes are brain, that time matters.

The key unlock: when a code stroke is called, the stroke neurologist is often off-site. Instead of
relying on a secondhand verbal description over the phone, they can remotely **"pass" the exam** —
verifying the agent's scored results against captured video of what actually happened. That's a
reliability upgrade over the status quo, and pulling the score right away standardizes something that
is normally rater-dependent.

### The platform play (the expansion)

The main weakness of audio-only ambient scribes is that doctors have to narrate everything out loud —
and they don't naturally do that during a physical exam. Visual capture removes that requirement. The
physician just examines the patient, and the findings land on the chart.

This generalizes well beyond stroke: rounds, skin lesions, any visible physical finding —
auto-documented without dictation. NIHSS is the entry point because it's structured, scored, and has
ground-truth training data. The thesis for everything after is: **document what you see, not what you
say.**

### Why this fits the evaluation framework

The judges evaluate high-impact agentic-AI ideas on **VALUE · SUITABILITY · FEASIBILITY**
(see [HACKATHON.md](HACKATHON.md) §5b). MedBridge maps cleanly:

**VALUE** — *speed & desire for adoption*
- **Repeatable:** the NIHSS is a fixed, standardized exam run over and over on every stroke code —
  ideal for automation.
- **ROI:** attacks door-to-needle time (minutes = brain tissue) and eliminates manual documentation
  burden — both expensive in time and outcomes.
- **Logic-based:** NIHSS is a rule-based scoring rubric, not an empathetic judgment call —
  well-suited to an agent.

**SUITABILITY** — *long-term moats & unlocks*
- **Data Structure:** unlocks unstructured visual exam data that today never gets captured beyond a
  number on a chart.
- **Data Availability:** unifies exam video, agent scoring, and chart documentation into one record
  across the care team.
- **Data Durability:** proprietary paired exam-video + ground-truth-score data accrues at scale as a
  defensible moat.

**FEASIBILITY** — *ability for the solution to work*
- **Technology:** scoring a structured neuro exam from video is within reach of today's models, and
  public NINDS NIHSS training footage provides gold-labeled ground truth.
- **Trust and safety:** the physician remains the accountable decision-maker (assistive, not
  autonomous); remote neurologist validation is built into the workflow. Consent/PHI handling is a
  first-class requirement.
- **Integration:** requires forward-deployed engineering for glasses hardware and EHR write-back —
  the deployment surface that makes it sticky.

## Why this is not a "mere image classifier" (the anti-project line)

The hackathon explicitly bars basic **image analyzers**, **Streamlit apps as the feature**, and
**dashboards**. MedBridge is categorically different on three axes:

1. **Audiovisual (video, not images).** It ingests **moving-image sequences + audio** — Whisper
   handles the speech items (LOC-Questions, Language, Dysarthria) the same way vision handles the
   motor items. A frames-only image classifier *cannot even do* those items.
2. **Spatio-temporal.** The signal for motor items *is motion over time* — arm-drift trajectory,
   gaze tracking, ataxia. We reason across ordered frame sequences (and add pose/CNN motion features
   where an item needs them), not over one still.
3. **Agentic + safety-verified.** An independent multi-agent pipeline (Extractor → Planner → Talker
   → **Verifier**) that grounds every claim in evidence and escalates — not one prompt returning a
   label.

## Multi-agent safety architecture (constant) — agents + models

Not one prompt: a pipeline of specialized agents, each a **separate model call with its own prompt
and typed (Pydantic) I/O**.

| Agent | Role | Model |
|---|---|---|
| **Listener** | audio → transcript for speech items (questions, commands, naming, dysarthria) | **Whisper** (`faster-whisper base`, local, no GPU) |
| **Visual Evidence Extractor** | frame **sequences** → source-attributed visual observations (asymmetry, arm drift over time, gaze) | **Claude Opus 4.8** (vision) · optional pose/CNN motion |
| **Clinical Planner** | works the NIHSS one item at a time; tracks goals; picks next step | **Claude Opus 4.8** (high effort) |
| **Talker** | plan → one concise, calm instruction/question | **Claude Haiku 4.5** (fast) |
| **Safety Verifier** | independent check of the exact message; blocks unsupported "normal"; escalates | **Claude Opus 4.8** (high effort) |
| **Response Router** | deterministic app code decides what reaches the user | *(no model)* |
| **Evaluator** (offline) | scores runs against gold labels | Claude Opus 4.8 |

Flow: `Listener + Visual Extractor → Encounter State → Clinical Planner → Talker → Safety Verifier
→ Response Router → clinician-reviewable guidance + escalation`. Workflow-agnostic engine
(`video/`, `audio/`, `api/`, `models/`, `services/`, `research_and_eval/`); only `workflows/*.yaml`
+ `prompts/` + the eval dataset change per task.

## Dataset — NINDS NIHSS

| | **NINDS NIHSS** |
|---|---|
| Role | **Clinical demo + on-workflow gold substrate** |
| Access | Direct MP4, **no gating** (Internet Archive) |
| Rights | **CC0 public domain** (best possible posture) |
| Fit | **Exact** — the NIHSS neuro exam itself |
| Gold | 218 auto-segmented item clips + labels |
| Modality | **audiovisual** (frames + speech) |

We **demo on NINDS** — a real, clinician-produced neurological exam with gold item labels, public
domain, audiovisual. It is the exact clinical workflow the product targets, not a proxy.

## Multimodal Evidence Extractor (frame + audio + motion)

```
frames (sequence)  → Claude vision      → visual observations (asymmetry, drift, gaze)
audio (per item)   → Whisper (MIT,local)→ transcript → Claude assessment (naming, dysarthria)
motion (if needed) → pose/CNN features  → quantitative drift/tremor summary
        └────────── all become source-attributed evidence → Planner → Talker → Verifier ──────────┘
```
Claude is the reasoning + safety core; Whisper and any pose/CNN are specialized extractors (all
rights-clean; no Claude-only requirement). Frame budget is **item-adaptive**: 2–4 (static), 8–15 or
motion-features (temporal), 0 + audio (speech). See NINDS_dataset.md §4 for the full analysis.

## The demo's winning moment

The **Verifier catching an output that looks fine but isn't supported by the evidence** — a "normal
exam" claim on a clip where the arm was never fully visible, or an unsafe instruction — and
**escalating to a human** instead of asserting it. That single beat maps onto Creativity (25%) +
Technical (20%) + Impact (20%).

## Scope for the 7-hour build

- **Headline: stroke / NIHSS screening on NINDS**, audiovisual, safety-verified.
- Focus items for the demo: **Facial Palsy (asymmetry)** + **Motor Arm (drift, temporal)** +
  one **speech item via Whisper** (e.g. Language or Dysarthria) — showcases visual, temporal, and
  audio in one flow.
- Eval: item-level ablation on the NINDS gold manifest.
