# NIH Stroke Scale (NIHSS) — Scoring Reference

**Source:** *NIH Stroke Scale*, NINDS / Know Stroke (`stroke.nih.gov`, 1-800-352-9424),
March 2025 508-compliant edition — the PDF is committed alongside this file at
[`KnowStroke_NIHStrokeScale_March2025_508c.pdf`](KnowStroke_NIHStrokeScale_March2025_508c.pdf).
Test materials (picture description, naming sheet, reading sentences, dysarthria words) are on
pp. 10–13 of that PDF and transcribed at the end of this document.

> **What this file is for.** This is the **canonical, deterministic scoring rubric** MedBridge
> works to. In the pipeline the models produce *observations* ("the right arm drifted to the bed
> within the 10 s hold"); **deterministic application code maps observations → score using the
> definitions below** — the rubric is not something a model is asked to invent. Per-item **MedBridge
> capture** notes tie each item to the observability/modality policy in
> [`video/processor.py`](../video/processor.py) so the agent knows, up front, what is assessable
> from an audiovisual capture and what must be escalated to a clinician.
>
> ⚠️ MedBridge is an experimental research prototype — **not** a certified NIHSS rater and **not** a
> medical device. This reference exists so the system's outputs are grounded in and traceable to the
> official scale; it does not make the system clinically validated.

---

## Global administration rules (PDF p. 2)

- **Administer items in the order listed** (1a → 11).
- **Record performance in each category after each subscale exam.**
- **Do not go back and change scores.**
- Follow the directions provided for each exam technique.
- **Score what the patient _does_, not what the clinician thinks the patient _can_ do.**
- Record answers while administering the exam, and **work quickly**.
- **Except where indicated, do not coach the patient** (no repeated requests to make a special effort).

**Cross-item automatic rules (must be enforced deterministically):**
- **Coma (item 1a = 3)** → item **9 (Best Language) automatically = 3**, and item **8 (Sensory)
  automatically = 2**.
- **Item 3 (Visual):** double simultaneous stimulation is performed here; **if there is extinction,
  the patient scores 1 on item 3 and that result feeds item 11.**
- **Item 11 (Extinction) is never untestable** — it is scored only if abnormality is present.
- **Motor items 5 & 6:** test **each limb in turn, beginning with the non-paretic limb.**

---

## Item-by-item rubric

Score-range and the verbatim scale definitions are authoritative. "Instructions" are condensed from
the PDF; consult the PDF for the full technique text.

### 1a · Level of Consciousness (LOC) — range 0–3
**Instructions:** Choose a response even if full evaluation is prevented (endotracheal tube, language
barrier, orotracheal trauma/bandages). Score **3 only** if the patient makes **no movement** (other
than reflexive posturing) to noxious stimulation.

| Score | Definition |
|---|---|
| 0 | Alert; keenly responsive. |
| 1 | Not alert; but arousable by minor stimulation to obey, answer, or respond. |
| 2 | Not alert; requires repeated stimulation to attend, or is obtunded and requires strong/painful stimulation to make (non-stereotyped) movements. |
| 3 | Responds only with reflex motor or autonomic effects, or totally unresponsive, flaccid, areflexic. |

*MedBridge capture:* **MIXED / observable** — alertness/responsiveness is visible; the examiner's
prompts and the patient's responses come via **audio**. Static frames (2–4) + transcript.

### 1b · LOC Questions — range 0–2
**Instructions:** Ask the patient **the month** and **their age**. The answer must be **exactly
correct** — no partial credit for "close". Aphasic/stuporous patients who don't comprehend score **2**.
Patients unable to speak for reasons **not secondary to aphasia** (intubation, orotracheal trauma,
severe dysarthria, language barrier) score **1**. **Grade only the initial answer; do not cue.**

| Score | Definition |
|---|---|
| 0 | Answers both questions correctly. |
| 1 | Answers one question correctly. |
| 2 | Answers neither question correctly. |

*MedBridge capture:* **AUDIO / observable** — graded from the **Whisper transcript**. **0 frames.**

### 1c · LOC Commands — range 0–2
**Instructions:** Ask the patient to **open and close the eyes**, then **grip and release the
non-paretic hand** (substitute another one-step command if hands can't be used). **Credit an
unequivocal attempt not completed due to weakness.** If no response, demonstrate (pantomime) and
score the result. **Only the first attempt is scored.**

| Score | Definition |
|---|---|
| 0 | Performs both tasks correctly. |
| 1 | Performs one task correctly. |
| 2 | Performs neither task correctly. |

*MedBridge capture:* **VISUAL / partial** — command-following (eyes open/close, grip/release) is
**visible**; grip **strength** is haptic and **not on camera**. Short temporal sequence.

### 2 · Best Gaze — range 0–2
**Instructions:** Test **horizontal eye movements only** (voluntary or reflexive/oculocephalic). If a
conjugate deviation is **overcome** by voluntary/reflexive activity → **1**. Isolated peripheral
nerve paresis (CN III/IV/VI) → **1**. Gaze is testable in all aphasic patients.

| Score | Definition |
|---|---|
| 0 | Normal. |
| 1 | Partial gaze palsy; gaze abnormal in one or both eyes, but no forced deviation / total gaze paresis. |
| 2 | Forced deviation, or total gaze paresis not overcome by the oculocephalic maneuver. |

*MedBridge capture:* **VISUAL / observable** — gaze tracking is **motion over time** → ordered
sequence.

### 3 · Visual Fields — range 0–3
**Instructions:** Test upper & lower quadrants by confrontation (finger counting or visual threat).
Score **1 only** for a clear-cut asymmetry (incl. quadrantanopia). If blind from any cause → **3**.
**Double simultaneous stimulation is performed here** (extinction → item 3 = 1, feeds item 11).

| Score | Definition |
|---|---|
| 0 | No visual loss. |
| 1 | Partial hemianopia. |
| 2 | Complete hemianopia. |
| 3 | Bilateral hemianopia (blind, incl. cortical blindness). |

*MedBridge capture:* **MIXED / partial** — the maneuver is visible but the grade depends on the
patient's **response** (points/blinks to the moving finger).

### 4 · Facial Palsy — range 0–3
**Instructions:** Ask (or pantomime) the patient to **show teeth, raise eyebrows, and close eyes**.
In poorly responsive patients, score **symmetry of grimace** to noxious stimuli.

| Score | Definition |
|---|---|
| 0 | Normal symmetrical movements. |
| 1 | Minor paralysis (flattened nasolabial fold, asymmetry on smiling). |
| 2 | Partial paralysis (total or near-total paralysis of lower face). |
| 3 | Complete paralysis of one or both sides (no facial movement, upper and lower face). |

*MedBridge capture:* **VISUAL / observable** — asymmetry is judged **during smile/eyebrow-raise** →
baseline→active key frames (~5). A demo showcase item.

### 5 · Motor Arm — range 0–4 (+ UN) · **scored per arm: 5a Left, 5b Right**
**Instructions:** Extend the arms **palms down, 90° (sitting) or 45° (supine)**. **Drift is scored if
the arm falls before 10 seconds.** Encourage the aphasic patient with urgency/pantomime (no noxious
stimulation). **Test each arm in turn, beginning with the non-paretic arm.** UN only for amputation
or shoulder joint fusion (write the explanation).

| Score | Definition |
|---|---|
| 0 | No drift; limb holds 90° (or 45°) for the full 10 seconds. |
| 1 | Drift; limb holds 90° (or 45°) but drifts down before 10 s; **does not hit bed** or other support. |
| 2 | Some effort against gravity; limb can't reach/maintain 90° (or 45°), **drifts down to bed**, but has some effort against gravity. |
| 3 | No effort against gravity; limb **falls**. |
| 4 | No movement. |
| UN | Amputation or joint fusion (explain). |

*MedBridge capture:* **VISUAL / observable, pose-recommended** — drift is a **downward wrist
trajectory over the 10 s hold**; the **1 vs 2** boundary hinges on **bed contact**. Dense ordered
frames + (target) quantitative pose. This is the canonical temporal item. **5a = Left, 5b = Right.**

### 6 · Motor Leg — range 0–4 (+ UN) · **scored per leg: 6a Left, 6b Right**
**Instructions:** Hold the leg at **30° (always supine)**. **Drift is scored if the leg falls before
5 seconds.** Begin with the non-paretic leg. UN only for amputation or hip joint fusion.

| Score | Definition |
|---|---|
| 0 | No drift; leg holds 30° for the full 5 seconds. |
| 1 | Drift; leg falls by the end of the 5-second period but **does not hit the bed**. |
| 2 | Some effort against gravity; leg **falls to bed** by 5 s but has some effort against gravity. |
| 3 | No effort against gravity; leg **falls to bed immediately**. |
| 4 | No movement. |
| UN | Amputation or joint fusion (explain). |

*MedBridge capture:* **VISUAL / observable, pose-recommended** — same drift-vs-bed-contact logic as
the arm, over a **5 s** hold. **6a = Left, 6b = Right.**

### 7 · Limb Ataxia — range 0–2 (+ UN)
**Instructions:** Look for a **unilateral cerebellar lesion**. Eyes open. **Finger-nose-finger** and
**heel-shin** on both sides; score ataxia **only if out of proportion to weakness**. Ataxia is
**absent** in a patient who cannot understand or is paralyzed.

| Score | Definition |
|---|---|
| 0 | Absent. |
| 1 | Present in one limb. |
| 2 | Present in two limbs. |
| UN | Amputation or joint fusion (explain). |

*MedBridge capture:* **VISUAL / observable** — coordination during finger-nose/heel-shin is visible,
but **fine dysmetria is hard at 320×240** → flag lower confidence rather than over-reading.

### 8 · Sensory — range 0–2
**Instructions:** Sensation/grimace to **pinprick** (or withdrawal from noxious stimulus in the
obtunded/aphasic patient). Score **2** only for a clearly demonstrable severe/total loss.
**Coma (1a = 3) → automatically 2.**

| Score | Definition |
|---|---|
| 0 | Normal; no sensory loss. |
| 1 | Mild-to-moderate; pinprick less sharp/dull on affected side, or loss of superficial pain but aware of being touched. |
| 2 | Severe or total; not aware of being touched in face, arm, and leg. |

*MedBridge capture:* **CONTACT / NOT ASSESSABLE FROM VIDEO** — grades a **subjective pinprick
sensation** no camera captures. **Emit "requires clinician" / insufficient_evidence — never guess.**

### 9 · Best Language — range 0–3
**Instructions:** Have the patient **describe the picture** (p. 10), **name items** on the naming
sheet (p. 11), and **read the sentences** (p. 12). Judge comprehension from these plus prior commands.
**Coma (1a = 3) → automatically 3.** Score **3 only** if mute **and** follows no one-step commands.

| Score | Definition |
|---|---|
| 0 | No aphasia; normal. |
| 1 | Mild-to-moderate aphasia; some loss of fluency/comprehension, but ideas still identifiable (examiner can identify picture/naming content from the response). |
| 2 | Severe aphasia; fragmentary expression, listener carries the burden; examiner cannot identify provided materials from the response. |
| 3 | Mute, global aphasia; no usable speech or auditory comprehension. |

*MedBridge capture:* **AUDIO / observable** — naming/reading/description graded from the **transcript**
(the reference materials below are the ground-truth targets). **0 frames.**

### 10 · Dysarthria — range 0–2 (+ UN)
**Instructions:** Obtain an adequate speech sample by having the patient **read/repeat the word list**
(p. 13); if severely aphasic, rate spontaneous articulation. **Do not tell the patient why they are
being tested.** UN only for intubation / physical barrier.

| Score | Definition |
|---|---|
| 0 | Normal. |
| 1 | Mild-to-moderate; slurs at least some words, understandable with some difficulty at worst. |
| 2 | Severe; speech so slurred as to be unintelligible (out of proportion to any dysphasia), or mute/anarthric. |
| UN | Intubated or other physical barrier (explain). |

*MedBridge capture:* **AUDIO / observable** — slurring graded from **audio**. **0 frames.**

### 11 · Extinction and Inattention (formerly Neglect) — range 0–2
**Instructions:** Information may already be gathered during prior testing. If severe visual loss
prevents visual double-simultaneous stimulation but cutaneous stimuli are normal → normal. Aphasic
patient who attends to both sides → normal. **Never untestable** (scored only if present).

| Score | Definition |
|---|---|
| 0 | No abnormality. |
| 1 | Inattention (visual/tactile/auditory/spatial/personal), or extinction to bilateral simultaneous stimulation in one modality. |
| 2 | Profound hemi-inattention or extinction to >1 modality; doesn't recognize own hand, or orients to only one side of space. |

*MedBridge capture:* **MIXED / partial** — depends on the patient's **report** of which side(s) were
touched, not just the maneuver.

---

## Score summary

| Item | Name | Range | Per-limb | MedBridge modality / observability |
|---|---|---|---|---|
| 1a | Level of Consciousness | 0–3 | — | mixed / observable |
| 1b | LOC Questions | 0–2 | — | audio / observable |
| 1c | LOC Commands | 0–2 | — | visual / partial |
| 2 | Best Gaze | 0–2 | — | visual / observable |
| 3 | Visual Fields | 0–3 | — | mixed / partial |
| 4 | Facial Palsy | 0–3 | — | visual / observable |
| 5 | Motor Arm | 0–4 (+UN) | 5a L, 5b R | visual / observable · pose |
| 6 | Motor Leg | 0–4 (+UN) | 6a L, 6b R | visual / observable · pose |
| 7 | Limb Ataxia | 0–2 (+UN) | — | visual / observable |
| 8 | Sensory | 0–2 | — | **contact / NOT assessable** |
| 9 | Best Language | 0–3 | — | audio / observable |
| 10 | Dysarthria | 0–2 (+UN) | — | audio / observable |
| 11 | Extinction/Inattention | 0–2 | — | mixed / partial |

**Total NIHSS** = sum of item scores (per-limb items summed across both limbs). UN entries are not
summed as a number. Typical severity bands (context only, not part of the raw scale): 0 none · 1–4
minor · 5–15 moderate · 16–20 moderate–severe · 21–42 severe.

---

## Test materials (PDF pp. 10–13) — ground-truth targets for items 9 & 10

**Picture description (p. 10, © Apex Innovations)** — the "kitchen/hallway accident" scene: a boy on a
tipping stepladder reaching up with a paint roller; an overflowing bucket; a dog running with a paw
print trail; a mouse; a spider on a web; a framed picture; a side table; a pet bed; a car crashed
through a window in the background.

**Naming sheet (p. 11):** bucket · bicycle · cloud · traffic light · leaf · mouse · bridge.

**Reading sentences (p. 12):**
- You know how.
- Down to earth.
- I got home from work.
- Near the table in the dining room.
- They heard him speak on the radio last night.

**Dysarthria word list (p. 13):** MAMA · TIP-TOP · FIFTY-FIFTY · THANKS · HUCKLEBERRY ·
BASEBALL PLAYER · CATERPILLAR.

*(These are exactly the items the examiner elicits in the NINDS videos — the transcripts in the gold
manifest contain the patient repeating/naming them, which is what the Listener stage scores against.)*
