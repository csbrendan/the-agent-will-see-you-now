# Potential Datasets for MedBridge

> **Decision (current):** the **primary dataset is NINDS NIHSS** (public-domain audiovisual stroke
> exam, auto-segmented into 218 gold-labeled item clips — see
> [research_and_eval/NINDS_dataset.md](research_and_eval/NINDS_dataset.md)). **ProGait** is the
> **secondary** scale-eval ([research_and_eval/ProGait_Dataset.md](research_and_eval/ProGait_Dataset.md)),
> run later if time permits. The screening notes below are retained as the research record that led
> to that choice.

Candidate **public medical/clinical video datasets** for the MedBridge multimodal
co-clinician prototype, screened for the "observe → reason → ask follow-up → coach"
loop described in [ProjectPlan.md](ProjectPlan.md).

> **Status:** research shortlist, not a committed choice. Figures are as reported by the
> screening pass (checked 2026-07-18); some were independently confirmed on Hugging Face /
> GitHub (noted inline), the rest still need a hands-on access + license check before use.

## ⚠️ Read before using any dataset here

- **License / access review is required per dataset.** Several are research-only,
  noncommercial (CC BY-NC), or gated behind registration or an author's email approval.
  Confirm the terms allow a hackathon demo before downloading or presenting.
- **Privacy stance still holds.** Per MedBridge policy, demonstrations use **synthetic,
  staged, de-identified, or consented** data only. These are consented research datasets,
  but do not re-identify subjects, and prefer face-blurred / de-identified clips for any
  public demo. See [README.md](README.md) → Privacy and Data Handling.
- **None of these replaces staging your own clips.** For the primary neuro-screening
  (FAST) demo, a couple of short self-recorded, consented clips remain the most reliable
  and privacy-safe option — and they double as gold-labeled eval scenarios.

## TL;DR picks

| Goal | Pick | Why |
|---|---|---|
| **Safest build for a 24h hackathon** | **REHAB24-6** | Immediate Zenodo download (`videos.zip`), explicit correctness labels, clean RGB clips |
| **Best overall clinical fit** | **KIMORE** | Clinician-scored rehab exercises, RGB+depth, rich for observe-and-coach |
| **Best neuro-exam concept** | **TULIP** | 6-view UPDRS motor tasks, 3-clinician ratings — closest to a neuro-exam benchmark (⚠️ restricted access) |
| **Best procedural coaching / emergency** | **CPR Performance** | 6-angle chest-compression clips + expert ratings; urgent, observable, demo-friendly (⚠️ registration + owner permission) |
| **Broadest HF-hosted corpus** | **MedVideoCap-55K** | Verified on HF, ships video zips; but broad curation, not technique/exam-specific |

Practical route: **REHAB24-6 first** (lowest integration risk), add **KIMORE** as the more
clinical second track if time allows. For the judge-facing thesis, pitch **TULIP** (neuro) +
**CPR** (procedural), being candid about their access friction.

## Ranked shortlist

Access legend: 🟢 immediate · 🟡 registration/email/permission · 🔴 restricted.
"Video?" = ships actual RGB video clips (vs. depth/skeleton/QA-only).

| # | Dataset | Domain | Video? | Access | License (as reported) | Hackathon readiness | Source |
|---|---|---|:--:|:--:|---|---|---|
| 1 | **KIMORE** | Rehab / movement assessment | ✅ RGB+depth+skeleton | 🟡 SharePoint | Research; license unclear on page | High (if download works) | [VRAI page](https://vrai.dii.univpm.it/content/kimore-dataset) |
| 2 | **TULIP** | Neuro motor exam (Parkinson's) | ✅ 6-view RGB | 🔴 restricted Zenodo | Restricted research | Medium (access friction) | [Zenodo](https://zenodo.org/) |
| 3 | **CPR Performance** | CPR / basic life support | ✅ 6-angle (faces blurred) | 🟡 UKDS + owner permission | UK Data Service EUL | Medium (permission) | [UK Data Service ReShare](https://reshare.ukdataservice.ac.uk/) |
| 4 | **REHAB24-6** | Physical therapy / form correctness | ✅ RGB | 🟢 Zenodo | CC BY-NC 4.0 (academic/non-profit) | **Very high** | [Zenodo](https://zenodo.org/) |
| 5 | **Keraal** | Low-back-pain rehab | ✅ RGB (mp4/avi) | 🟢 author-hosted | BSD-2 (repo); data page recheck | Medium-high | [GitHub](https://github.com/) |
| 6 | **UCO Physical Rehab** | Rehabilitation | ✅ per-camera avi | 🟡 email request | Unclear on repo | Medium | GitHub (AVA group) |
| 7 | **Health&Gait** | Gait / mobility | ✅ RGB | 🟢 Zenodo | GPL-3.0 repo / open Zenodo | High | GitHub + Zenodo |
| 8 | **MedVideoCap-55K** | Broad medical corpus | ✅ video zips | 🟢 Hugging Face | Apache-2.0 (not for clinical use) | High (integration) | `FreedomIntelligence/MedVideoCap-55K` ✔ on HF |
| 9 | **MM-Fit** | Exercise monitoring | ✅ RGB (39 GB) | 🟢 Zenodo | CC BY 4.0 | High | Zenodo |
| 10 | **K3Da** | Balance / frailty mobility | ⚠️ depth+skeleton only | 🟢 Dropbox | Free non-commercial | Medium | Project page |
| 11 | **KINECAL** | Falls-risk / balance | ⚠️ depth+skeleton only | 🟢 PhysioNet | Open (PhysioNet) | Medium | PhysioNet |

### Dataset facts (as reported)

- **KIMORE** — 78 subjects, 5 physician-selected low-back rehab exercises; clinician
  questionnaire scores + physician-defined features; healthy vs. patient groups.
  *IEEE TNSRE; Università Politecnica delle Marche.* Narrow exercise set.
- **TULIP** — synchronized 6-camera RGB of UPDRS-aligned tasks (gait, finger tapping);
  labels from 3 clinicians + calibration metadata. *CVPR 2024; Duke.* PD-specific; restricted.
- **CPR Performance** — 6-angle manikin chest-compression videos (41 participants of video,
  42 of eval); 2 expert ratings + agreed rating + demographics. Manikin-only.
- **REHAB24-6** — 65 recordings, 184,825 frames, 1,072 reps; deliberate mistakes; rep
  segmentation + correctness labels + 2D/3D joints. Zenodo `videos.zip`. Rehab form, not diagnosis.
- **Keraal** — anonymized RGB rehab clips; correct/incorrect + error type + body part +
  temporal localization + physiotherapist comments + skeleton. *IJCNN 2024.* Author-hosted.
- **MedVideoCap-55K** — 55,803 medical videos (education, clinical, imaging, teaching,
  pop-sci); model-generated captions; six `videos_*.zip` + JSON. **Verified on HF.** Mixed
  content quality; not technique/maneuver-focused.

## Per-dataset demo concepts (top 5)

Each follows the ProjectPlan turn loop: sample frames → conservative structured observation
→ one follow-up question → conservative corrective prompt → explicit safety/escalation rule.
Sampling guidance from the report:

- **KIMORE** — 6–10s clip @ ~1 fps + one mid-sequence clip. Observe alignment, ROM, symmetry,
  hesitation, compensation. Ask: *"Any pain, weakness, dizziness, or limited range on one side?"*
- **TULIP** — motor-task clip @ 1–2 fps + a 2–3s peak-movement clip. Observe bradykinesia-like
  slowness, asymmetry, reduced arm swing, tap-rhythm irregularity. Ask: *"Is this your usual
  pattern, and mainly one-sided?"* Screening only; focal weakness/droop → urgent in-person eval.
- **CPR** — 5–10s compression segment @ 2 fps + one contiguous clip. Observe hand placement,
  posture, interruptions, consistency. Ask: *"Has emergency help been called; is an AED available?"*
  Educational/decision support only — real emergencies require immediate EMS activation.
- **REHAB24-6** — full repetition @ 1 fps (begin/mid/end frames). Identify exercise,
  correct/incorrect, off segment, incompleteness. Ask: *"Full rep, or did pain/fatigue stop it early?"*
- **Keraal** — one rep @ 1 fps + a compact clip around the usual error window. Output exercise,
  global correctness, suspected error type, responsible body part, temporal segment.

In every case the structured output includes: observed finding, confidence, what **cannot** be
verified visually, and a next-step prompt — and the safety rule forbids diagnosis and mandates
escalation for severe pain, neurologic symptoms, or sudden decline.

## Excluded / near-miss (don't be fooled by the names)

- **Trauma THOMPSON** — real and highly relevant (3,717 egocentric life-saving-intervention
  clips), but **not on Hugging Face**. Videos are on **Harvard Dataverse**
  ([doi.org/10.7910/DVN/V5BTRU](https://doi.org/10.7910/DVN/V5BTRU)); code at
  [purdue-isat/TT](https://github.com/purdue-isat/TT) and [zhuoyp/TTD](https://github.com/zhuoyp/TTD).
- **MedVidQA** — real, but **YouTube-based**: [deepaknlp/MedVidQACL](https://github.com/deepaknlp/MedVidQACL)
  ships IDs/subtitles/I3D features, not raw MP4s. Expect a download step and some dead links.
- **OpenBiomedVid** (`connectthapa84/OpenBiomedVid`) — on HF, but a JSON/text-style release
  rather than shipped video.
- **SurgeryVideoQA** (`connectthapa84/SurgeryVideoQA`) — on HF, but a QA release, not a video corpus.
- **MedVidBench** (`UII-AI/MedVidBench`) — on HF, but the public release is questions only.
- **UCOPhyRehab++** — credible, but the public Zenodo release ships processed modalities, not raw RGB.
- **K3Da / KINECAL** — clinically meaningful and downloadable, but **depth/skeleton only** —
  weaker fit for a frame-sampling → general multimodal-API pipeline. Kept as low-rank backstops.

## Pipeline note

The download → OpenCV/Pillow extract → resize → base64 → `claude-opus-4-8` (Extractor) path is
already validated end-to-end (see the smoke tests run during setup). Any dataset above that ships
real RGB video can drop straight into that path; the reusable extraction logic will live in
`video/processor.py` when the vertical slice is built.
