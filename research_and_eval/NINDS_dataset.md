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
> gold-labeled item clips**) are the real product substrate + validation, **not** a side eval.
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

> **What the gold IS:** item **segmentation + which NIHSS item** each clip shows (+ patient/examiner
> metadata). It is **not** the numeric NIHSS *score* per item — those live in the NINDS
> certification answer key (separate). So this supports *"is the system observing the right thing /
> grounding on the right region?"* evals today; adding the answer key later upgrades it to scoring
> accuracy.

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
- **Small patient-n (19)** at the patient level; but **~180+ observations at the item level**
  (19 patients × ~11 items) → adequate for item-level eval.
- **Sensory/Dysarthria under-segmented** (8/19, 5/19) — refine OCR density if those items matter.
- **Gold = item labels, not scores** (see §3).

## 7. Regenerate / runtime

```bash
# one-time, ~3 min, all local, no API:
./.venv/bin/python sample_data/ninds/ninds_segmenter.py ALL
# -> sample_data/ninds/segmented/<id>/manifest.json + ALL_manifest.json + frames
```
Decode is ~free (11k frames/s); OCR (Apple Vision) is the only cost (~7–12s/video). Per-item **audio**
extraction + Whisper is the planned next addition (audio path validated separately).

## 8. Eval usage (feeds `research_and_eval`)

`ALL_manifest.json` is the gold index for the ablation: for each patient × item, sample frames
(item-adaptive) and/or per-item audio → run the pipeline variants (Extractor-only → +Verifier →
+Planner → full) → score deviation/observation recall, **unsupported-claim rate**, and the Verifier
catch/escalation behavior against the item labels. Demo the **Verifier blocking an unsupported
"normal" call + escalating** — the winning moment.
