# Hackathon Guidance — Abridge "Build Agents for Healthcare"

Authoritative working guide for how MedBridge competes: the mandate, the **rules that can
disqualify us**, the **provided resources**, and the **official judging rubric** — plus the
strategic implications for our build. Logistics (venue/address/schedule) omitted on purpose.

---

## 1. The mandate

- Build an **agentic** system for **one** clinical **or operational** healthcare workflow that
  makes it **faster, smarter, or safer** (guide links Anthropic's *Building Effective Agents*).
- **Real-world clinical impact — "saving time or lives."**
- **Ship something a clinician or patient-facing team could use on Monday.**
- Framing: *"$4 trillion industry running on fax machines and burnt-out clinicians."* → the pain
  is **clinician burden and broken operational workflows.**
- Given examples: **clinical-trial matching**, **prior-authorization eligibility from payor
  policies** — both **operational/administrative**, patient-context-driven.
- **Abridge engineers *and clinicians* pressure-test on the floor all day** — use them.

## 2. Rules & compliance (get these wrong = disqualification)

| Rule | Requirement | MedBridge action / flag |
|---|---|---|
| **Open source** | Repo **must be public** | ✅ `github.com/csbrendan/the-agent-will-see-you-now` is already public |
| **Team size** | **Max 2** (solo allowed) | Confirm team ≤ 2 |
| **Demo = only what you built *during* the event** | Judges must clearly identify what was created **at the hackathon**. Unclear provenance = **immediate DQ** | 🔴 **Critical.** All current repo work (ProjectPlan, READMEs, dataset setup, smoke tests) is **pre-event scaffolding**, NOT hackathon output. The **product code must be built during the event**, and the demo/video must clearly delineate hackathon-built work. Treat existing files as environment, not as the deliverable to claim. |
| **New work only** | May not present an existing project as your own | 🔴 Do **not** pitch "MedBridge" as if the pre-built plan is the hackathon build. Frame the hackathon as building *the working agent* on event day. |
| **Rights to code/data/assets** | DQ if you use assets you don't have rights to | ✅ **NINDS NIHSS videos are CC0 public domain** (Internet Archive) — the best possible rights posture, no attribution/commercial constraints. It is the only dataset MedBridge uses. |

### 🚫 Anti-projects — STRICTLY NO (auto-risk of DQ / poor scoring)

- AI Mental Health Advisor *(basic chatbots only)*
- Basic RAG Applications
- **Streamlit Applications** ⚠️
- **Image Analyzers** *(basic / limited technical complexity only)* ⚠️
- "AI for Education" Chatbot · AI Job Application Screener · AI Nutrition Coach *(basic)* ·
  Personality Analyzers
- **Any project where a dashboard is the main feature** ⚠️
- **Sports analyzers or coaches** ⚠️

> **These directly threaten our default direction — read carefully:**
> - **Streamlit** is named. Our stack defaulted to Streamlit. → Streamlit must **not** be the
>   "main feature"; the **agentic architecture** must be unmistakably the substance. Consider a
>   non-Streamlit frontend, or keep UI minimal and make the agents the star.
> - **"Image Analyzers"** is named. Our defense is unambiguous: MedBridge is an **audiovisual +
>   temporal, multi-agent, safety-verified clinical agent** on a real neurological exam — categorically
>   not a "basic image analyzer." Make the independent Safety Verifier + evidence-grounding the visible
>   substance, not the perception call. *(We dropped the earlier gait/rehab direction, which
>   pattern-matched to the "image analyzer" + "sports coach" traps.)*
> - **Dashboard** must not be the centerpiece.

## 3. Provided resources

- **Abridge datasets (strong signal — use if possible):** anonymized **patient encounters + EHR
  entries + associated FHIR data**, with spec, provided as a `.zip`. Using the **sponsor's own
  rights-clean clinical data** on an **operational workflow** aligns with the prompt's examples
  (prior-auth, trial matching), sidesteps every anti-project trap, and reads as "built for this
  hackathon." **This is the safest, best-fit data substrate.**
- **Anthropic:** **$100 Claude API credits** (claim per provided instructions) + the *Building
  Effective Agents* guide.

## 4. Submission requirements

- Submit on the Cerebral Valley event page when done.
- **1-minute demo video** highlighting **only what the team built during the hackathon**.
- Repo **public**, demo link accessible, **all team members added** to the submission.

## 5. Judging — the official rubric

**Two rounds, ~3-min live demo + 1–2 min Q&A each.**

**Round One** (weighted):

| Criterion | Weight | What judges reward |
|---|---:|---|
| **Execution** | **30%** | Complete, polished, **working**; thoughtfully built; **clearly demoed live**. *"A focused, finished build beats an ambitious but broken one."* |
| **Creativity & Originality** | **25%** | Novel, unseen approach; fresh thinking; tackled it in a way no one else did |
| **Impact** | **20%** | Clear real user pain **at scale**; matters to clinicians/patients/care teams; moves the needle for **many**; lasting beyond the hackathon |
| **Technical Complexity** | **20%** | Technically ambitious, well-engineered; hard problem with depth; thoughtful architecture, clever use of models/data, engineering rigor |

*(Weights as published sum to 95%.)*

**Round Two:** top **six** teams demo on stage to the full panel + attendees. **Same criteria,
equal weighting (~25% each).**

## 5b. Judges' idea-evaluation framework (VALUE · SUITABILITY · FEASIBILITY)

The judges additionally shared this framework for evaluating high-impact agentic-AI ideas — design
toward it, and address it directly in the pitch.

**VALUE** — *dictates speed & desire for adoption*
- **Repeatable** — automates consistent tasks done over and over
- **ROI** — targets dollar- or time-consuming pain points, making the effort worth it
- **Logic-based** — built-in logic vs. emotional / empathetic

**SUITABILITY** — *dictates long-term moats & "unlocks" via AI*
- **Data Structure** — unlocks a high degree of **unstructured** data
- **Data Availability** — unifies data assets across multiple sources
- **Data Durability** — owns **proprietary** data at scale

**FEASIBILITY** — *dictates ability for the solution to work*
- **Technology** — pain points models are technically capable of solving **today**
- **Trust & safety** — fits within compliance / regulatory requirements
- **Integration** — requires some level of forward deployment / engineering

### MedBridge mapped against it (with honest soft spots)

| Pillar | Criterion | MedBridge |
|---|---|---|
| **VALUE** | Repeatable | ✅✅ NIHSS is a standardized exam repeated constantly in EDs / stroke units / tele-neuro |
| | ROI | ✅✅ "Time is brain" — faster, consistent screening + triage; offloads repeated exams; missed/delayed stroke is enormously costly |
| | Logic-based | ✅✅ NIHSS **is** a structured scoring rubric — logic-based, not empathetic |
| **SUITABILITY** | Data Structure | ✅✅ Core unlock: turns an **unstructured audiovisual exam** into structured, source-attributed findings |
| | Data Availability | ✅ Unifies exam video + agent scoring + chart documentation into one record across the care team (frames + audio; extensible to EHR/FHIR) |
| | Data Durability | ⚠️→✅ We use public NINDS today (**no proprietary moat yet**), but the glasses/ambient framing gives a real durability story: a deployed product accrues **proprietary paired exam-video + ground-truth-score data at scale** — a defensible moat. Near-term moat is still the **architecture + safety layer** |
| **FEASIBILITY** | Technology | ⚠️/✅ Multimodal vision+audio is solvable today; fine-grained NIHSS **scoring** from low-res video is not fully — hence **screening support, not autonomous scoring**. Public NINDS footage supplies gold-labeled ground truth |
| | Trust & safety | ✅✅ **Strongest axis** — the physician stays the accountable decision-maker (assistive, not autonomous); the independent Safety Verifier + escalate-to-human + **remote-neurologist validation** **is** the compliance/trust story; consent/PHI handling is first-class |
| | Integration | ✅ Deployable into tele-stroke / bedside triage as a "co-clinician that escalates to a human"; the sticky surface is **forward-deployed glasses capture + EHR write-back** |

> **Product framing that strengthens this mapping (from clinician/MD advice — see [concept.md](concept.md)):**
> *the glasses see the exam, so nothing has to be spoken aloud to be captured.* A clinician wears the
> glasses and performs the NIHSS normally; the agent scores it immediately (a standardized score ready
> before the stroke team arrives) and an off-site neurologist can remotely **"pass" the exam** against
> the captured video. NIHSS is the beachhead; the platform play is **visual ambient documentation of
> the physical exam** — "document what you see, not what you say" — which is where audio-only ambient
> scribes fall short. *(Hackathon build runs on pre-recorded NINDS video, not live glasses.)*

**Pitch implications:**
- **Lead with VALUE (all three strong) + Trust & Safety** — these are MedBridge's standout columns
  and map onto the official **Impact** and **Creativity** criteria.
- **Pre-empt the two soft spots honestly:** *Data Durability* (near-term moat is the architecture/
  safety layer; the proprietary paired video+score data moat accrues on deployment) and *Technology*
  (framed as **screening support with human escalation**, not autonomous scoring — the Safety Verifier
  is exactly what makes the technology limit safe).

## 6. How this rubric should steer MedBridge

**Execution is the single biggest lever (30%), and the rubric explicitly prefers a focused,
finished build over an ambitious broken one.** This is the decisive strategic input:

1. **Scope ruthlessly small and finish it.** One workflow, one clean end-to-end path, a demo
   that *works live*. Kill the emergency-moonshot temptation — ambitious-but-broken loses.
2. **Lead with the differentiator for Creativity (25%) + Technical (20%):** the **independent
   Safety Verifier** catching/correcting unsafe or unsupported AI output and **escalating to a
   human**. That multi-agent, evidence-grounded safety layer is *not* a "basic image analyzer"
   or "basic RAG" — it is the originality + technical-depth story. Make it the centerpiece.
3. **Impact (20%) wants scale + real users.** Frame the workflow around a pain that hits *many*
   clinicians/patients (documentation burden, prior-auth, triage, care-gap closure), not a
   niche.
4. **Data choice matters for rights + fit:** we use the **CC0 public-domain NINDS NIHSS videos** —
   rights-clean, the exact clinical workflow, and gold-labeled. Extensible to Abridge FHIR/EHR for
   chart write-back. The defense against the image-analyzer trap is the audiovisual + temporal,
   multi-agent, safety-verified framing (not the perception call in isolation).
5. **Provenance discipline:** build the *product* during the event; the current repo is
   scaffolding. The 1-minute video and live demo must clearly show hackathon-built work.
6. **Talk to Abridge clinicians early** to sharpen the workflow and pre-empt the deployability /
   liability questions in Q&A.

## 7. Direction — decided

**Resolved: a tightly scoped clinical workflow — audiovisual NIHSS stroke screening for clinical
use.** MedBridge is an **ambient visual documentation** co-clinician: a clinician (nurse, resident,
attending) performs the NIHSS exam normally while the agent observes, scores, and documents from what
it sees — *"document what you see, not what you say"* (full framing in [concept.md](concept.md)). The
earlier multimodal-gait direction is **dropped** (it pattern-matched the image-analyzer + sports-coach
traps and carried a CC-BY-NC license); we use the **CC0 NINDS NIHSS videos** only.

**The safety-verification architecture is the moat regardless of substrate**, and it stays the
centerpiece: the independent Safety Verifier catching unsupported "normal" claims and escalating to a
human. NIHSS is the beachhead; the platform play is visual ambient documentation of the wider physical
exam, extensible to Abridge FHIR/EHR for chart write-back. *(Hackathon build runs on pre-recorded
NINDS video; smart-glasses capture is the productization path, not a demo claim.)*
