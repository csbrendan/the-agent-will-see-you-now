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
| **Open source** | Repo **must be public** | ✅ `github.com/csbrendan/MedBridge` is already public |
| **Team size** | **Max 2** (solo allowed) | Confirm team ≤ 2 |
| **Demo = only what you built *during* the event** | Judges must clearly identify what was created **at the hackathon**. Unclear provenance = **immediate DQ** | 🔴 **Critical.** All current repo work (ProjectPlan, READMEs, dataset setup, smoke tests) is **pre-event scaffolding**, NOT hackathon output. The **product code must be built during the event**, and the demo/video must clearly delineate hackathon-built work. Treat existing files as environment, not as the deliverable to claim. |
| **New work only** | May not present an existing project as your own | 🔴 Do **not** pitch "MedBridge" as if the pre-built plan is the hackathon build. Frame the hackathon as building *the working agent* on event day. |
| **Rights to code/data/assets** | DQ if you use assets you don't have rights to | ⚠️ **ProGait is CC-BY-NC-SA-4.0** (non-commercial, attribution, share-alike). OK for a research/non-commercial demo *with attribution*, but must be cited and not commercialized. **Abridge's provided data (below) is the rights-clean, sponsor-blessed option.** |

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
> - **"Image Analyzers"** and **"Sports coaches"** are named. A **gait / exercise-form video
>   coach pattern-matches to BOTH** ("basic image analyzer" + "sports/exercise coach"). The
>   multimodal-rehab pivot is **risky** unless it is clearly a *safety-verified clinical agent
>   system*, not "an app that watches you exercise." This is a real reason to reconsider the
>   video direction vs. an operational-data agent.
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
| | Data Availability | ✅ Fuses multiple sources (frames + audio; extensible to EHR/FHIR) |
| | Data Durability | ⚠️ We use public NINDS — **no proprietary-data moat today**. A deployed product accrues proprietary exam data over time; the near-term moat is the **architecture + safety layer**, not owned data |
| **FEASIBILITY** | Technology | ⚠️/✅ Multimodal vision+audio is solvable today; fine-grained NIHSS **scoring** from low-res video is not fully — hence **screening support, not autonomous scoring** |
| | Trust & safety | ✅✅ **Strongest axis** — the independent Safety Verifier + escalate-to-human **is** the compliance/trust story; never autonomous diagnosis |
| | Integration | ✅ Deployable into tele-stroke / bedside triage as a "co-clinician that escalates to a human"; modest forward deployment |

**Pitch implications:**
- **Lead with VALUE (all three strong) + Trust & Safety** — these are MedBridge's standout columns
  and map onto the official **Impact** and **Creativity** criteria.
- **Pre-empt the two soft spots honestly:** *Data Durability* (moat is the architecture/safety layer
  now; proprietary data accrues on deployment) and *Technology* (framed as **screening support with
  human escalation**, not autonomous scoring — the Safety Verifier is exactly what makes the
  technology limit safe).

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
4. **Data choice matters for rights + fit:** strongly consider the **Abridge FHIR/EHR encounter
   data** — rights-clean, sponsor-aligned, operational, and it dodges the Streamlit/image-
   analyzer/sports-coach anti-project traps that the video/gait direction risks.
5. **Provenance discipline:** build the *product* during the event; the current repo is
   scaffolding. The 1-minute video and live demo must clearly show hackathon-built work.
6. **Talk to Abridge clinicians early** to sharpen the workflow and pre-empt the deployability /
   liability questions in Q&A.

## 7. Open strategic question this raises

The rules meaningfully **reweight our earlier plan.** The multimodal-video / ProGait-gait
direction now carries real anti-project risk (**image-analyzer + sports-coach adjacency**,
Streamlit trap, CC-BY-NC license) and a steep Execution bar. Meanwhile Abridge hands us
**rights-clean FHIR/EHR data** pointing straight at the operational examples the prompt names.

**The safety-verification architecture is the moat regardless of substrate.** The decision to
make: apply it to (a) an **operational agent on Abridge's FHIR/EHR data** (prior-auth, referral/
care-gap, encounter-to-action) — safest fit, best Execution/Impact odds; or (b) a **tightly
scoped clinical workflow** that keeps a multimodal element but is clearly a *safety-verified
agent system*, not an "image analyzer/coach." Decide this before building.
