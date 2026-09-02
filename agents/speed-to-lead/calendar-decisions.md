# Calendar step — decisions

Agreed Tuesday 18 August 2026, before any of it was built.
Plain English. No code in this file.

---

## STATUS — end of Tuesday 18 August

**Every decision in this file is made. Nothing is open.**

**What is BUILT and working:**
- `diary.py` — reads the plumber's calendar, writes bookings back, handles
  all-day and multi-day jobs, explains permission problems in plain English
- `make_reply.next_windows()` now takes `busy` and `travel_minutes` and skips
  slots he is already in
- Address-first replies; 1-hour windows; the 12–1 lunch
- The service account is live and proven read+write against the real test
  calendar. Project `speed-to-lead-505911`.
- 57 parser + 92 reply-engine checks, all passing

**Finished Wednesday 19 / Thursday 20 August:**
- `distance.py` — real distances from a 33,144-row zip coordinate file. Free,
  offline, nothing charged per lookup.
- The service-area check — too far away gets a polite no, not a booking
- `test_calendar.py` — 42 checks, PART 2B of the results file
- Reading the diary wired into `run_agent.py`; it refuses to start if the
  calendar cannot be opened
- Minimum notice 4 hours → 1
- The half-hour appointment grid (decided 18 Aug, found unbuilt 20 Aug)
- Travel measured from the previous customer where the plumber put an address
  on his own calendar entry

**227 checks. All automated ones passing.**

**Still not wired in:** `diary.add_booking()` is built and proven, but nothing
calls it — the agent still goes silent when a customer replies "1". That loop
closes with the AI step.

**The deadline moved.** It was Wednesday 19 August. There was roughly ten hours
more work than time, so Roshan invoked step three of his own written fallback
and moved it to **Friday 21 August**. Nothing is being cut.

**One thing is blocked on Roshan:** the test calendar. Six fake jobs in
joesplumbingtest2026@gmail.com, and the calendar shared with a **service
account** that can read AND write. Claude cannot do this — its Google
connection is signed into Roshan's personal account, not the test one. The six
jobs and the exact steps are near the bottom of this file.

**The read-only iCal plan was dropped on 18 August** — see "HOW THE AGENT
CONNECTS TO THE CALENDAR" below. It could not see the agent's own bookings,
which meant the agent double-booked Joe with jobs it had promised itself.

---

## THE ONE RULE THAT OVERRIDES EVERYTHING

**Once a window has been given to a customer, nothing may move it.**

Not the "done" signal, not a cancellation, not a convenient gap. The agent may
only ever fill time that has not been promised to anybody.

Turning up early is not a favour. The customer may be at work, in the shower,
or have taken the afternoon off for that window. A plumber knocking two hours
early is the same broken promise as knocking two hours late.

Roshan's rule. Anyone tempted to "optimise" it away later: don't.

---

## What Joe's day looks like

| Setting | Value | Why |
|---|---|---|
| Timezone | America/New_York | Everything is worked out in the client's zone, never the laptop's |
| Working days | Mon–Fri | |
| Day starts | 8:00 AM | **At the customer's door**, not leaving his own house. See below. |
| Day ends | 5:00 PM | |
| Lunch | 12:00 – 1:00 PM | Hard block. The agent will never offer a window running through it. |
| Arrival window | **1 hour** | Changed from 2. See "Why one hour" below. |
| Appointments start every | **30 minutes** *(a setting — Joe can change it)* | See "What times appointments can start" below |
| Travel between jobs | **Real drive time from Google** | Worked out from the customer's street address. See "Travel time and service area" below |
| How far Joe will travel | **ask every client** | Beyond it, the agent says "outside our area" instead of offering times |
| Minimum notice | 4 hours | Joe is under a sink and won't see his phone for a while |
| Max windows offered per day | 3 | Safety cap |
| Options offered per email | 2 | Two feels helpful, more feels like a form |

### "8:00 AM" means at the customer's door

Decided explicitly, because it was ambiguous and nobody had said. Joe leaves
home earlier on his own time. The first window of the day can therefore start
at 8:00 sharp.

If a future client means it the other way — *"I pull out of the driveway at
8"* — their first window has to start later, or they are late to their first
customer every single morning. **Ask this on the onboarding call.**

---

## Why one hour, not two

A window is a promise about **when Joe turns up**, not when he finishes.
Because the agent cannot see him, it has to assume he arrives at the very last
moment the window allows. So a wider window means more padding, and more of
Joe's day held back.

Leaking toilet (45 min), 30 minutes travel:

| Window told to customer | Agent assumes arrival | Next slot it will offer |
|---|---|---|
| 8–10 AM (two hours) | 10:00 | 11:30 |
| **8–9 AM (one hour)** | 9:00 | **10:30** |

One hour hands Joe back a full hour of sellable day, every job.

**The cost:** two hours is the trade norm because plumbers hit traffic and jobs
run long. A tighter window means Joe misses it more often. It is one number in
his settings file — if a real plumber says it is too tight, change the number,
no code.

---

## How the agent guesses when Joe is free

**Assume the latest possible arrival.** Window 8–9 means assume he knocks at
9:00.

Being wrong this way leaves Joe with a free hour. Being wrong the other way
leaves a customer standing in a doorway. Only one of those is recoverable.

The sum, every time:

> end of the window + how long the job takes + travel time = when he's free

---

## TIME NEEDED — four groups, not a catalogue

Called **time needed**, not "job size" — "size" gets misread as how big the job
is physically, rather than how long it takes.

Every time below comes from a US plumbing trade source, not from guesswork.
Sources listed at the bottom of this file.

### 1 hour — in and out

| Job | What the trade quotes |
|---|---|
| Blocked sink, tub or shower drain (simple snake) | 30 min – 1 hr |
| Blocked toilet | 30 min – 1 hr |
| Running toilet — flapper, fill valve | 30 – 45 min |
| Dripping faucet — washer, cartridge | 30 min – 1 hr |
| Leaky shut-off valve | under 1 hr |
| Water heater pilot light / thermocouple | "less than an hour" |
| Water heater flush / tune-up | ~1 hr |
| Low water pressure — diagnosis | quick check |
| Filter change / softener salt refill | quick |
| Sump pump test | quick |

### 2 hours — the ordinary day's work

| Job | What the trade quotes |
|---|---|
| Leak under a sink | 1 – 2 hrs |
| Faucet replacement | 1 – 3 hrs per fixture |
| Toilet replacement or install | **90 – 120 min** (confirmed) |
| Bidet install | ~2 hrs |
| Garbage disposal replacement | 1 – 2 hrs |
| Dishwasher water-line hookup | 1 – 2 hrs |
| Sewer camera inspection | 1 – 2 hrs |
| Main-line snaking / rooter service | 1 – 2 hrs |
| Frozen pipe thawing | 1 – 2 hrs |
| Shower or tub repair | 1 – 2 hrs |
| Hose bib / outdoor spigot | 1 – 2 hrs |
| Water heater thermostat or heating element | 1 – 2 hrs |
| Whole-home plumbing inspection | 1 – 2 hrs |
| Backflow prevention test | 1 – 2 hrs |
| Pinhole leak spot repair | 1 – 2 hrs |
| **Sump pump replacement** | **1 – 3 hrs** — existing pit and discharge line get reused |

### 4 hours — half a day gone

| Job | What the trade quotes |
|---|---|
| Water heater replacement (tank) | 2.5 – 4 hrs — the most-quoted figure in the trade |
| Water softener / filtration install | 2 – 4 hrs |
| **Sump pump — brand new installation** | **4 – 8 hrs** |
| Hydro jetting | 2 – 4 hrs |
| Gas line repair | half day |
| Main water line repair | half day |
| Sewage ejector / booster / well pump replacement | half day |
| Shower or tub installation | half day |
| Pipe descaling | half day |
| Recirculating hot water system | half day |

### Multi-day — the agent books a QUOTE VISIT, never the job

| Job | What the trade quotes |
|---|---|
| Whole-house repipe | **2 – 5 days** |
| Sewer line replacement | **1 – 2 days, sometimes a week** |
| Trenchless sewer lining / pipe bursting | days |
| Bathroom or kitchen rough-in | **1 – 4 days** |
| Slab leak repair | depends entirely on access |
| Tankless water heater conversion | 6 – 8 hrs or more |

**These are never booked as jobs.** The agent offers a **1-hour visit to come
and quote it** instead.

Why: no plumber on earth quotes five days of work off two sentences from a
stranger. He goes out, looks at the house, gives a price. So the appointment
that should be booked is the estimate visit, not the work.

What this protects: if the agent treated a repipe as "one day", it would offer
somebody the next morning while Joe is still on day two in the first customer's
crawl space. That is the double-booking fault again, on his most valuable jobs —
the worst possible place to have it.

The customer still gets a real appointment, so the instant-booking promise
holds. Roshan's decision, 18 August.

### Not on this list — emergencies

Burst pipe, flooding, gas leak, sewage backup, no water, overflowing toilet.
Handled separately and already built: **no times offered, Joe is alerted to
call immediately.** Unchanged.

---

Kept in the client's own settings file, so Joe can change any of the four
numbers himself without touching code, and any job can be moved between groups.

**The AI names the group. The settings supply the time.** The AI reads *"weird
noise in the wall when I flush"* and decides that is a 1-hour job. The settings
say 1 hour. The AI never invents a duration — otherwise a number appears in
Joe's diary that he can neither see nor change.

### Two things the research says we cannot fix

**"Simple" is doing a lot of work.** Every source says the same: a blocked
drain is 30 minutes *unless* the blockage is deep, in which case it is several
hours or a full day. Same job name, wildly different times. Neither the groups
nor the AI can see that difference — because the **customer doesn't know
either**. This is exactly why the "done" signal earns its keep: when it turns
out to be the quick version, Joe reclaims the afternoon.

**Access changes everything.** Pipes behind finished walls or under a concrete
slab take far longer to reach. Nothing in an email will ever tell us that.

Both belong in the README, so a client is not surprised by them.

**Fallback: 2 hours**, used when the AI cannot tell, when the AI is
unreachable, or before the AI step exists. Deliberately generous — the agent
under-books rather than over-books, and the "done" signal claws the time back.

### Why four sizes and not twenty-five exact times

Because differences under an hour disappear into the rounding, so writing them
down is wasted effort. The agent offers windows on the hour — never "10:17 to
11:17".

Joe's first job is 8–9 AM, a leaking toilet, so he is assumed to arrive at 9:00:

| If we say a toilet takes | He finishes | +30 min travel | Next window offered |
|---|---|---|---|
| 45 minutes | 9:45 | free 10:15 | **11–12** |
| 60 minutes | 10:00 | free 10:30 | **11–12** |

Identical. We could argue for twenty minutes about 45 versus 60, write it in,
ask Joe to confirm it — and the customer is offered the same slot either way.

The difference only matters when it is **big**: one hour versus four hours
changes the whole afternoon. So the useful question is never *"is this 45 or 60
minutes?"* but *"is this a small job or a big one?"* — which is what the sizes
answer.

Side benefits: onboarding is four questions instead of twenty-five, and the AI
choosing between four sizes is right far more often than the AI choosing
between twenty-five rows.

**If a paying client later says "my water heaters are always exactly 90
minutes", build the detailed list then** — with a real plumber's numbers
instead of guesses.

---

## The "done" signal

Joe sends one word — **done** — when he finishes a job. The agent already reads
his inbox every minute, so this needs no AI at all.

Two kinds of knowledge, living side by side:

- **Jobs already finished** → the agent knows the real time. Fact.
- **Jobs still to come** → the agent guesses. Estimate.

It uses whichever it has for each job. Nothing ever waits on a signal that
hasn't arrived — the cautious guess is always there underneath.

If Joe forgets to send it, nothing breaks. The agent just falls back to the
guess.

**It never moves a promise already made.** It only changes what the agent
offers to the next person who emails.

### The done signal cancels the 4-hour notice

Roshan's question, 18 August, and it exposed a gap nobody had written down.

The 4-hour minimum notice is **not about travel**. It is about Joe reading his
phone — he is under a sink and has not looked at a screen since 8am, so the
agent refuses to promise anyone a slot until he has plausibly had a chance to
see it.

**Tapping "done" is proof he has just looked at his phone.** The entire reason
for the wait has evaporated. So after a done signal the 4-hour rule no longer
applies, and the agent may offer him something as soon as he could drive there.

Without this the done signal is half-useless: Joe says he is free at 9, and the
agent still refuses to sell that morning.

**How soon after "done" he can be booked is a per-client setting** — Roshan's
call, because it genuinely differs. A plumber on a tight city patch is not the
same as one covering a county. **Default: travel time plus 30 minutes.**
Question 6 on the onboarding call.

---

## WHAT THE MINIMUM NOTICE IS ACTUALLY FOR

Roshan pushed hard on this, 18 August, and largely won. **Joe's default drops
from 4 hours to 1, and it becomes an onboarding question.**

### His argument

Once the agent has Maps, the job-length list and the diary, it can *compute*
when Joe is free — his diary says he is at Bergman's until 10, the list says
that job is an hour, Maps says the next customer is 20 minutes away, so he is
free at 10:20. That is arithmetic, not guesswork. Waiting four hours on top of
arithmetic wastes whole afternoons: a customer emailing at 1pm gets pushed past
Joe's 5pm finish and loses the same-day job entirely.

He is right about all of that.

### What the notice actually protects — and it is not arithmetic

**The agent knows when Joe will be FREE. It does not know Joe has AGREED.**

The diary says 9–10 at Bergman's. The agent computes free at 10:20 and promises
somebody 10:30. Joe knows nothing about it. He might finish early and drive to a
supplier for a part. He never agreed to be anywhere at 10:30.

**The minimum notice is Joe's chance to look at his phone and say "no, I can't
do that"** — before a customer is standing in a doorway waiting for him.

### Two things pure arithmetic cannot do

1. **Where is he when nothing precedes the slot?** If his diary is empty at
   10am, Maps cannot measure a drive from an unknown location. He could be at
   home, at a supplier, anywhere. The arithmetic only works when a job sits
   immediately before.
2. **The job list is a guess.** Every trade source says the same: a blocked
   drain is 1 hour *unless* the blockage is deep, in which case it is a full
   day. Give Joe 30 minutes of slack and a job that runs 2 hours over abandons
   the next customer.

### Where it landed

Four hours was far too blunt once Maps, job durations and the done signal
exist. Zero is too sharp — it removes Joe's ability to object.

**Joe's default: 1 hour. Asked on every onboarding call. Zero after a "done"
signal**, since he is demonstrably looking at his phone at that moment.

Note that Google Maps does **not** by itself justify shortening the notice.
Maps knows how long the drive takes; it knows nothing about when Joe next looks
at his screen. Different problems. What justifies shortening it is that the
notice was doing two jobs — covering unknown travel AND giving Joe a veto
window — and Maps takes the first job off it.

---

## GOING BACK TO LEADS WHEN JOE FREES UP EARLY

Roshan's idea, 18 August. **Agreed, and it lands with the AI step.**

The hole he spotted: a customer emails at 1pm, the notice period pushes them to
tomorrow, and the agent says "tomorrow 8am". At 2pm Joe finishes early and taps
done. His whole afternoon is now free — and the agent has no way to go back to
that customer.

**What it does:** emails them again with an extra choice. *"Good news — we've
had something open up at 3pm today if you'd rather not wait."*

**Why this does not break the promise rule:** nothing is un-promised. They were
offered tomorrow and tomorrow is still theirs. They are simply given one more
option. The rule forbids *moving* a window someone has accepted, not *adding*
one.

**Cost:** about 1.5 hours, and it needs the AI step, so it lands Thursday.

**Watch for:** this must never feel like pestering. If it starts chasing people
about enquiries they sent hours ago and forgot, put a cutoff on it.

---

## FOR THE README — how to explain what the client is buying

Roshan's call: this is the clearest sales explanation of the product. Not
"an agent that replies fast" — **an agent that finds the jobs his day already
had room for.**

> Joe has Carla booked 8–9 AM (leaking toilet) and Dave booked 1–2 PM (water
> heater). At 9:00 Joe finishes at Carla's and sends one word: **done**.
>
> At 9:05, Maria emails. Blocked drain.
>
> **Without the done signal**, the agent thinks Joe might still be at Carla's
> until 10:15. The earliest it could offer Maria is 10:30–11:30 — which would
> run him past Dave's start. So it offers her nothing. Maria calls someone
> else.
>
> **With the done signal**, the agent knows Joe finished at 9:00. It offers
> Maria 9:30–10:30. She's done by 11:15, Joe is at Dave's by 1.
>
> Same day, same plumber. One version earns money and one doesn't. The gap was
> always there — the agent just couldn't see into it.

---

## What times appointments can start

Not a law — a setting. The agent can offer 10:20 just as easily as 10:00.

| Step | Sounds like | Time wasted by rounding |
|---|---|---|
| Hourly | "between 11 and 12" | up to 59 min per job |
| **Half-hourly (default)** | "between 10:30 and 11:30" | up to 29 min per job |
| Quarter-hourly | "between 10:15 and 11:15" | up to 14 min per job |

Quarter-hourly starts to read like a machine wrote it, and no plumber talks
that way. It would also weaken the case for four job sizes — at that fineness,
45 minutes and 60 minutes land in different slots. Half-hourly keeps the sizes
sound.

---

## EVERY NUMBER IN ONE PLACE

Several numbers repeat and mean different things. This table is the answer to
"wait, what was the 2 hours again?"

| Number | What it is |
|---|---|
| 8:00 AM – 5:00 PM | Joe's working day, at the customer's door |
| Mon–Fri | days he works |
| 12:00 – 1:00 PM | lunch, hard block |
| 1 hour | the arrival window told to the customer |
| every 30 min | what times an appointment may start |
| 30 minutes | travel between jobs (Joe's number — ask every client) |
| minimum notice | **ask every client.** Joe's default drops from 4 hours to 1. It is his chance to SEE a job and object, not a travel allowance |
| travel + 30 min | how soon he can be booked after tapping "done" — a per-client setting, default shown |
| 3 | most windows offered on any one day |
| 2 | choices given to each customer in one email |
| 1 / 2 / 4 hours | the three "time needed" groups |
| 1 hour | a quote visit — what multi-day jobs get offered instead of the job |
| 2 hours | held back when the agent has no idea what the job is |

**"2 hours" appears three times** and means three different things: a standard
job, the unknown-job fallback, and the *old* arrival window now changed to 1
hour. **"4 hours" appears twice**: a big job, and the minimum notice. They are
unrelated.

---

## Questions to ask on every onboarding call

Not assumptions — things a real plumber must answer:

1. Does "I start at 8" mean at the customer's door, or leaving your own house?
2. **How far will you travel to a job?** Beyond that, the agent turns the
   enquiry away instead of offering times.
3. When is lunch, and is it fixed?
4. How long is a quick job, a standard one, a big one, for *you*?
5. Do you want appointment times on the hour, or every half hour?
6. **Once you tell us a job is done, how soon can we book you the next one?**
   Travel time plus 30 minutes is the default. This is the number that decides
   whether telling us "done" is worth your thirty seconds.
7. **How much warning do you need to accept a job you haven't seen yet?**
   This is your chance to look at your phone and say no before a customer is
   waiting for you. Default 1 hour. Answer 4 if you work long stretches
   underground; answer 1 if you check your phone between jobs.

---

## ⚠ TRAVEL TIME — WHAT IS BEING BUILT RIGHT NOW (18 August)

**Free offline zip-code distances first. Google Maps when a card arrives.**

Roshan has no credit card, and his debit card is lost — he applies for a new one
on Wednesday 19 August. **Google Maps drive times require billing, which
requires a card.** UPI is only available to enterprises on invoiced billing, so
it is not an option.

**What is NOT blocked:** the Google Calendar API is free and does **not** require
billing. The service account, reading the diary and writing bookings back all go
ahead with no card at all.

**So travel time is built in two layers, and it always was going to be:**

| Layer | Status |
|---|---|
| Free zip-code distances, offline | **Build now.** ~2 hrs. Download a file of US zip coordinates once, work out real miles, convert to drive time. No API, no card, no cost ever. |
| Google Maps drive times | **When the card arrives.** Slots in behind the same interface — nothing gets rebuilt. |

**Build it so the Maps version drops in later without rework.** One function
answers "how long from A to B"; today it does the zip maths, tomorrow it calls
Maps and falls back to the zip maths.

**Nothing decided today is undone.** Asking for the full street address is still
right — Joe needs it to actually drive there, and the zip sits inside the
address anyway.

**Worth remembering:** the Maps key is really the *plumber's* usage, not
Roshan's. A paying client sets up their own Google Cloud account with their own
card. Roshan may never need one.

The honest limits of the zip version: straight-line distance rather than roads
(multiply by a factor to compensate); a zip is an area, not a point, so two jobs
in one large zip look like next-door neighbours; and **no traffic awareness at
all** — which was Roshan's whole argument for Maps, and it stands.

---

## TRAVEL TIME AND SERVICE AREA — THE DESIGN

**Real drive times from Google, worked out from the customer's street address.**
*(The destination. See the section above for what ships first.)*

Roshan's decision, Tuesday 18 August. It reverses an earlier decision — see
"THE ORDER CHANGED" below.

### Why a flat number wasn't good enough

A single number is wrong in both directions. Two jobs on the same street and the
agent still holds back half an hour it doesn't need. Two jobs at opposite ends
of the county and half an hour isn't nearly enough.

Roshan's argument, which settled it: **zip codes cannot see traffic.** A journey
the agent thinks is 30 minutes becomes an hour in the rain. Joe misses the
window, the customer blames him, and he regrets buying the agent.

*(One misunderstanding cleared up along the way: a flat setting would have been
written once on the onboarding call, not edited daily. Roshan had thought Joe
would be changing it several times a day. Nothing in the design asked that.)*

### THE ORDER CHANGED — address first, then times

**This reverses the zip-first decision.** The memory note
`speed-to-lead-zip-then-address` is now out of date and must be rewritten.

The old order was: ask for the zip, offer times, collect the street address
afterwards. That created a circle — travel time needs an address, but the
address only arrived *after* the slot had been offered.

**The new order:**

1. Ask for the **full street address** in the first reply
2. Check it is inside Joe's service area
3. If it is not — say so plainly, and offer no times
4. If it is — work out real drive times, and offer only slots Joe can make

**Why asking is fine.** Someone contacting a plumber is asking a stranger to
come to their house. The address *is* the job. The earlier privacy worry was
overweighted. And the reason given is a good one: *"so we can check we cover
your area."*

**What this buys beyond accuracy:** the agent can now turn away work outside the
area. Today it would happily book a job 60 miles away, and Joe would find out
when he opened the spreadsheet. That is a real feature, not a side effect.

**Many web forms and lead platforms already include the address**, so in a lot
of cases the agent has it without asking anybody anything.

### The honest limit — do not oversell this

Google's traffic prediction works on **historical patterns**. It knows Thursday
4 PM is usually slow on that road. **It cannot know it will rain on Thursday.**

So "traffic-aware" is not "weather-proof". Nothing can schedule around weather
three days out. What actually absorbs a bad day is the **"done" signal** — when
Joe runs late, the agent stops offering slots he cannot make.

### What it costs

- **Google's Routes API** (the replacement for the Distance Matrix API) has a
  free monthly allowance, then about **$10 per 1,000 lookups**. At roughly 100
  leads a month a plumber sits inside the free allowance, so realistically
  **$0 a month**. Cost was never the objection.
- It needs a **Google Cloud account with a card on file**. Roshan will walk each
  client through this on a video call, so it is a sales step, not a blocker.
- **Build: about 5 hours** — API and error handling 2, service-area check and
  its setting 1, reworking the first reply to ask for the address 1, re-proving
  the 83 reply-engine tests 1.

### The fallback stays

If the Google call fails, the agent falls back to a plain distance estimate
rather than showing an error.

Not because Google is unreliable — Uber depends on it and never breaks in front
of you, and that is *because* it has fallbacks. It is also the project's own
rule: a client seeing a raw error is a refund request. About twenty minutes.

Sources: https://mapatlas.eu/blog/google-maps-api-pricing-2026 ·
https://developers.google.com/maps/documentation/distance-matrix/usage-and-billing

---

## Everything in this file is decided

No open questions. Approved by Roshan, Tuesday 18 August 2026.

---

## THE TEST CALENDAR — only Roshan can do this

Claude's Google Calendar connection is signed into **roshansinghkandra18@gmail.com**
(his personal account), not the test account. It cannot create these events.
Roshan adds them by hand.

**Step 1 — set the timezone FIRST.** Sign into **joesplumbingtest2026@gmail.com**
→ Google Calendar → gear icon → Settings → Time zone →
**(GMT-04:00) Eastern Time – New York**.

Skip this and every job below lands at an Ohio time nobody intended, and the
whole test proves nothing. Joe's 8am–5pm Eastern is 5:30pm–2:30am in Noida.

**Step 2 — add these six.** Ordinary timed events. Do **not** tick "All day" on
3 or 6 — type the times. An all-day event is different data in Google, and this
needs testing against real bookings.

All jobs are in the FUTURE. Roshan spotted that the first draft put two of them
on the current day, which was already half over in Ohio — a test built on a
partly-gone day gives unreliable results, and the 4-hour minimum notice means
the agent would not offer today anyway. The first draft also had job 5 and job 6
both starting Monday 24th at 8:00 AM, which clashed.

| # | Day | Start | End | Title |
|---|---|---|---|---|
| 1 | Wed 19 Aug | 9:00 AM | 10:00 AM | Running toilet – Bergman |
| 2 | Wed 19 Aug | 2:00 PM | 4:00 PM | Leak under sink – Alvarez |
| 3 | Thu 20 Aug | 8:00 AM | 5:00 PM | Bathroom rough-in – Kowalski |
| 4 | Fri 21 Aug | 3:30 PM | 4:30 PM | Sewer camera inspection – Prewitt |
| 5 | Mon 24 Aug | 8:00 AM | 9:00 AM | Dripping faucet – Duggan |
| 6 | Tue 25 Aug 8:00 AM → **Wed 26 Aug 5:00 PM** | | | Whole-house repipe – Okonkwo |

**What each one is there to catch:**

- **1 and 2 together (Wed)** — a normal messy day. Busy 9–10, free till lunch,
  lunch 12–1, free 1–2, busy 2–4, free 4–5. The agent must find those gaps
  *and* leave travel time either side of both jobs.
- **3 (Thu)** — blocked wall to wall. The agent must offer Thursday nothing at
  all. This catches an agent that only *mostly* reads the diary.
- **4 (Fri)** — a single late job leaves 8 AM to 2 PM wide open, and the agent
  had better offer it. This is the case Roshan caught Claude getting wrong. It
  also starts on the **half hour**, testing the new appointment grid.
- **5 (Mon)** — start-of-day edge, and leaves Monday afternoon completely empty
  as a control. If the agent offers nothing on a wide-open Monday afternoon,
  something is broken in the opposite direction.
- **6 (Tue–Wed)** — spans two days. Both days must come back fully blocked.

**Step 3 — share the calendar with the service account.** Settings → click the
calendar's name under "Settings for my calendars" → **Share with specific
people or groups** → **Add people** → paste the service account's email address
(it looks like `something@project.iam.gserviceaccount.com`) → set permission to
**"Make changes to events"** → Send.

The service account is created in the same Google Cloud project as the Maps
key. Its JSON key file goes in the agent folder, and `.env` points at it:

```
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
CALENDAR_ID=joesplumbingtest2026@gmail.com
```

**The JSON key file must never be committed to git.** It is a password in file
form. Check `.gitignore` covers it.

---

## HOW THE AGENT CONNECTS TO THE CALENDAR

**Decided 18 August: a service account with read AND write access.**
The earlier read-only iCal plan was dropped.

### Why iCal was dropped — Roshan's scenario

A read-only address means the agent can read Joe's diary but never write to it.
So:

> The agent books Joe 4–5pm. Joe goes and does the job. The agent has no way to
> put that booking in the calendar. Next time it looks, 4–5 is empty — so it
> offers that slot to somebody else.

**The agent double-books Joe with its own booking.** That is worse than not
reading the diary at all, because it looks like it is working.

### Why a service account, and not OAuth

The reason iCal was chosen originally was "read-only, no OAuth consent screen,
no verification wait". A **service account** gets all three of those *and* write
access:

- It is a robot email address created inside the Google Cloud project that
  already exists for the Maps key.
- The client shares their calendar with that address and grants **"Make changes
  to events"** — same settings page as the old iCal address, a few extra clicks.
- No consent screen, no Google verification queue.

Source: https://developers.google.com/workspace/calendar/api/concepts/sharing

### What it costs

About 2 hours more than the iCal version, plus one extra sharing step per
client on the onboarding call.

---

## THE LIMIT THAT CANNOT BE FIXED — say it on the sales call

Roshan's second scenario, 18 August:

> Joe takes a job over the phone for 2–3pm and never puts it in his calendar.
> The agent offers 2–3 to somebody else. Two customers, one plumber.

**There is no clever fix.** The agent has one window into Joe's day and he
didn't write in it. Not a bug — a boundary.

> **The agent only knows what is in your calendar. If it is not in the
> calendar, it does not exist.**

That goes in the README in plain words, and it gets said out loud on the sales
call — not buried in small print. **A plumber who will not put his jobs in a
calendar is not a customer for this product**, and that is far better discovered
on the call than after he has paid.

**What we can do** is make his own mistake visible fast: the agent tells Joe
immediately every time it books something, and with write access the booking
appears in his own calendar. If he has double-booked himself he finds out within
a minute, rather than when two customers are waiting.

---

## Sources for the job names and times

Twelve searches and page-fetches, 18 August 2026. The job wording comes from
plumbers' own service menus, not from guesswork.

**Service menus — where the job names came from**
- https://www.housecallpro.com/resources/plumbing-services-list/ *(also gives toilet install 90–120 min, basic faucet repair ~1 hr)*
- https://www.servicefusion.com/blog/plumbing-services-list
- https://serviceagent.ai/blogs/plumbing-services-list/

**Durations**
- https://www.mrrooter.com/yavapai-and-coconino-counties/about-us/blog/how-long-does-a-plumber-take/
- https://www.baethkeplumbing.com/blog/water-heaters/water-heater-replacement-time/
- https://calltripleplay.com/articles/how-long-does-it-take-to-fix-a-plumbing-issue/
- https://www.dillonplumbing.com/expert-tips/pipe-repair-timeframe-in-nampa-id-what-to-expect-with-dillon-plumbing/
- https://trustcampbell.com/blog/how-long-sewer-line-replacement-takes/
- https://usaplumbingdirectory.com/faq/how-long-does-sump-pump-installation-take/ *(sump pump: new install 4–8 hrs, replacement 1–3 hrs)*
- https://www.callprideplumbing.com/how-long-does-it-take-to-install-a-water-softener-a-complete-homeowners-guide/
- https://www.tonysplumbing.com/how-long-does-repiping-really-take-a-homeowners-step-by-step-timeline/ *(repipe 2–5 days)*
- https://www.hopeplumbing.com/estimated-timeline-for-a-full-bathroom-remodel/ *(rough-in 1–4 days)*

**Corrected by this research:** the sump pump had been put flat at 4 hours. It
is two different jobs — swapping an existing pump reuses the pit and takes
1–3 hours; a brand-new installation is 4–8 hours. They sit in different groups
now.

---

## What this cost in hours

The calendar step was 8 hours in the countdown plan. As designed here:

| | Hours |
|---|---|
| Read the diary, stop double-booking | 8 |
| Job sizes (four buckets, not a 25-row list) | 1.5 |
| Done signal | 1 |
| Lunch break + travel time | 1 |
| **Total** | **11.5** |

Plus roughly 1 hour added to the AI step, for naming the job from fuzzy
wording.

Said out loud on Tuesday 18 August rather than discovered on Wednesday night.
