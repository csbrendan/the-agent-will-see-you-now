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

**Scored inventory** (verified against the full verbatim transcripts — see §3.2 for the complete
table with per-limb scores and rationale; `n/a` = the patient's exam did not segment that item):

| Item | 4 Facial | 5 Arm | 6 Leg | 9 Lang | 10 Dysar | 11 Ext | 1a LOC | 1b Q | 1c Cmd | 2 Gaze | 3 VF | 7 Ataxia | 8 Sens |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **A** (`1.3`) | 1 | 0 | 1 | 0 | 1 | 0 | 0 | n/a | n/a | 0 | 0 | 0 | 0 |
| **B** (`1.4`) | 2 | 2 | 3 | 2 | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

Patient A total **NIHSS 4** (mostly normal); Patient B total **NIHSS 17** (multiple abnormal). Together
they give **both positive (abnormal) and negative (normal) examples**, but coverage is **thin**: 1–2
labeled examples per item, and only **two items — Motor Arm (0 vs 2) and Best Language (0 vs 2)** —
have a clean normal-*and*-abnormal pair. (Motor/facial/dysarthria items have abnormals but no matching
normal; the rest are normal-only.)

> ⚠️ **Leakage risk.** For the demo patients the transcript *literally contains the answer*
> ("scored as a two"). If the raw transcript is fed to the model, the eval leaks the gold. The
> examiner's scoring commentary **must be split off** (held out as gold) from the exam-performance
> portion the model is allowed to see. See §8 for how this shapes the eval.

**To unlock the 194 certification items** for outcome eval you need the **official NINDS
certification answer key** (check whether it's published) or an expert/hand-labeling pass on a chosen
subset. Until then, cert clips are gold for *item-type / observation / abstention* evals, not scoring.

### 3.2 The complete labeled set — 24 clips with ground-truth scores

Every clip below is a **demonstration-patient** item where the examiner narrates the NIHSS score *inside the transcript* (the ground truth). Base path for the Directory column: `sample_data/ninds/segmented/`. Motor Arm/Leg are scored **per limb** (A = right, B = left). The score phrase is inside each transcript — that is the leakage span to hold out for scoring evals (§8).

| Directory | Clip | NIHSS item | Gold score | Transcript (Whisper `base`, verbatim) |
|---|---|---|:--:|---|
| `gov.hhs.ninds.stroke.1.3` | `1a.mp4` | 1a Level of Consciousness | **0** | Do you feel comfortable right now? Yes, I do. Are you in any pain? No. How old are you today? 71. And do you know what month it is now? Well, it's February. Can you close your eyes and now open your eyes? Can you make a fist with your hand and now open your hands? An item one, he would score a zero. His age was 71. And although he hesitated on what month it is, he did get it correct. It's February. |
| `gov.hhs.ninds.stroke.1.3` | `2.mp4` | 2 Best Gaze | **0** | It's February. I'll hold them up for you. Follow my finger with your eyes. Great. On best gaze, he also got a zero. It may have been difficult to see that his right eye did go all the way to the right. |
| `gov.hhs.ninds.stroke.1.3` | `3.mp4` | 3 Visual Fields | **0** | did go all the way to the right. Now, I want you to look at my nose and I'm going to wiggle my fingers on the outside to test your vision. Can you do it with one hand covering one eye? And look right here at my eye and tell me if you see my hands moving. Yeah. Can you point to the hand that moves? Great. Great. Look at my eye. Great. Great. Now I'm going to have you cover the other eye. Put that one down. Terrific. And look at my eye and point to my hand that wiggles. Great. You can put your hand down. Anything wiggling? Great. Great. Unvisual field, he would score a zero. I did need to remind him to keep focused on the target my nose and to reposition his arms. Now, can you show me your teeth? |
| `gov.hhs.ninds.stroke.1.3` | `4.mp4` | 4 Facial Palsy | **1** | Now, can you show me your teeth? Great. Can you raise your eyebrows? Terrific. And now squeeze your eyes shut. Great. All right. You can open your eyes. For facial palsy, he would get a one for a decreased right nasal labial fold. This was somewhat subtle. And sometimes when I'm trying to assess a subtle facial weakness, I have the patient smile. And then I count the number of teeth on both sides. The side with the weakness generally has fewer teeth showing. Now I'm going to have you hold your arms up for the count of ten. |
| `gov.hhs.ninds.stroke.1.3` | `5.mp4` | 5 Motor Arm | **0 / 0 (per arm)** | Now I'm going to have you hold your arms up for the count of ten. One, two, three, four, five, six, seven, eight, nine, ten. Great. Down right there. Great. One, two, three, four, five, six, seven, eight, nine, ten. Terrific. You can put your arms down. On motor arm, he scored a zero for each arm. Let's hold this leg up for the count of five. |
| `gov.hhs.ninds.stroke.1.3` | `6.mp4` | 6 Motor Leg | **1 / 1 (per leg)** | Let's hold this leg up for the count of five. Ready? One, two, three, four, five. Great. One, two, three, four, five. Terrific. He scores a one point for each leg. After the initial dip, he continued a downward drift of both his left and his right leg. He does not score a two because his leg did not drift down and touched the bed. Now I want you to make a pointer finger with your hand. |
| `gov.hhs.ninds.stroke.1.3` | `7.mp4` | 7 Limb Ataxia | **0** | Now I want you to make a pointer finger with your hand. Touch my finger and then touch your nose. Back and forth. Now touch your nose. My finger. Your nose. My finger. Your nose. Your nose. Excellent. Now let's do it with the other hand. My finger. Your nose. My finger. Your nose. My finger. Your nose. Great job. Now I'm going to have you put your heel right on your knee and slide it right down your shin. Okay? Can you do that? Can you bring it back up? And now do it again. Put your heel right down. Slide it down. And then bring it back up your shin. Okay. Good. Let's have you do it with the other leg. With this heel on this shin and slide it right down the heel. Go ahead and slide it back up and slide it back down. Terrific. On Limey Taxia he would score a zero. He did not have a taxi on either his finger to nose or his heel to shin. |
| `gov.hhs.ninds.stroke.1.3` | `8.mp4` | 8 Sensory | **0** | He did not have a taxi on either his finger to nose or his heel to shin. I want to see if it feels different on the left the right or it feels the same. All right? No, the same. Feels the same. I'm going to do the same thing on your legs. It feels the same. I'm going to do the same thing on your face. I'll be gentle. Okay. On sensory testing he scores a zero. Let me give you your glasses because I'm going to have you read some things for me. |
| `gov.hhs.ninds.stroke.1.3` | `9.mp4` | 9 Best Language | **0** | Let me give you your glasses because I'm going to have you read some things for me. Okay. Great. Now can you describe what's going on in this picture? Yes. The sink is overflowing and the cookie jar. He's on a stepsuit and the cookie jar. The stepsuit is tipping over. And that's about it. And the woman is well trying to dishes and that was about it. Okay. Great. Can you name these objects? The key glove, feather, hammock, chair. And I don't know. It's a cactus. Great. Now you read some things. Down the earth. I got home from work near the table and the dining table, the dining room table. I heard him speak and he'd let radio last night. Great. On language testing, he scores a zero. Even though he hesitated, he eventually did get the word cactus. |
| `gov.hhs.ninds.stroke.1.3` | `10.mp4` | 10 Dysarthria | **1** | Even though he hesitated, he eventually did get the word cactus. Can you read these? Mama, tips app, 50-50. Thank. Huckleberry, baseball player. Terrific. On Dessartria, he scores a one for slurred speech. A zero would be when there's crystal clear speech and a two would be when it's almost unintelligible speech and anything in between would score a one. Now I'm going to touch you |
| `gov.hhs.ninds.stroke.1.3` | `11.mp4` | 11 Extinction/Inattention | **0** | and anything in between would score a one. Now I'm going to touch you on the left side, the right side or both sides and I want you to close your eyes and tell me where I touch you. Left, that's the right. Right, that's right. I'm going to do it on your face. Left, that's right. Right. I'm going to move on the left, the right, or both and I want you to point to what's wiggling. Terrific. On item 11, he would score a zero. He did not extinguish on either visual or tactile stimuli. I did notice earlier in my exam that he did not describe the little girl in the cookie jar picture but taking the whole exam into account, I would not give him a point for this item. This patient's total NIH stroke scale score would be four. |
| `gov.hhs.ninds.stroke.1.4` | `1a.mp4` | 1a Level of Consciousness | **0** | Good morning. Are you having any pain? Yeah. One A is scored as a zero because he was alert and answered my questions. |
| `gov.hhs.ninds.stroke.1.4` | `1b.mp4` | 1b LOC Questions | **2** | because he was alert and answered my questions. Can you tell me what the month is? And can you tell me how old you are? One B was scored as a two because this patient answered both questions incorrectly. Can you close your eyes? |
| `gov.hhs.ninds.stroke.1.4` | `1c.mp4` | 1c LOC Commands | **0** | Can you close your eyes? Good. Now open your eyes. Can you open your eyes? Good. Okay. I'm just going to get your arm here. Can you give me a big squeeze here? Good. Let go. Can you let go? Very good. One C would be scored as a zero because he was both able to open and close his fist as well as open and close his eyes. Okay. I'm going to check how your eyes are moving now. |
| `gov.hhs.ninds.stroke.1.4` | `2.mp4` | 2 Best Gaze | **0** | Okay. I'm going to check how your eyes are moving now. Can you look right at me? Can you use your eyes to look at me? Good. Just follow my eyes. Follow my face with your eyes. Okay. Just look right at me. Follow me. See me? Look right at my face. Follow me. Follow me all the way over here. Follow me all the way to the left. You're right side. All the way over here. Follow me all the way over here. That's it. Very good. Very good. Two was scored as a zero because he was able to look to extremes of gaze horizontally. Can you look right at my nose? |
| `gov.hhs.ninds.stroke.1.4` | `3.mp4` | 3 Visual Fields | **0** | Can you look right at my nose? I'm going to be testing your peripheral vision. How many fingers do you see? Three. Okay. You look right at my nose. How many fingers do you see? Okay. Try to concentrate right at my nose. How many fingers? You're doing just fine. Look right at my nose. Do you see any fingers? How many fingers do you see? Look right at my nose. How many fingers? Three. Okay. How many fingers do you see? How many fingers do you see? Look right at my nose. How many fingers? How many do you see? Three. I cried in my nose. Keep looking at my nose. Good, keep looking right at my nose. I want to try the other eye, okay? Okay, I cried in my nose. I cried in my nose. Three was scored as a zero, because he was able to blink to thread in all four visual quadrants. This patient demonstrates the difficulty of testing visual fields in an aphasic patient. |
| `gov.hhs.ninds.stroke.1.4` | `4.mp4` | 4 Facial Palsy | **2** | of testing visual fields in an aphasic patient. Show me your teeth. Good. Close your eyes tightly. Okay. You make your eyebrows go up. You can open your eyes. Make your eyebrows go up really big. Can you open your eyes? Okay, good. Four is scored as a two, because he shows a clear-cut upper motor neuron facial weakness. |
| `gov.hhs.ninds.stroke.1.4` | `5.mp4` | 5 Motor Arm | **2 / 1 (5A / 5B)** | neuron facial weakness. Can you lift up this arm off the bed? Hold it up here. Just really extend it out there. Good, and we're going to do this for the count of ten, okay? One, two, three, four, five, six, seven, eight, nine, ten. Okay, you can relax that one down. Five A was scored as a two, because the patient's arm eventually hit the bed. Can extend this arm straight out. Try your best. That's it. Excellent. Just hold it there for a count of ten. Okay, hold it right up there. One, two, three, four, five, six, seven, eight, nine, ten. Good. Relax that hand down. Five B is scored as a one. Now, I want you to lift up your left leg. |
| `gov.hhs.ninds.stroke.1.4` | `6.mp4` | 6 Motor Leg | **3 / 3 (6A / 6B)** | Now, I want you to lift up your left leg. I'm just going to help you here a little bit. Okay. Just going to hold it for the count of five. Okay. I'm going to let go. One, two, okay. Can you move your left leg? Six A was scored as a three. This was not scored as a four, because some movement was possible. Okay, I'm going to help you lifting this up. Lift it up in the air and try to hold it here the best you can, okay? One, two, and now let's try the right leg. Okay. Six B was also scored as a three. This was not scored as a four, because some proximal movement was possible. Can you touch my finger here? |
| `gov.hhs.ninds.stroke.1.4` | `7.mp4` | 7 Limb Ataxia | **0** | Can you touch my finger here? Can you try to touch my finger? That's excellent. Now touch your nose. Touch your nose. Good. Touch my finger again. Touch my finger. Can you touch my finger? That's it. Come and touch my finger. Okay. Let's try the other arm. Okay. You can relax this one. You touch my finger with your finger? Can you reach my finger with your finger? You touch my finger here? Okay. Can you touch your nose with this finger? Good. Good. Try and touch my finger. That's it. Good. Keep going. Okay. We're going to do the same thing with the legs now. Just want to have you run your heel up and down your shin. And I'm going to help you a little bit here. Can you run your heel up and down your shin? Okay. We'll try the other side, okay? Just going to move this leg. Bend your knee a little bit. Is that hurt? Can you run your heel up and down your shin? Seven with scored is a zero. Even though this patient is weak, he scored a zero because no, a taxi was demonstrated. |
| `gov.hhs.ninds.stroke.1.4` | `8.mp4` | 8 Sensory | **0** | he scored a zero because no, a taxi was demonstrated. Okay. I'm just going to see if you can feel this sensation here. Okay. Let's try the other side, okay? I'm going to try on the foot here, okay? Eight with scored is a zero because he withdrew from painful stimuli on both sides. I'm going to put on your glasses here so that you can see. |
| `gov.hhs.ninds.stroke.1.4` | `9.mp4` | 9 Best Language | **2** | I'm going to put on your glasses here so that you can see. Can you describe what's going on in this picture? We'll try this one. Can you name this? What is this? Since you're having some problems naming these verbally, let's see if you can do any writing here. I'm going to give you this hand. Can you hold onto the pen? And here we have a piece of paper to write with. Can you write what this object is here? Can you tell me by writing what this is? Nine is scored as a two. Three is a reserve for patients who are mute and unable to follow single step commands. |
| `gov.hhs.ninds.stroke.1.4` | `10.mp4` | 10 Dysarthria | **2** | and unable to follow single step commands. Can you read this? Ten is scored as a two due to his unintelligible speech. I want you to close your eyes and tell me |
| `gov.hhs.ninds.stroke.1.4` | `11.mp4` | 11 Extinction/Inattention | **0** | I want you to close your eyes and tell me if I'm touching on the right side of the left side or both. Okay. Can you feel me touching you? Yes. Is it the right side or the left side or both? Okay. You can open your eyes. Eleven is scored as a zero. Despite his aphasia, he was able to attend to both sides. This patient's total NIH stroke scale score is a 17. |

**Patient A total NIHSS = 4  (Patient A — mostly normal). Patient B total NIHSS = 17 (Patient B — multiple abnormal).** These two patients are the *entire* outcome-labeled set today; all 17 certification patients (items 2.1–2.17) are item-typed but score-unlabeled (§3.1).

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
