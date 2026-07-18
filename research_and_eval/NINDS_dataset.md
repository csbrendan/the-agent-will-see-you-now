# NINDS NIHSS — Primary Dataset & Findings

> **Safety-verified acute stroke screening from an audiovisual neuro exam — for clinical use.** A
> **clinician** (nurse, resident, or attending) performs a focused neurological exam normally, and
> MedBridge captures the resulting short **video clip — moving images *and* audio —**. Its
> **multimodal Evidence Extractor** fuses **Claude vision over frame *sequences*** (facial asymmetry,
> arm *drift over time*, gaze tracking) with **Whisper over the audio** (speech clarity, naming,
> commands) into source-attributed evidence; the **Clinical Planner** works the NIH Stroke Scale one
> item at a time; the **Safety Verifier** refuses to call an exam "normal" without the evidence to
> support it and fires an **emergency escalation** on stroke red flags. Time-critical ✓ ("time is
> brain"), clinician-facing ✓ (the physician stays the accountable decision-maker),
> *safer* (a missed or over-claimed stroke finding is the liability the Verifier prevents) ✓ — and
> the **NINDS NIHSS videos** (public-domain, clinician-produced, auto-segmented into **218
> item-typed clips** — every clip labeled with *which* NIHSS item it shows; numeric *scores* are
> narrated only for the 2 demonstration patients, see §3) are the real product substrate +
> validation, **not** a side eval.
>
> **This is video understanding, not image classification.** The exam is inherently **audiovisual
> and temporal**: arm drift is a *trajectory over ~10s*, dysarthria is *speech*, gaze is *motion*.
> MedBridge reasons across **ordered frame sequences + audio** (plus spatio-temporal motion
> features where an item needs them), through an **independent multi-agent safety architecture** —
> categorically distinct from a single-prompt image analyzer or a dashboard.

This is the **only** dataset MedBridge uses — the exact clinical workflow the product targets.

---

## 1. What it is

The official **NINDS NIH Stroke Scale (NIHSS) training & certification videos** — studio-produced
footage of physicians performing the NIHSS on real patients, released by the US National Institute
of Neurological Disorders and Stroke and hosted free on the Internet Archive.

- **License: CC0 1.0 Public Domain** (US federal work) — no consent/PHI/licensing friction. The
  best possible rights posture, with no attribution or commercial constraints.
- **Access: direct MP4 download, no gating** — `https://archive.org/download/<id>/<id>_512kb.mp4`.
- **Why it fits MedBridge exactly:** it *is* the neuro exam our primary workflow scopes — **facial
  symmetry, arm/leg drift, gaze, visual fields, speech/language, dysarthria, commands, alertness,
  extinction** — not a single sign, and every patient carries a known NIHSS structure.

## 2. Dataset structure (25 Internet Archive items)

| Group | Identifiers | Contents |
|---|---|---|
| **Training** | `gov.hhs.ninds.stroke.1.1 – 1.8` | Instructional parts (intro, instruction, tips, significance, credits) — **1.3 & 1.4 are full exams of Demo Patients A & B** |
| **Certification** | `gov.hhs.ninds.stroke.2.1 – 2.17` | **17 certification patient exams**: Group A = 2.1–2.6, Group B = 2.7–2.12, Group C = 2.13–2.17 |

**Patient exams available for eval: 19** (17 certification + 2 demo). Each is a full multi-item
NIHSS exam, ~5–11 minutes, **320×240** resolution, with audio.

## 3. Our auto-segmentation (built + run)

Full NIHSS exams are long, multi-item recordings with **on-screen title cards** demarcating each
item ("CERTIFICATION 7 LIMB ATAXIA"). We exploit those cards to auto-segment.

**Method** (`sample_data/ninds/ninds_segmenter.py`):
1. Sample a frame every ~1.2s; **OCR** it with **Apple Vision** (`ocrmac`) — ~31 ms/frame.
2. Detect title-card frames whose text matches a canonical NIHSS item (match on item **names** —
   number OCR is noisy: 1B→"IBI", 2→"121").
3. Each item = [its title card → the next item's card]; sample exam frames from the segment
   (skipping the card).
4. Write per-item frames + a gold manifest (item id/name, start/end s, frame paths, patient +
   examiner header).

**Result (full run, all 19 patients):**

- **218 item-segments · 654 frames · ~3 min total runtime** (OCR ~7–12s/video; decode is free at
  ~11k frames/s).
- Output: `sample_data/ninds/segmented/<id>/manifest.json` per video + a combined
  **`ALL_manifest.json`** gold index. (Data is gitignored; regenerate with the segmenter.)

**NIHSS item coverage across the 19 patients:**

| Item | Name | Coverage | Item | Name | Coverage |
|---|---|:--:|---|---|:--:|
| 1a | LOC | 19/19 | 6 | Motor Leg | 19/19 |
| 1b | LOC Questions | 18/19 | 7 | Limb Ataxia | 17/19 |
| 1c | LOC Commands | 18/19 | 8 | Sensory | **8/19** |
| 2 | Best Gaze | 19/19 | 9 | Best Language | 19/19 |
| 3 | Visual Fields | 19/19 | 10 | Dysarthria | **5/19** |
| 4 | Facial Palsy | 19/19 | 11 | Extinction | 19/19 |
| 5 | Motor Arm | 19/19 | | | |

**FAST-critical items (Facial, Motor Arm, Motor Leg, LOC, Gaze, Language, Extinction) are 19/19.**
Sensory (8) and Dysarthria (10) are low — a mix of real per-patient variation (some certs skip
them) and short segments whose title card fell between OCR samples. Refinement: drop OCR interval
to ~0.8s and add fuzzy matching near the language segment.

**Gold manifest item shape:**
```json
{ "item_id": "5", "item_name": "Motor Arm",
  "start_s": 94.9, "end_s": 116.5, "frame_paths": ["gov.../5_0.jpg", "..."] }
```

### 3.1 Outcome labels (scores) — what is and isn't labeled (READ before eval design)

The manifest item shape above has **no `score` field**. The NIHSS *outcome* per item is never a
structured field — it only ever appears as the examiner **speaking it inside the audio/transcript**,
and only for some patients. There are **two data regimes**:

| Regime | Videos | Items | Outcome in our data? |
|---|---|:--:|---|
| **Demonstration** (Patient A, Patient B) | `1.3`, `1.4` | **~24** | ✅ examiner narrates the score inline — *"Four is scored as a two, because he shows a clear-cut upper-motor-neuron facial weakness"*, *"Nine is scored as a two"*. Score **+ rationale**, extractable from the transcript. |
| **Certification** (Group A/B/C) | `2.1`–`2.17` | **~194** | ❌ the exam is performed but **the score is never spoken** — by design, the trainee scores themselves against the **external NINDS answer key**, which is **not** in our data. Outcome-unlabeled today. |

So *"218 gold-labeled clips"* precisely means: **218 clips labeled with the item _type_** (reliable,
from OCR) — but only **~24 clips carry an _outcome_ label** (the two demo patients), and those must
be parsed out of narration.

**Scored inventory we can extract today** (parsed from the two demo-patient transcripts; `–` = the
item's score phrasing didn't parse cleanly and needs a manual read):

| Item | 4 Facial | 5 Arm | 6 Leg | 9 Lang | 10 Dysar | 11 Ext | 1a LOC | 1b Q | 1c Cmd | 2 Gaze | 3 VF | 7 Ataxia | 8 Sens |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **A** (`1.3`) | – | 0 | 1 | 0 | 1 | 1 | 0 | — | — | – | 0 | 0 | 0 |
| **B** (`1.4`) | 2 | 2 | 3 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

Patient A is **mostly normal**; Patient B is **mostly abnormal** — so together they give
**both positive (abnormal) and negative (normal) examples**, but coverage is **thin**: 1–2 labeled
examples per item, and only a few items (Motor Arm 0/2, Language 0/2, Extinction 1/0) have a clean
normal-*and*-abnormal pair.

> ⚠️ **Leakage risk.** For the demo patients the transcript *literally contains the answer*
> ("scored as a two"). If the raw transcript is fed to the model, the eval leaks the gold. The
> examiner's scoring commentary **must be split off** (held out as gold) from the exam-performance
> portion the model is allowed to see. See §8 for how this shapes the eval.

**To unlock the 194 certification items** for outcome eval you need the **official NINDS
certification answer key** (check whether it's published) or an expert/hand-labeling pass on a chosen
subset. Until then, cert clips are gold for *item-type / observation / abstention* evals, not scoring.

## 4. Frames required — the temporal analysis (critical design finding)

"3 frames per item" was enough to **validate segmentation**. It is **not** the right budget for the
**agent**, because NIHSS is **audiovisual and temporal**, not single-image. By item:

| Item(s) | What's assessed | Modality | Frames / input needed |
|---|---|---|---|
| 4 Facial Palsy | asymmetry **while** smiling / showing teeth | visual, semi-temporal | baseline + active → **3–5 key frames** |
| **5 Motor Arm (drift)** | arm held 10s, **drifts down over time** | visual, **fully temporal** | trajectory → **8–15 frames** or motion features |
| 6 Motor Leg | leg drift over time | visual, temporal | **8–15** or features |
| 7 Limb Ataxia | coordination **during** finger-nose | visual, temporal | dense sequence |
| 2 Best Gaze | eyes **tracking / deviating** | visual, temporal | sequence |
| 3 Visual Fields | response to finger movement | visual, temporal | sequence |
| 1c LOC Commands | did they perform the command | visual, temporal | short sequence |
| 1a LOC | alertness / responsiveness | visual, mild-temporal | 3–5 frames |
| 1b LOC Questions | correct verbal answers | **audio/verbal** | **Whisper** (frames don't help) |
| 9 Best Language | naming / reading | **audio/verbal** | **Whisper** |
| 10 Dysarthria | slurred speech | **audio** | **Whisper** |

**Two consequences that shape the architecture:**
1. **~3 items are speech, not vision** (1b, 9, 10) → require **audio → Whisper transcript**. We keep
   these (audiovisual is a differentiator), sliced per-item using the same segmentation timestamps.
2. **Most visual items are motion, not snapshots.** Arm drift is the canonical case — the *entire
   signal is the downward trajectory over ~10s*, which 3 spread-out stills cannot capture.

**How to handle temporal (no native video input to Claude — frames only):**
- **(A) Dense frame sequence** — 8–15 ordered frames w/ timestamps across the maneuver (~1–2 fps);
  Claude infers motion. Simple, ~550 tokens/frame. Good for gross motion; may miss subtle motion.
- **(B) Spatio-temporal motion features** — local **pose/keypoint** tracking over the whole segment
  → compute the metric (wrist-y slope = drift, tremor frequency) → feed a compact summary + 2–3 key
  frames. More robust/quantitative for exactly the motor signs NIHSS grades; cheaper. Add **only for
  the item(s) that need it** (start with arm drift) — YAGNI until proven necessary.

**Frame budget by category (item-adaptive sampling, replaces the flat "3"):**
- Static-ish (LOC, resting asymmetry): **2–4 frames**
- Temporal/motion (arm drift, gaze, ataxia, facial-during-smile): **8–15 frames** or features (B)
- Speech (1b/9/10): **audio → Whisper, 0 frames**

## 5. Multimodal Evidence Extractor (design implication)

The Extractor is a **fusion module**, not a single vision call:

```
frames (sequence)  → Claude vision      → visual observations (asymmetry, drift, gaze)
audio (per item)   → Whisper            → transcript → Claude assessment (naming, dysarthria)
motion (if needed) → pose/CNN features  → quantitative drift/tremor summary
        └────────────── all become source-attributed evidence in Encounter State ──────────────┘
                          → Clinical Planner → Talker → Safety Verifier → escalate/route
```

Claude stays the **reasoning + safety-verification core**; Whisper (MIT, runs on the MacBook via
Apple Silicon / `whisper.cpp` — **no GPU needed**) and any pose/CNN are **specialized extractors**.
No Claude-only requirement exists; all chosen models are rights-clean.

## 6. Caveats

- **Low resolution (320×240)** — fine for gross observations (posture, gross movement, examiner
  interaction, resting asymmetry); limited for *fine* facial detail. Higher-resolution glasses
  capture at deployment would improve fine-grained perception.
- **Small patient-n (19)** at the patient level; **218 item-typed observations** → adequate for
  *item-type / observation / abstention* eval, but **outcome (score) labels exist for only ~24
  items** (2 demo patients — see §3.1), so scoring-accuracy numbers will be illustrative, not
  statistically powered, until the answer key or hand-labels are added.
- **Sensory/Dysarthria under-segmented** (8/19, 5/19) — refine OCR density if those items matter.
- **Gold = item labels for all 218; outcome scores for ~24** (see §3.1). Not the numeric answer key
  for the 194 certification items.

## 7. Regenerate / runtime

```bash
# one-time, ~3 min, all local, no API:
./.venv/bin/python sample_data/ninds/ninds_segmenter.py ALL
# -> sample_data/ninds/segmented/<id>/manifest.json + ALL_manifest.json + frames
```
Decode is ~free (11k frames/s); OCR (Apple Vision) is the only cost (~7–12s/video). Per-item **audio**
extraction + Whisper is the planned next addition (audio path validated separately).

## 8. How we design & validate the multi-agent workflow

The labeling reality in §3.1 (item type for all 218; outcome scores for only ~24) means **one eval
track is not enough**. We validate on **three tracks**, from most data to least, so the headline
result never over-claims what the gold supports.

### Track 1 — Perception & grounding (all 218 clips · item-type gold)

The strongest data we have. For each clip we know the item type and the exam region/modality it
should attend to. Score the **Evidence Extractor** (and the fused Listener/motion features):
- **Right-thing rate** — did it produce evidence for the correct item/modality (e.g. arm-drift item →
  arm-trajectory evidence, speech item → transcript-based evidence)?
- **Source-attribution correctness** — observations cite the right frame IDs / audio segment.
- **Abstention / uncertainty calibration** — on deliberately degraded inputs (see Track 3) does it
  mark evidence *uncertain/unknown* rather than guessing? This is the safety primitive.

No numeric answer key needed — this measures whether the system **observes the right thing**.

### Track 2 — Outcome / scoring accuracy (~24 demo-patient clips · narrated gold)

The only place we can compare a **predicted NIHSS score to a gold score** today.
- **Leakage-safe input (mandatory):** split each demo transcript into (a) the *exam-performance*
  portion — instructions, the patient's responses, counting — which the model may see, and (b) the
  *examiner's scoring commentary* ("…is scored as a two because…") which is **held out as gold +
  rationale**. Never feed (b) to the pipeline.
- **Metrics:** exact-match score, ±1 tolerance, and normal-vs-abnormal (0 vs >0) binary — the last is
  the most robust given thin per-item n and the clinically important call.
- **Report honestly:** n≈24, illustrative not powered. Use it for qualitative "the system scored this
  arm as a 2, matching the examiner" moments, not a headline accuracy %.

### Track 3 — Safety behavior (constructed cases · the winning moment)

Where the multi-agent architecture earns its keep. Build a small set of **adversarial/degraded
scenarios** from real clips (deterministic, replayable):
- **Occlusion / too-brief / off-frame** — arm leaves frame, maneuver <10s, poor lighting → the
  system must **decline to call it "normal"** and request re-capture or escalate.
- **Contradiction** — frames suggest asymmetry but transcript says "looks fine" → surface the
  conflict, don't silently resolve it.
- **Red-flag** — force a plausible stroke red flag → **emergency escalation** fires immediately.
- **Hallucination trap** — a clip where no reliable conclusion is possible → no invented finding.
Metrics: **unsupported-"normal" block rate, false-escalation rate, red-flag recall, hallucination
rate.**

### The ablation (runs across all three tracks)

`ALL_manifest.json` is the gold index. For each patient × item, sample frames (item-adaptive, §4)
and/or per-item audio, then run four variants and diff them:

| Variant | Question it answers |
|---|---|
| Extractor only | raw perception quality |
| + Safety Verifier | does the independent check catch unsupported claims? |
| + Clinical Planner | does goal management improve item ordering / coverage? |
| **Full** (Planner + Verifier) | the shipped system |

Report per variant: perception metrics (T1), scoring metrics (T2, demo subset), safety metrics (T3),
plus **latency and token cost per agent**. The decisive comparison is **Extractor-only vs. Full on
Track 3** — the Verifier converting a confident-but-unsupported "normal" into a *"can't confirm —
escalating to a human"* is the result we lead with, and it maps onto Impact + Creativity + Technical.

### Build order for the eval harness

1. Transcript **score-parser** → structured `gold_score` (+ held-out rationale) for the 24 demo items
   — this is the one piece of gold that doesn't exist yet.
2. Track 1 metrics on all 218 (no scores needed) — get a number early.
3. Track 3 constructed cases (hand-authored from ~5–10 clips) — the demo.
4. Track 2 leakage-safe scoring on the demo subset — the "it actually matches the examiner" proof.
5. Optional stretch: obtain/hand-label the certification answer key to widen Track 2 to 194 items.
