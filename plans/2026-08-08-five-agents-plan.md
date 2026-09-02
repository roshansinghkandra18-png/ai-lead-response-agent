# The Plan: 5 Agents to Build and Sell to US Small Businesses

Date: 2026-08-08 · For: Roshan · Source interview: `brainstorms/2026-08-08-ai-agents-for-us-clients.md`

---

## PART 1 — What the research actually says (read this first)

Four findings. Two of them are bad news, and you need them before you build anything.

### Finding 1: The obvious agents are already commoditised

"AI receptionist" and "missed call text-back" — the first ideas everyone has — are **finished markets**. Off-the-shelf products already do this:

| Product | Price |
|---|---|
| AIRA | $24.95/mo |
| Dialzara | $29/mo (60 mins) → $349/mo (1,000 mins) |
| Trillet | $49/mo |
| NextPhone | $199/mo unlimited |
| SupaBook | $0 + $0.15/min |

**What this means for you:** you cannot cold-call a plumber and charge $1,500 for an AI receptionist. He googles it, finds Dialzara at $29/month, and you look like a fraud. Any agent you sell must be something these products **do not** do.

This is the single most important finding. Most "sell AI agents" advice on YouTube ignores it.

### Finding 2: The $2,000–5,000/month retainer numbers are marketing

Search results claim AI automation agencies charge $1,000–$5,000/mo, and up to $7,000 in financial services. **Check who publishes those numbers** — they are agency blogs and course sellers whose business is convincing you to start an agency. Treat them as a ceiling that experienced operators with case studies occasionally reach, not as your starting price.

Your realistic first sale: **$300–$800 one-time.** Plan around that, and be delighted if you beat it.

### Finding 3: Cold outreach maths is brutal — know it before you start

- Generic templated sequences to SMBs: **under 0.8% reply rate**
- B2B average: **1–5%**, and AI-automation pitches sit at the *low* end
- Decision-makers get dozens of AI pitches weekly. 361 billion emails/day.

**Do the maths on yourself:** at a 1% reply rate, 500 emails → 5 replies → maybe 2 calls → maybe 1 client. That is a realistic month of work. If you expected 50 emails to produce a client, adjust now, not in week three when you feel like a failure.

### Finding 4: What still works is proof, not volume

The one consistent signal across every source: agencies still booking calls send **fewer, better-researched** messages with **proof attached** and a message matching **what the owner already suspects is broken**.

That single sentence dictates the whole strategy below.

---

## PART 2 — The strategy this points to

Given: you're unknown, based in India, cold outreaching, with no case studies and ~$20.

**Don't sell "an AI agent." Sell a specific fixed problem, and prove it before you ask for money.**

Concretely: your first build should not be a product you sell. It should be the thing that makes your outreach work — an agent that researches each prospect and produces a **personalised, evidence-backed audit** you attach to the cold email. That directly attacks the 0.8% reply rate problem.

Then you sell the fix for what the audit found.

**The commercial model** (from the interview, with Claude's amendment):
- One-time fee, as you wanted — **but you host it, you do not hand over the code.**
- Client brings their **own API key** so you never carry running costs.
- Framed as: "$X setup, includes first 30 days. $Y/month after to keep it live."

---

## PART 3 — The five agents

Ordered by build order, not by revenue. Every one is **vertical-agnostic** — same product for plumbers, gyms or salons, only the pitch wording changes. Your friend's vertical pick tonight does not invalidate any of these.

---

### AGENT 1 — The Prospect Audit Agent *(build first, never sell)*

**What it is.** You give it a business name and website. It checks their public online presence and produces a one-page PDF: how fast they reply to enquiries, whether their Google listing is complete, how many reviews they have unanswered, whether their contact form works, how they compare to three local competitors.

**The problem it solves — yours, not theirs.** Your reply rate. Instead of "Hi, I build AI agents," you send: *"I noticed 14 of your Google reviews from the last 3 months have no reply, and your contact form didn't send when I tested it. Here's a one-page breakdown."* That is the "proof attached" the research says is the only thing still working.

**Price:** $0. This is a sales weapon, not a product. Free audits are also the single best call-booking offer available to someone with no reputation.

**How to build it (Claude Code):**
1. Input: a list of business names + websites in a CSV
2. Fetch their website, extract phone/email/contact form
3. Look up their Google Business Profile data
4. Have Claude analyse and write findings in plain English
5. Output a simple branded PDF

**Outside Claude Code — what YOU do:**
| Step | Where | Cost |
|---|---|---|
| Get an Anthropic API key | console.anthropic.com → sign up → API keys → Create | ~$5 credit |
| Get a search/scrape API key (SerpAPI free tier or similar) | serpapi.com → sign up | Free tier |
| Build the prospect list | Google Maps, manually or scraped | Free |
| Nothing to deploy — runs on your laptop | — | $0 |

**Build time:** 2–3 days at 3–5 hrs/day. **Start here.**

---

### AGENT 2 — Speed-to-Lead Responder

**What it is.** Watches the business's email inbox for new enquiries (website form, Yelp, Angi, Thumbtack). Within 60 seconds it sends a personalised reply, asks the two qualifying questions the owner cares about, and alerts the owner by SMS/email.

**The problem it solves.** Speed-to-lead is the most provable stat in small business: the business that replies first usually wins the job. A plumber sees an enquiry three hours later, by which time the customer hired someone else. **Every hour of delay is money already lost** — and unlike "AI receptionist," you can prove this one with their own inbox.

**Why it isn't commoditised.** The $29/mo tools handle *phone calls*. Web-form and marketplace leads arriving by **email** are a different pipe, and most cheap tools don't touch it. This is a real gap.

**Price:** $500–800 setup + $150–250/mo. Justify it with their own numbers: "you get ~40 leads/month, you're losing maybe 8 to slow response, each job is $400 — that's $3,200/month."

**How to build it:**
1. Connect to the client's inbox (IMAP — a standard way to read email)
2. Detect new enquiries and extract name, phone, job type
3. Claude drafts a reply in the owner's voice
4. Send reply, log to a Google Sheet, alert the owner
5. Run every 60 seconds

**Outside Claude Code — what YOU do:**
| Step | Where | Cost |
|---|---|---|
| Client creates an Anthropic API key | console.anthropic.com | Client pays (~$5–15/mo) |
| Get an app password for their email | Google Account → Security → App passwords | Free |
| Create a Google Sheet for the log | sheets.google.com | Free |
| Deploy so it runs 24/7 | Railway or Render free tier | $0 |

**Build time:** 4–5 days. **This is your first paid product.**

---

### AGENT 3 — Review Reply Agent

**What it is.** Watches new Google reviews. Drafts a reply in the owner's voice — warm for 5-star, careful and de-escalating for 1-star. Owner approves by replying "yes" to a text; nothing posts without approval.

**The problem it solves.** Unanswered reviews cost real money — Google ranks responsive businesses higher, and an unanswered angry review is the first thing a new customer reads. Owners know they should reply and never do, because writing a calm reply to an unfair 1-star review at 9pm is emotionally the last thing they want to do.

**Why it sells well cold.** It's **visible**. You can show the owner their own unanswered reviews on the call. No imagination required — the pain is on screen.

**Price:** $400–600 setup + $100–200/mo.

**Important warning.** Never let it auto-post. One tone-deaf AI reply to a grieving or furious customer, published publicly under their business name, is a catastrophe you will be blamed for. **Human approval is mandatory** — and it's also a selling point.

**How to build it:**
1. Pull new reviews (Google Business Profile API)
2. Claude drafts a reply matched to the star rating
3. Text the draft to the owner for approval
4. Post only on "yes"

**Outside Claude Code — what YOU do:**
| Step | Where | Cost |
|---|---|---|
| Google Cloud project + enable Business Profile API | console.cloud.google.com | Free |
| **Request API access — this needs Google's approval and can take days/weeks** | Google Business Profile API request form | Free but slow |
| Client grants access to their listing | OAuth consent flow | Free |
| Twilio number for approval texts | twilio.com | ~$1/mo + $0.008/text |
| Deploy | Railway/Render free tier | $0 |

**Build time:** 5–7 days, plus waiting on Google. **Start the API access request early — it's the bottleneck.**

---

### AGENT 4 — Quote & Estimate Drafter

**What it is.** Owner forwards an enquiry (text description, sometimes photos). Agent produces a formatted, branded estimate using the owner's own pricing rules, ready to send in minutes.

**The problem it solves.** This is the one with the least competition and the most genuine pain. Home-service owners write quotes **at night, after a full day of physical work.** It's the job they hate most and the one that delays cash. A two-day delay in sending a quote loses jobs.

**Why it isn't commoditised.** Every business prices differently. That's exactly why big SaaS can't serve it well — and exactly why it's defensible for you. You encode *their* rules.

**Price:** $800–1,500 setup + $200–300/mo. **This is your highest-value agent** because it touches money directly and can't be replaced by a $29 tool.

**The catch — be honest with yourself.** It requires real discovery: you must sit with the owner and extract their pricing logic. That's a 60–90 minute call and they may not have it written down anywhere. Harder to sell cold, much stickier once sold.

**How to build it:**
1. Owner forwards enquiry to a dedicated email address
2. Extract job type, size, location, urgency
3. Apply their pricing rules (stored in a config file you fill in during onboarding)
4. Generate a branded PDF estimate
5. Send back to owner for review and sending

**Outside Claude Code — what YOU do:**
| Step | Where | Cost |
|---|---|---|
| Client's Anthropic API key | console.anthropic.com | Client pays |
| Dedicated inbox for forwarding | Google Workspace or free Gmail | $0–6/mo |
| Their logo + pricing sheet | From the client during onboarding | Free |
| Deploy | Railway/Render free tier | $0 |

**Build time:** 5–7 days. **Sell this second, once you have one happy client.**

---

### AGENT 5 — Review Request Agent

**What it is.** When a job is marked complete, it texts the customer a short, personal review request with a direct link — then follows up once if ignored.

**The problem it solves.** More Google reviews → higher local ranking → more calls. Owners know this and still never ask, because they're finishing a job and moving to the next one. This agent turns "I should ask for reviews" into something that just happens.

**Why it's here.** It's the **easiest to build** and produces a **visible result within two weeks** — review count goes up, and the owner can see it. That makes it a superb *first* paid engagement and a case study generator.

**Price:** $300–500 setup + $75–150/mo. Lower value, but it's the easiest yes.

**Compliance warning — this one is legally real.** Automated SMS to US consumers is regulated (TCPA). Rules include consent, business identification, and honouring STOP. **Get written confirmation from the client that their customers consented to be texted**, and always include opt-out. This is not optional and it is not paranoia — TCPA penalties are per-message.

**How to build it:**
1. Trigger: owner texts/emails "done — [customer name] [number]"
2. Wait a set delay (2–4 hours)
3. Send personalised SMS with their Google review link
4. One follow-up after 3 days if no review appears
5. Stop on STOP

**Outside Claude Code — what YOU do:**
| Step | Where | Cost |
|---|---|---|
| Twilio account + US number | twilio.com | ~$1/mo + $0.008/text |
| **A2P 10DLC registration** — US carriers require business SMS registration | Twilio console, during setup | ~$4 one-time + $2/mo |
| Get the client's Google review link | Their Google Business Profile | Free |
| Deploy | Railway/Render free tier | $0 |

**Build time:** 3–4 days. **A2P registration takes days — start it early.**

---

## PART 4 — Which Claude Code skills actually matter for you

You asked which skills (`/name` commands) matter. Honest answer: **most skill lists online are filler.** These are the ones that will actually change your outcome.

### Already installed and directly relevant

| Skill | Why it matters to you |
|---|---|
| `/grill-me` | What we just used. Use it before every agent build to extract the client's requirements. **Use it on your client during onboarding** — it's a discovery-call weapon. |
| `/session-handoff` (your "karde") | You're on Pro and will hit limits mid-build. This preserves state so a fresh session continues cleanly. **Use it every time you're near a limit.** |
| `/plan-critic` (your own subagent) | Run it against this plan and against every client proposal before you send it. |
| `/run` | Launches and drives your agent so you can *see* it working. Critical for you specifically — you can't read code well yet, so seeing it run is how you verify. |
| `/code-review` | Run before anything touches a client. Catches the errors that would embarrass you. |
| `/security-review` | **Run before every client deployment, without exception.** You're handling their inbox and customer data. |

### Worth learning as you go

| Skill | When |
|---|---|
| `/claude-api` | When you build anything calling Claude — correct model IDs, pricing, token counting. Directly relevant to your "log token usage" rule. |
| `/artifact-design` + `/dataviz` | When you build the audit PDF (Agent 1) and want it to look professional |
| `/update-config` | When you want automatic behaviours, e.g. auto-run security review |
| `/fewer-permission-prompts` | After a week of building, to stop approving the same commands repeatedly |
| `/simplify` | Your CLAUDE.md caps agents at ~300 lines. This enforces it. |

### The honest point about skills

Skills are **not** what makes you money. They speed up building, which was never your bottleneck. **Your bottleneck is finding someone who will pay you.** Don't spend tomorrow installing skills; spend it building Agent 1 and sending emails.

---

## PART 5 — Questions for your friend tonight

Ask these. Write the answers down.

**On outreach**
1. Which channel actually books calls now — email, LinkedIn, cold calling, Loom video? What's your real reply rate?
2. How many touches before you get a response?
3. Where do you get prospect lists, and what do you pay?
4. What's your exact first line? Can I see a message that worked?
5. How do you handle "where are you based?"

**On closing**
6. What do you charge for your first client vs now? What did you charge your very first?
7. Do you take payment upfront, split, or on delivery?
8. What's the most common objection and your answer to it?
9. Do you use contracts? Which ones?

**On money**
10. **How do you receive USD?** Payoneer, Wise, Stripe? What are the fees?
11. How do you handle Indian tax on foreign income? Do you use a CA?
12. Have you ever been scammed or not paid? How do you protect yourself now?

**On the market**
13. Which vertical would you pick today, and why?
14. What are clients asking for that nobody is building?
15. **What would you tell me not to waste time on?**

**Then tell him this and watch his reaction:** "I found AI receptionists selling for $29–199/month off the shelf. How do you sell an AI agent against that?" His answer tells you whether he really understands this market.

---

## PART 6 — Your next two weeks

**Days 1–3** — Build Agent 1 (Prospect Audit). Buy a domain (~$12) and set up a professional email.
**Days 4–5** — Build your prospect list (100 businesses in one vertical, one US city). Run audits.
**Days 6–7** — Send your first 100 personalised emails with audits attached. Expect 1–5 replies.
**Days 8–12** — Build Agent 2 (Speed-to-Lead). Take any calls that come.
**Days 13–14** — Sell Agent 2 to whoever booked a call. First price: $500 setup + $150/mo.

**If nobody replies in week one, that is normal.** Re-read Finding 3. Volume and personalisation, not a new agent idea.

---

## Sources

- [Best Niches for AI Automation Agency 2026 — Agensi](https://www.agensi.io/learn/best-niches-ai-automation-agency-2026)
- [Best AI Automation Agency Niches for Small Business — DataStaq AI](https://datastaqai.com/blog/ai-automation-agency-niches-small-business)
- [How to Sell AI Agents: 5 Profitable Niches for 2026 — SellerShorts](https://sellershorts.com/resources/blog/how-to-make-money-selling-ai-agents)
- [AI Receptionist Pricing in 2026 — NextPhone](https://www.getnextphone.com/blog/ai-receptionist-pricing-guide)
- [Missed Call Text Back: Best Tools & Setup Guide 2026 — AIRA](https://www.getaira.io/blog/missed-call-text-back)
- [AI Phone Agents for Small Businesses: Costs and Failure Modes — Beancount.io](https://beancount.io/blog/2026/07/16/ai-phone-agents-receptionist-small-business-guide)
- [Why AI Automation Agency Cold Outreach Fails 2026 — Aurozen](https://aurozenmarketing.com/why-ai-automation-agency-cold-outreach-fails-in-2026/)
- [AI Outreach Automation: Benchmarks & What Works in 2026 — Prospeo](https://prospeo.io/s/ai-outreach-automation)
- [Build AI Agents with Claude: Agent SDK + Skills](https://decodethefuture.org/en/build-ai-agents-with-claude/)
- [Best Claude Code setups for AI & agent development — Claude Directory](https://www.claudedirectory.org/for/ai-agent-development)

**Note on source quality:** most of these are agency and vendor blogs with an interest in making this business look easy. Pricing claims are treated as ceilings, not expectations. The receptionist pricing (Finding 1) is the most reliable data here because it's real published product pricing.
