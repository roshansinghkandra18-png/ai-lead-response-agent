# Countdown to 31 August — Speed-to-Lead ready to sell

All times **IST (Noida)**. Written Monday 24 August 2026.

**The goal:** by **Monday 31 August, 9pm**, the Speed-to-Lead agent is
finished, tested, documented and deployed, Roshan can honestly sell
*"we book your jobs for you"*, and the first cold outreach has actually gone
out.

---

## Why this plan looks different

| Deadline | What happened |
|---|---|
| Wed 19 Aug | Sunday was lost. Mon/Tue went on designing the calendar rather than building it. |
| Fri 21 Aug | Two days not worked. |
| Tue 25 Aug (set 21 Aug) | Moved again same evening, before an hour of it was worked. |
| Wed 26 Aug | Nothing was done against it at all. |
| **Mon 31 Aug, 9pm** | **This one — Roshan's own ultimatum.** |

Four plans have slipped in a row, all for the same reason: no slack, and
outreach kept getting pushed to "later." This plan is a full week (7 days)
instead of 3-4, with real buffer built in near the end rather than a single
light day tacked on.

**Nothing is being cut. The full product ships, AI step included.**

**On the ultimatum itself:** Roshan asked that everything be deleted if this
slips. That won't happen automatically — deleting a week of working, tested
code is exactly the kind of action that gets a conversation and explicit
sign-off in the moment, not a standing order from today. If 31 Aug passes
incomplete, we'll look honestly at what's done and decide together. The
deadline pressure stands either way.

---

# WHERE THINGS ACTUALLY STAND (unchanged since 20 Aug — nothing was built)

**Working and tested — 227 checks, all automated ones passing:**
- Reads a live Gmail inbox and spam folder every 60 seconds
- Pulls name, phone, second phone and whose it is, email, job type, address and
  urgency out of messy human writing
- Survives signatures, forwarded chains, caps lock, emoji, form questions
- Spots emergencies and alerts the plumber instead of offering times
- Asks for the full street address before offering any time
- Turns away work outside his service area, politely
- **Reads his real Google Calendar** and offers only slots he is genuinely free
  for, with travel time either side
- Never offers his lunch hour, a weekend, or a US public holiday
- Logs every lead to a spreadsheet he can open in Excel
- Won't email itself in circles, won't answer old mail on first run, survives a
  dropped connection

**The one thing it cannot do:** close the loop. A customer replies "1" and the
agent goes quiet. That is the AI step, and it is the only large thing left.

**Found 24 Aug, fixed same day:** `latest.txt` had a stale summary paragraph
claiming E1/E2 were still open, contradicting its own detailed record showing
both fixed and re-proven on live Gmail on 17 Aug. Documentation bug, not a code
bug.

---

# MONDAY 24 AUGUST (today) — outreach, then the three loose ends

**Target: the first cold emails are actually sent. This is the task that has
slipped four times — it goes first, before any more code.**

## First — outreach (2 hours, before anything else)

- [ ] Work out who to target: small US plumbing firms with a Gmail address and
      no scheduling software (~68,000 of them — see the "who we sell to" notes)
- [ ] Write the email. Lead with the number that sells it:
      **78% of homeowners hire the first contractor who responds**
- [ ] Find 10 firms and send
- [ ] Do NOT promise firm booking until the AI step is done. Sell what is
      already true: every enquiry answered in 60 seconds, real appointment
      windows from his own diary, emergency alerts

## Then — the three loose ends (1.5 hours)

- [ ] **Fix the drive-time estimate.** One speed is wrong at both ends. Two
      speeds — town for the first few miles, highway after — brings Mentor from
      50 minutes to ~35 (real: 35-40) and Columbus from 245 to ~155 (real: 135)
- [ ] **Save the real-calendar run**, so the proof it works against Google is a
      file Roshan can re-run himself rather than a terminal window that scrolled
      away
- [ ] **Decide what happens on an unknown address.** Accepting an address we
      cannot place is gambling — could be next door or in Alaska, and the agent
      offers times either way
- [x] Fix the stale E1/E2 summary in `latest.txt`

---

# TUESDAY 25 AUGUST — the AI step, part one

**Target: the agent understands a reply instead of ignoring it.**

- [ ] Anthropic API wired in, key from `.env`, never hardcoded
- [ ] Every API failure handled — a client must never see a raw error
- [ ] A hard cap on spend, so a loop cannot empty the balance
- [ ] Understands "1", "2", "the first one", "Tuesday works", "neither"
- [ ] Understands a counter-offer — "how about Friday morning?"
- [ ] Tests written and passing

---

# WEDNESDAY 26 AUGUST — the AI step, part one (finish)

**Target: fuzzy, real-world replies stop confusing it.**

- [ ] Understands fuzzy job descriptions — "weird noise in the wall when I
      flush" — and picks the right time-needed group
- [ ] Token usage logged per run, so the agent can be priced properly
- [ ] Tests written and passing
- [ ] Check for replies to Monday's outreach

---

# THURSDAY 27 AUGUST — the AI step, part two

**Target: the booking loop closes.**

- [ ] The chosen slot is **written into the plumber's calendar** —
      `diary.add_booking()` is already built and proven, nothing calls it yet
- [ ] Confirmation email to the customer
- [ ] The whole conversation logged so the plumber can read it back
- [ ] The "done" signal — Joe replies with one word and the agent knows he is
      free early. No AI needed, it is word-matching the agent already does
- [ ] Going back to leads pushed to tomorrow when he frees up early
- [ ] Tests written and passing

---

# FRIDAY 28 AUGUST — the README

**Target: a non-technical client can set it up alone.**

- [ ] **README.md** for a non-technical American client: what it does, how to
      set it up assuming zero terminal experience, what it costs to run
- [ ] README covers the **domain mail records**, or the client's replies get
      filtered into customers' spam folders
- [ ] README covers the **Google Cloud account, the service account, and
      sharing the calendar** — in plain steps with no jargon
- [ ] README is honest about the three things nothing can fix:
      "simple" jobs that turn out to be all-day ones; traffic prediction that
      cannot see tomorrow's weather; and **the agent only knowing what is in
      the calendar — if it is not in the calendar, it does not exist**
- [ ] `example.env` checked — every key listed, fake values only
- [ ] Second batch of outreach, and follow-ups to the first

---

# SATURDAY 29 AUGUST — deploy

**Target: it runs somewhere other than Roshan's laptop.**

- [ ] Hosting decided, with the monthly cost written down before committing
- [ ] Deployed and running unattended for at least one hour
- [ ] Cost per lead worked out from real token usage, and the selling price set

---

# SUNDAY 30 AUGUST — REAL BUFFER DAY

**Deliberately empty. Nothing new gets scheduled here.**

This is the day that absorbs whatever overran Mon-Sat. If everything above is
actually done, this day is free. If Roshan doesn't work today, that is fine —
it was never counted on.

---

# MONDAY 31 AUGUST, until 9pm — final proof and ship

- [ ] `SEND_FOR_REAL` tested properly, once, against a mailbox Roshan owns
- [ ] Full test run — every part green — saved to `latest.txt`
- [ ] `TEST_LOG.md` known-limitations list honest and current
- [ ] **Commit the repo.** A week+ of work still exists only as loose files
      with no history and no undo
- [ ] Final check-in by 9pm: what shipped, what didn't, decide together what's
      next

**End of day: sellable, or an honest account of exactly what isn't.**

---

# IF THIS SLIPS TOO

**No automatic deletion — see the note at the top.** But the AI step is what
gets cut, and what ships is:

> Every enquiry answered within 60 seconds in the customer's own words. Real
> appointment windows from the plumber's actual diary, that he can physically
> drive to. Work outside his area turned away. Emergency alerts. A lead
> spreadsheet he can trust.

That is genuinely sellable. The words *"we book your jobs for you"* would wait.

**Three things are never sacrificed:**

- **The README.** A client who cannot set it up alone asks for a refund, and
  the support calls cost more hours than the README ever would.
- **The test groups.** Group C found four faults nobody predicted, every one
  invisible from the plumber's side.
- **Practice mode staying on until the last day.** `SEND_FOR_REAL` gets
  switched on once, deliberately, against a mailbox Roshan owns.
