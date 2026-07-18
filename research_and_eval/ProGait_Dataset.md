# ProGait — Evaluation Dataset

The primary **labeled video dataset** for MedBridge's offline evaluation harness
([research_and_eval/](.)). Chosen because it is open-access (after a one-time terms
acceptance), large enough for statistically meaningful evals (**412 clips**), ships **real
RGB video** (not depth/mesh), and — critically — its gold annotations mirror MedBridge's own
observe → identify → recommend → justify loop.

> **ProGait: A Multi-Purpose Video Dataset and Benchmark for Transfemoral Prosthesis Users**
> Yin, Yang, Liu, Xue, Alamri, Fiedler, Gao — ICCV 2025.
> Paper: <https://arxiv.org/abs/2507.10223> · HF: [`ericyxy98/ProGait`](https://huggingface.co/datasets/ericyxy98/ProGait)

## What it is

412 video clips of **four above-knee (transfemoral) amputees** walking trials while testing
newly-fitted prosthetic legs, filmed indoors and outdoors. It depicts the presence, contours,
poses, and gait patterns of subjects with transfemoral prostheses.

**License: CC-BY-NC-SA-4.0** — non-commercial, share-alike, attribution required. Fine for a
research/hackathon demo; **not** for commercial use. Cite the paper.

## Access (one-time)

The repo is **gated (auto-approve)** — a programmatic token cannot accept the terms, so accept
once in the browser, then all downloads work with your `HF_TOKEN`:

1. Open <https://huggingface.co/datasets/ericyxy98/ProGait> → click **Agree / Access repository**.
2. Ensure `HF_TOKEN` is in `.env` (already configured for this project).
3. Pull files with `huggingface_hub.snapshot_download("ericyxy98/ProGait", repo_type="dataset")`.

**Local copy already downloaded** (full 6.72 GB snapshot, verified):
`~/.cache/huggingface/hub/datasets--ericyxy98--ProGait/snapshots/<hash>/` — 412 clips +
412 segmentation XMLs + keypoints/masks. Re-calling `snapshot_download` returns the cached path
instantly.

## Label schema — three annotation tracks per clip

| Track | Files | Contents |
|---|---|---|
| **Video Object Segmentation** | `*_masks.npy.gz`, `*_annotations.xml` | Bounding boxes + segmentation masks of the subject |
| **2D Human Pose Estimation** | `*_keypoints.npy.gz` | 23 COCO-wholebody keypoints (17 body + 6 feet) |
| **Gait Analysis** | `annotations/**/*.txt` | Structured clinician text (below) |

> **Label coverage (verified on the local copy):** segmentation + pose cover **all 412 clips**;
> the **gait-analysis `.txt` gold labels cover 150 clips**. The MedBridge-relevant deviation/
> recommendation eval therefore has **~150 gold-labeled clips** — still well past an n≥100
> significance bar. Use the full 412 for the segmentation/keypoint grounding checks.

### The gait-analysis text (the gold MedBridge scores against)

Each clip's `.txt` has a **four-part structure**, plus a secondary-issues block:

1. **Gait category** — a class label (e.g. `CCC: 1`)
2. **Specific deviation** — e.g. *"internally rotated foot"*, *"insufficient knee flexion"*
3. **Recommendation** — the correction, e.g. *"rotate foot outward underneath knee"*
4. **Reason** — justification, e.g. *"toe-out does not mirror the sound leg… patient may trip"*

This is not a bare positive/negative set: it is a **multi-class deviation taxonomy with paired
corrections and justifications**. A positive/negative split (deviation present vs. clean) is
trivially derivable, and non-gait clips can be mixed in as out-of-scope negatives.

### Why the structure matters

The gold annotation is literally **observe → identify deviation → recommend → justify** — the
same loop MedBridge runs across Extractor → Planner → Talker → Verifier. So each field maps to
a module output you can score directly:

| ProGait field | MedBridge module it evaluates |
|---|---|
| Specific deviation | Evidence Extractor / Clinical Planner (did we spot it?) |
| Recommendation | Talker (is our corrective guidance aligned?) |
| Reason | Planner/Verifier (is our justification sound?) |
| (finding **not** in gold) | Safety Verifier (unsupported-claim / hallucination) |

## How MedBridge uses it (eval designs)

See the four `research_and_eval` system variants (Talker-only, +Verifier, +Planner, full).
Recommended runs:

- **Deviation-detection scorecard** — deterministic/keyword or blinded LLM-judge match of the
  pipeline's claimed deviations against the gold list → recall / precision / F1, plus a
  confusion matrix over deviation categories.
- **Ablation (headline result)** — run all four variants on the same clips; show deviation
  recall rises and **unsupported-claim rate falls** as the Planner and Verifier are added —
  evidence the safety architecture earns its complexity.
- **Grounding / hallucination rate** — count findings not present in gold; use pose keypoints
  as a proxy for "was the relevant limb actually visible?" (ties to the "not safe without the
  evidence" principle).
- **Verifier red-team** — pair each clip's correct recommendation with a plausible-but-wrong
  distractor built from another clip's label; measure the Verifier's catch rate.
- **Out-of-scope specificity** — mix in non-gait clips and confirm the Extractor abstains
  rather than confabulating.

**Framing for judges (honest scope):** ProGait is transfemoral **prosthetic gait**. Report
results as *"the system's observations align with clinician gait annotations X% of the time"* —
a technical alignment benchmark, **not** clinical validation. Consistent with the project rule
that LLM-as-judge results are never treated as clinical validation.

## Verified pipeline — smoke tests A–D (measured)

Full path `HF snapshot → OpenCV frame sampling → resize/JPEG/base64 → Claude vision (forced JSON)`
confirmed working on the local copy:

| Test | Setup | Result |
|---|---|---|
| **A** bare minimum | 1 clip, 1 frame, Opus 4.8 | 7.8s, 1287in/300out, valid schema ✓ |
| **B** minimal video | 1 clip, 3 frames (evenly spaced), Opus 4.8 | 12.3s, 2859in/680out ✓ |
| **C** minimal batch | 4 clips, 3 frames each, Opus 4.8 | 50.4s total, **~12s/clip** ✓ |
| **D** model bake-off | same 3 frames, Opus vs Haiku | Opus 11.2s ~**$0.030**/call · Haiku 9.6s ~**$0.0044**/call ✓ |

**Sampling:** clips are short (a few seconds), so **1 fps often yields a single frame** — use
**evenly-spaced N frames** (e.g. N=3) instead; it produced markedly richer observations
(*"parallel bars, both hands on rails for support"* vs. a single ambiguous frame).

**Model choice (from D):** Haiku 4.5 is **~6.7× cheaper and slightly faster** than Opus 4.8 for the
Extractor role. Budget implication for a **150-clip × 4-variant** ablation (600 calls): ≈ **$18 on
Opus vs ≈ $2.6 on Haiku**; wall-clock ≈ 2h serial (parallelize to cut it). Reserve Opus 4.8 for the
Planner/Verifier reasoning calls where quality matters most.

---

## Clinical relevance beyond prosthetics — and why the architecture generalizes

ProGait is prosthetic gait, but **gait and movement analysis is a shared perceptual primitive
across many clinical workflows.** The same "observe posture, limb movement, symmetry, stability,
and deviation from expected motion" capability transfers to:

| Domain | Gait / movement signal MedBridge would observe |
|---|---|
| **Stroke (MedBridge primary)** | Hemiparetic gait, arm-drift asymmetry — the "A" in FAST is the same asymmetry-detection task |
| **Parkinson's disease** | Shuffling/festinating gait, reduced arm swing, freezing, bradykinesia |
| **Cerebellar / ataxic disorders** | Wide-based unsteady gait, incoordination |
| **Multiple sclerosis, neuropathy** | Foot drop, spasticity, balance loss |
| **Orthopedics / post-surgical rehab** | Antalgic gait, ROM limits, compensation patterns |
| **Geriatrics / falls & frailty** | Balance, sit-to-stand, Timed-Up-and-Go mobility |
| **Cerebral palsy, pediatric rehab** | Crouch gait, tone-related deviations |

The clinical *content* differs, but the **model infrastructure does not.** MedBridge's
architecture deliberately separates the workflow-agnostic engine from the task-specific
knowledge:

- **Reused unchanged for any new task** (the "infra"): frame sampling and quality gating
  (`video/`), the shared Claude client (`api/`), typed Pydantic boundaries and structured-output
  discipline (`models/`), encounter-state validation and response routing (`services/`), audit
  logging, and **this evaluation harness** (`research_and_eval/`).
- **Swapped per task** (the "knowledge"): a workflow definition (`workflows/<task>.yaml`), the
  agent system prompts (`prompts/`), and a labeled dataset for evaluation.

So onboarding a new medical task is **not** a rebuild — it is: add a YAML workflow, tune the
prompts, and plug in a labeled dataset. The Extractor still extracts source-attributed evidence;
the Planner still manages goals; the Verifier still gates unsafe output; the harness still scores
against gold labels. **ProGait both validates the perception+reasoning stack today and serves as
the template for how future datasets (stroke, Parkinson's, CPR, rehab) drop into the same
pipeline** — the decisive test being whether an observe→deviation→recommend→justify dataset can
be scored without touching the engine. ProGait shows it can.
