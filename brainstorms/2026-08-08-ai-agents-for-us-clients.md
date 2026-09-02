# AI Agents for US Clients: Brainstorm / Discovery Notes

Date: 2026-08-08 · Goal: Identify 5 AI agents Roshan should build with Claude Code and sell to US small businesses — grounded in his real constraints. Also identify which Claude Code skills matter most for building them.

## Context going in

- Roshan is India-based, no coding background, learning by building.
- Wants to sell to US clients — "they pay more and I can make good money."
- Wants agents that solve a real pain point, save time, create value for business owners.
- Token budget: 4 hours until quota reset. Running on Haiku 4.5 (efficient but less capable than Sonnet).
- Deliverables: 5 agent recommendations (what, how they work, how to build, problem solved, pricing), and important Claude Code skills.
- Repo `Building agents` is set up with CLAUDE.md, .gitignore, git init. No agents built yet.

## Summary / key decisions

_(running synthesis — updated after every Q&A checkpoint)_

## Q&A log

### Q1 — How will you actually reach US clients?
- Asked: What's the route to US buyers — existing domain knowledge, or a network you can sell into?
- Captured: **Not yet known — but a strong lead exists.** Roshan has a childhood friend who has been freelancing to US clients for the past 4 years. Meeting him **this evening (2026-08-08)**. In Roshan's words: "he will teach me everything today in the evening and guide me through the whole path: how to do it, crack it, and sell to US clients."
- Implication: The distribution answer is deferred by ~hours, not unknown indefinitely. This is a high-value input — 4 years of real US-client experience beats any market report. Recommendations should stay flexible until his input lands.
- Flags: **Distribution strategy / how to land US clients -> the friend, tonight.** Roshan should come to that meeting with specific questions (Claude to draft a question list).

### Q2 — Domain knowledge / background
- Asked: What do you actually know deeply — work, industries, hobbies? And what does your friend do for US clients?
- Captured:
  - **Roshan: 4 years reselling Jordans and Yeezys.** Part-time also **resells concert tickets.**
  - Never held a job. Zero involvement/knowledge of the family business.
  - **Friend: 5 years in digital marketing.** Was a project manager, now **VP at a company.** Sells a mix — "sometimes sells websites, sometimes sells AI agents, sometimes sells other things."
- Claude's read (corrected from a wrong prior assumption that Roshan had no domain knowledge):
  - Sneaker/streetwear resale and ticket resale are **US-centric markets**. Roshan has 4 years of lived experience inside US consumer demand — hype cycles, drop timing, pricing, platform mechanics (StockX / GOAT / eBay / StubHub / SeatGeek).
  - Reselling **is sales**: sourcing, pricing, negotiating, closing. This is the skill most technical builders lack, and Roshan already has it.
  - Real candidate niche: **build for resellers** (a market he understands and can speak the language of) rather than generic SMBs.
  - Friend's profile is valuable beyond intros — a digital-marketing VP knows agency pain points AND is a potential **channel partner** (he already sells AI agents to clients; Roshan could build what he sells).
- Flags: Decide whether to target the known niche (resellers) or generic US SMBs -> **Roshan, after tonight's meeting**

### Q3 — Capacity: time, money, urgency
- Asked: Hours/week, money you can spend before earning, and how urgently you need income?
- Captured:
  - **Time: 3–5 hours every day** (~21–35 hrs/week). Time is NOT the constraint.
  - **Money: wants to spend nothing.** In his words: "I just want to make money first and then reinvest. But still, if required, lowest to lowest money spend."
  - **Urgency: high but not deadline-driven.** Wants to compress the cycle — "if I make the AI agent in one week and sell it the next week by cracking a client, I'll do that." Target rhythm: build in ~1 week, close a client in ~1 month.
- Claude's correction to Roshan: **zero spend is not achievable.** Realistic floor:
  - ~**$5–15 one-time** in API calls to build and test an agent (hundreds of test runs).
  - Hosting genuinely **$0** on free tiers.
  - **Structural fix for ongoing cost: client brings their own API key.** Client creates their own account and pays their own usage. Roshan never fronts running costs and isn't liable for bill spikes. **All 5 agent recommendations must be designed this way.**
  - Net: **~$10–20 once, then near-zero.**
- Flags: Confirm Roshan can spend ~$10–20 one-time -> **Roshan**

### Q4 — What are you actually selling? (pricing model)
- Asked: One-time fee (A), monthly subscription (B), or setup fee + monthly (C)?
- Captured: Roshan's answer — **"for the start option A is good but long term option B."** Wants one-time fees now for fast cash, subscriptions later.
- Claude's pushback (important, unresolved):
  - **A does not naturally convert into B.** Once the client owns the code, they stop paying; you can't retroactively charge monthly. You'd be restarting the subscription business from scratch later, not graduating into it.
  - **Recommended bridge:** charge the one-time fee as Roshan wants, but **do NOT hand over the code — keep it hosted on Roshan's setup.** Frame it as "setup fee includes first 30 days, then $X/month to keep it live." Same fast cash, but the recurring door stays open. Costs nothing extra since hosting is free-tier.
  - Secondary issue: clients are non-technical, so "here's the code, run it yourself" tends to fail in practice and generates unpaid support work.
- Flags: Confirm — pure one-time handover, or one-time fee with Roshan hosting? -> **Roshan**

### Q5 — Who is the buyer?
- Asked: Resellers (known niche), generic US SMBs (cold outreach), or friend's clients (channel partner)?
- Captured: **DECIDED — generic US small businesses via cold outreach from India.** Roshan's words: "I want to sell to generic U.S. small businesses, dentists, plumbers, gyms, salons, law firms." Target pains he named: **missed calls, unanswered leads, no-show appointments, review replies.**
- **Correction to Claude's earlier assumption:** the friend is **NOT a sales channel.** Roshan: "my friend's clients are not going to sell my agents to people. He is only going to help me understand the process of cold outreach from India as he does that." Friend's role = **mentor/teacher on cold outreach, closing, and selling to foreigners.** Do not build plans that depend on the friend supplying clients.
- Roshan explicitly acknowledged the access problem and accepted it: "I know I have no access to them. I will cold outreach to them from India."
- Status: Claude raised the cold-outreach-from-India difficulty in Q5; Roshan reaffirmed deliberately, with a mentor who does this professionally. **Decision stands — proceed, do not re-litigate.**
- Flags: Pick a single starting vertical vs spraying across all five -> **Q6**

### Q6 — Which single vertical to start with?
- Asked: Pick one vertical (recommended: home services — plumbers/HVAC/roofers/electricians) rather than spraying across five?
- Captured: **DEFERRED to the friend.** Roshan: "The vertical which I will particularly focus on will be told to me by my friend in the evening. When he teaches me the whole process."
- Claude's recommendation on record (for Roshan to sanity-check against the friend's advice): **home services first.** Rationale:
  - Pain is measurable in dollars — one missed call = a $300–$5,000 job lost to the next plumber on Google.
  - Owner answers the phone; no gatekeeper, single decision-maker.
  - Low tech sophistication, no entrenched competitor tools.
  - **No compliance minefield.** Dentists = HIPAA; law firms = confidentiality rules. Real legal exposure, bad place for a beginner. Do these LAST.
  - Gyms/salons: same pains but $30–80 per booking vs $500+, so a much weaker ROI story and harder to price.
- **Design consequence:** since the vertical is TBD, the 5 agents must be **vertical-agnostic** — same core product, only the pitch wording changes per industry. Do not hard-code industry assumptions.
- Flags: Final vertical choice -> **friend, tonight**. Roshan to compare friend's pick against the HIPAA/ticket-size reasoning above.

### Q7 — Will you do live sales calls with US business owners?
- Asked: Video/Zoom calls (higher ticket, odd hours) vs text/email/Loom only (lower ticket, higher volume)? Plus honesty about spoken English.
- Captured: **YES to calls.** Roshan: "I'm okay with late-night calls as long as I'm earning good money in dollars. I'll keep myself awake." On English: "I don't have the American accent, but I am pretty good at talking in English."
- Consequence: **Higher price points are on the table ($500–2,000+ rather than $100–400).** Sales motion = live conversation, not self-serve. Demo must be presentable live on a call.
- Note: US Eastern business hours ≈ **6:30pm–3:30am IST**. Roshan has accepted this.
- Claude's note: accent is not a real barrier — clarity, confidence and knowing the numbers matter far more. Do not attempt to fake an American accent.
- Flags: Video-on vs audio-only not explicitly confirmed -> **Roshan** (minor; recommend video-on, it builds trust faster)

### Q8 — Credibility and payment infrastructure
- Asked: Domain/professional email, web presence, USD payment rail, Claude Code plan?
- Captured:
  - **Domain + pro email: NO.** Roshan believed he needed a registered company first — **Claude corrected this: you do NOT need a company to buy a domain or create a professional email.** You're buying a name, not registering a business.
  - **Portfolio site: none, willing to build one.** Roshan's own reasoning: "Before selling, obviously, I will put up the agents there." Correct instinct.
  - **LinkedIn: exists but thin** — lists one company, school, college.
  - **USD payment: via parents' account.** No personal account in his own name.
  - **Claude Code plan: PRO.**
- Claude's guidance:
  - **Domain (~$12/yr) = highest-ROI spend available. Non-negotiable before outreach.** Gmail→US business cold email gets filtered/ignored; a domain gets read. First claim on budget.
  - **Portfolio site: defer.** Don't block outreach on it. Build one simple free page (GitHub Pages / Carrd free tier) AFTER agent #1 exists.
  - **Payment: caution.** Business income landing in a parent's name has Indian tax + FEMA implications and gets messy as amounts grow. OK for the first payment or two, NOT a permanent setup. **Consult a CA once money starts flowing.** Claude explicitly declined to give tax advice.
  - **Pro plan: build on Sonnet, reserve Opus for hard debugging.** Roshan already hit limits once on 08/08/2026.
- Flags:
  - Buy domain + set up professional email -> **Roshan, before first outreach**
  - Payment setup — ask what he uses after 4 years of US income -> **friend, tonight**
  - Proper payment structure + tax treatment -> **a CA, once revenue starts**
  - Minor inconsistency: Roshan said he's never had a job, but LinkedIn lists one company -> **Roshan to clarify** (affects positioning)

### Q9 — Completeness backstop
- Asked: Anything untouched? Plus confirmation of assumptions (built nothing, no US contacts, working alone, no preference on which pain to attack first).
- Captured:
  - **Job history clarified:** never had a full-time job, but **did a 3-month internship**, which is what appears on LinkedIn. Resolves the earlier inconsistency.
  - **KEY CONCERN RAISED — fear of the work outside Claude Code.** In his words: *"I am just scared that there are things which are required for me to do outside of Claude Code as well when building the agent. I don't know things outside Claude Code, so I am just scared. I hope that Claude Code tells me the whole process in detail, including everything that is to be done outside Claude Code as well. I need to know the whole process."*
  - Roshan gave the green light to begin research.
- Claude's response and **binding commitment for the deliverable**:
  - Confirmed the fear is well-founded — real agent-building involves substantial non-coding work: creating accounts, obtaining API keys, buying phone numbers, connecting calendars/CRMs, configuring webhooks, deploying, DNS.
  - **Every agent recommendation MUST include an explicit "outside Claude Code" section**: which website, which button, what it costs, what to copy where. This is the step most tutorials omit and the most common place beginners stall.
  - Assume **zero terminal experience** and **zero prior account setup**. Nothing may be left implicit.

## Open flags (pending input)

- Starting vertical -> **friend, tonight** (Claude recommends home services; flag HIPAA risk if friend suggests dentists, and low ticket size if he suggests gyms/salons)
- Cold outreach method — channel (email/LinkedIn/cold call/Loom), tooling, volume, scripts -> **friend, meeting tonight 08/08/2026**
- Payment mechanics — how to receive USD from India (Stripe/Payoneer/Wise/direct) -> **friend, tonight**
- Realistic pricing — what US clients actually pay a solo India-based operator -> **friend, tonight**
- Trust/credibility — how he overcomes the "stranger overseas" objection -> **friend, tonight**
