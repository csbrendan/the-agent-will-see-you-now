# MedBridge — Concept & Framing Summary

> **Safety-verified acute stroke screening from an audiovisual neuro exam.** A patient, bedside
> responder, or tele-neurology nurse captures a short **video clip — moving images *and* audio —**
> of a focused neurological exam. MedBridge's **multimodal Evidence Extractor** fuses **Claude
> vision over frame *sequences*** (facial asymmetry, arm *drift over time*, gaze tracking) with
> **Whisper over the audio** (speech clarity, naming, commands) into source-attributed evidence;
> the **Clinical Planner** works the NIH Stroke Scale one item at a time; the **Safety Verifier**
> refuses to call an exam "normal" without the evidence to support it and fires an **emergency
> escalation** on stroke red flags. Time-critical ✓ ("time is brain"), patient/responder-facing ✓,
> *safer* (a missed or over-claimed stroke finding is the liability the Verifier prevents) ✓ — and
> the **NINDS NIHSS videos** (public-domain, clinician-produced, auto-segmented into **218
> gold-labeled item clips**) are the real product substrate + validation, **not** a side eval.
>
> **This is video understanding, not image classification.** The exam is inherently **audiovisual
> and temporal**: arm drift is a *trajectory over ~10s*, dysarthria is *speech*, gaze is *motion*.
> MedBridge reasons across **ordered frame sequences + audio** (plus spatio-temporal motion features
> where an item needs them), through an **independent multi-agent safety architecture** —
> categorically distinct from a single-prompt image analyzer or a dashboard.

Judging guidance: [HACKATHON.md](HACKATHON.md) · Datasets:
[research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md) (primary),
[research_and_eval/ProGait_Dataset.md](research_and_eval/ProGait_Dataset.md) (secondary).

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

## Datasets — NINDS primary, ProGait secondary

| | **NINDS NIHSS** (primary) | **ProGait** (secondary, if time) |
|---|---|---|
| Role | **Clinical demo + on-workflow gold substrate** | Scale eval + "generalizes" story |
| Access | Direct MP4, **no gating** | Gated (accept-once), already downloaded |
| Rights | **CC0 public domain** (best) | CC-BY-NC-SA-4.0 |
| Fit | **Exact** — the NIHSS neuro exam | Gait/mobility |
| Gold | 218 auto-segmented item clips + labels | 150 gait deviation labels |
| Modality | **audiovisual** (frames + speech) | video (frames) |

We **demo on NINDS** (real exam, gold item labels, public domain, audiovisual) and, **later in the
day if time allows**, run the scale eval on **ProGait** to show the architecture generalizes across
movement-analysis tasks.

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
- Eval: item-level ablation on the NINDS gold manifest; ProGait scale-eval only if time remains.
