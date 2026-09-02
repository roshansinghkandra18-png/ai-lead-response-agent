# Real-email test set

## WHERE WE ARE — updated 13 August 2026

| Group | Status |
|---|---|
| **A** — the everyday cases | ✅ Done. 5 checked, 5 passed |
| **B** — one email per bug already fixed | ✅ Done. 7 checked, 7 passed |
| **S** — proving the spam / already-read fix | ✅ Done. 2 checked, 2 passed |
| **C** — things only real email can break | ⬅️ **NEXT. Not started.** 11 emails |
| **D** — the known weak spots | Not started |
| **E** — messy shapes real people produce | Not started |

**Pick up here:** send all 11 of Group C (send C1 before C9 — C9 is a
deliberate duplicate of it), then run `run_agent.py`. **C2b is expected to
fail** by taking the office switchboard number out of Barbara's signature
instead of the mobile she gave.

Full results live in `what-the-tests-checked/latest.txt`, Part 3.
Current score: **121 checked, 121 passed, 0 failed.**

---

Send these from your personal Gmail to **joesplumbingtest2026@gmail.com**.

Use **Ctrl+Shift+V** to paste, so no formatting comes across.

The agent is in practice mode — nothing is ever sent to anyone. Every reply it
writes is saved to `replies-it-wrote.txt`.

**Send in groups, not all at once.** Run the agent after each group and read
what it did. Finding one problem early beats untangling thirty at the end.

---

## Read this first — why some tests behave differently by hand

Real enquiries arrive from a **website robot** (`noreply@joesplumbing.com`).
Nobody reads mail sent there, so if the form gave no customer email, the plumber
has to phone instead.

You are sending by hand from a **real personal address**. So the agent decides
*you* are the customer and replies to you. That is correct behaviour, not a bug.

The order it uses:

1. Did the form include an `Email:` field? → use that
2. Was it forwarded? → never reply to the forwarder
3. Is the sender a robot (`noreply@`, `do-not-reply@`)? → don't use it
4. Otherwise → the sender is probably the customer

**Anything marked ⚠️ below cannot be fully tested by hand** because of this. It
says what it *can* still tell you.

---
---

# GROUP A — the everyday cases
*Start here. If these are wrong, nothing else matters.*

## A1. A complete website form
**Should:** find everything, offer two windows in Ohio time, ask nothing extra.

**Subject:** New Contact Form Submission

```
Name: Angela Foster
Phone: (216) 555-0143
Email: angela.foster@example.com
Service Needed: Water Heater Repair
Address: 1420 Fairmount Blvd, Cleveland OH 44118
When do you need this work done?: This week
Message: No hot water since Sunday.
```

**Check:** reply says *"your water heater repair"*, offers two windows,
and asks **no** extra question — the form already gave address and timing.

---

## A2. A form missing the address
**Should:** ask for the zip code, and only that.

**Subject:** New Contact Form Submission

```
Name: Kenneth Boyle
Phone: (440) 555-0166
Email: k.boyle@example.com
Service Needed: Toilet Installation
Message: Replacing the downstairs toilet.
```

**Check:** exactly one extra question, and it's the zip code — not two questions.

The zip is deliberate: a stranger may not want to give a home address in the
first exchange, and the zip already answers "are they in Joe's area?" The full
street address is collected in the follow-up conversation — which needs the AI
step, and isn't built yet.

---

## A3. Someone just typing, no form at all
**Guards Bug E.** **Should:** get the name from "I'm", the phone from the digits,
and the job from the words.

**Subject:** need help

```
Hi, I'm Marcus. My toilet won't stop running and it's driving me mad.
Can someone come take a look? 216-555-0921 is my number.
```

**Check:** reply opens **"Hi Marcus,"** — not "Hi there". That's the bug you'd
never notice until a customer felt talked at by a machine.

---
---

# GROUP B — one test per bug we already fixed
*These are the regression guards. If one of these fails, something we fixed has
come back.*

## B1. Supplier junk mail — guards Bug A
**Should:** bin it, silently. No reply, no review entry.

**Subject:** September deals on copper fittings

```
Hi there,
Our autumn sale is now on. Message us about bulk pricing on plumbing supplies.
```

**Check:** nothing in `replies-it-wrote.txt`, nothing in `leads.csv`.
**The bug was:** it saw "plumbing" in the sender's domain and replied to an advert.

---

## B2. Phishing — guards Bug D
**Should:** bin it. **Not** put it in the review pile.

**Subject:** URGENT: account verification required

```
Dear Customer,
Please confirm your details immediately to avoid suspension.
Contact: support@prize-notification.example.com  Phone: 1-800-555-0199
```

**Check:** `needs_review.log` does **not** grow. **The bug was:** spam filling
the review tray until you stopped opening it.

---

## B3. Three email addresses in one message — guards Bugs B and F
**Should:** reply to **Nadia** — not you, not the robot.

**Subject:** Fwd: New Contact Form Submission

```
Dave - another one for you.

---------- Forwarded message ----------
From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Nadia Kaur
Phone: (216) 555-0490
Email: nadia.kaur@example.com
Service Needed: Shower Valve Replacement
Message: Shower handle spins without turning the water on.
```

**Check:** `To:` line says `nadia.kaur@example.com`. **This is the single most
important test in the set** — both silent-failure bugs live here.

---

## B4. A forwarded enquiry with no customer email — guards Bug C and F
**Should:** read Rosa's details, and refuse to reply to you.

**Subject:** Fwd: New Contact Form Submission

```
Dave - can you handle this one?

---------- Forwarded message ----------
From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Rosa Delgado
Phone: (216) 555-0234
Service Needed: Toilet Installation
```

**Check:** the plumber gets a **CALL THIS PERSON** alert with Rosa's number, and
**no email is written at all.** This is the one test that proves the no-email
path on real mail.

---

## B5. Nothing to go on — guards Bugs G and H
**Should:** cope with no name and no job type.

**Subject:** hi

```
call me
```

**Check:** the subject reads **"Re: your plumbing issue"** — never
*"your your plumbing issue"*, and the body never says *"about plumbing issue"*
without the word "your". The exact phrase matters less than the shape: one
"your", never two, never none.

---

## B6. Flooding — guards Bugs I and J
**Should:** flag EMERGENCY, name the job as **Flooding**, alert the plumber
**with the customer's own words**, and offer no appointment times.

**Subject:** New Contact Form Submission

```
Name: Angela Foster
Phone: (216) 555-0143
Email: angela.foster@example.com
Service Needed: Burst Pipe
Message: The basement is flooding, water everywhere, please hurry.
```

**Check three things:** job says Flooding or Burst Pipe (not "plumbing job"), the
alert contains *"basement is flooding"*, and no times are offered.

---

## B7. The clock — guards Bug K
No email needed. **Every time you run the agent**, look at the header:

```
Their time : Wednesday 12 Aug, 08:36PM EDT
```

**Check:** that is Ohio time, and it does **not** match your laptop clock. If it
ever matches yours, the timezone fix has broken and every appointment time is
wrong.

---
---

# GROUP C — things only REAL email can break
*None of these can be tested with a made-up sample. This is why we're doing this.*

## C1. With a photo attached
**Should:** ignore the attachment and read the message normally.

**Subject:** New Contact Form Submission

```
Name: Derek Voss
Phone: (216) 555-0611
Email: d.voss@example.com
Service Needed: Leak Repair
Message: Photo attached of the damp patch under the sink.
```

**Attach any picture from your computer before sending.** Thumbtack lets
customers attach photos, so this will happen. **Check:** it doesn't crash and
still finds Derek.

---

## C2. With a phone signature
**Should:** not be confused by "Sent from my iPhone" or a footer.

**Subject:** dripping tap

```
Hi, this is Louise. The bathroom tap has been dripping for a week.
My number is 216-555-0455.

Sent from my iPhone
```

**Check:** name is Louise, phone is 216-555-0455. Real emails almost always
carry something like this and none of our made-up samples did.

---

## C2b. With a full work signature — THE HARD ONE
**Should:** use the number Barbara *said* is hers — not the office switchboard
sitting in her signature.

**Subject:** leaking radiator

```
Hi, this is Barbara. The radiator in our back office has been leaking
since Monday and there's a bucket under it now. Best number for me is
216-555-0644, I'm usually in after 10.

Thanks,

Barbara Nolan
Office Manager | Nolan & Sons Ltd
Tel: 216-555-9000  |  Fax: 216-555-9001
barbara.nolan@nolanandsons.example.com
www.nolanandsons.example.com
```

**The right answer:**

| | Should be | The trap |
|---|---|---|
| Name | Barbara | from "this is Barbara" |
| Phone | **216-555-0644** | her signature says `Tel: 216-555-9000` — the switchboard |
| Email | barbara.nolan@nolanandsons.example.com | fine either way |
| Job | Leak | from "leaking" |

**I expect this one to get the phone wrong.** The word `Tel:` is on our list of
phone labels, so the agent will most likely take the switchboard number from the
signature and ignore the mobile she actually gave.

**Why that matters:** the plumber rings a reception desk that has never heard of
Barbara, gets nowhere, and gives up on the lead. It looks like the agent worked —
it found *a* phone number — and nobody can see why the job went cold.

**If it fails, that is a genuine find**, and worth more than the ten tests that pass.

---

## C3. With bold and formatting
**Should:** read it exactly the same as plain text.

**Subject:** New Website Inquiry

Type this and make **some words bold** before sending — Gmail then sends the
message twice over, once as plain text and once as a web page.

The subject is deliberately worded differently from C1. Different website
builders phrase it differently, and we have never checked that the agent isn't
quietly relying on the exact words "New Contact Form Submission".

```
Name: Marcus Webb
Phone: (216) 555-0700
Email: m.webb@example.com
Service Needed: Drain Cleaning
Message: Kitchen sink is completely blocked.
```

**Check:** finds everything. **This tests the two-copies problem** we built for
but never proved on real mail.

---

## C4. A reply three levels deep
**Should:** recognise it as a reply and stay completely silent.

**Subject:** Re: Re: your water heater repair

```
Yes Tuesday still works.

On Tue, Aug 11, 2026 at 9:02 AM Dave Harris wrote:
> Sorry, can we say Tuesday instead?
>
> On Mon, Aug 10, 2026 at 2:14 PM Joe's Plumbing wrote:
> > Hi Dave, thanks for reaching out about your water heater repair.
> > Reply 1 for Tue 2-4pm or 2 for Wed 8-10am.
> > Name: Dave Harris
> > Phone: (614) 555-0182
```

**Check:** no reply written. **The danger:** it reads Dave's details out of the
old quoted text and greets him as a brand new stranger.

---

## C5. Everything in the subject, nothing in the body
**Should:** not crash. It will probably not have enough to work with.

**Subject:** Need a plumber for a blocked drain, call 216-555-0888

```
(leave the message body completely empty)
```

**Check:** it doesn't fall over. Whatever it decides, it must decide it calmly.

---

## C6. A very long subject line
**Should:** cope.

**Subject:** New Contact Form Submission from the website contact page regarding an urgent plumbing matter concerning the downstairs bathroom and kitchen area

```
Name: Priya Raman
Phone: (614) 555-7788
Email: p.raman@example.com
Service Needed: Drain Cleaning
```

---

## C7. Emoji in the message
**Should:** not fall over.

**Subject:** New message from your website

```
Name: Chloe Barnett
Phone: (216) 555-0322
Email: chloe.b@example.com
Service Needed: Leak Repair
Message: Ceiling is dripping please help
```

**Add two or three emoji to that last line yourself before sending.**

---

## C8. An accented name
**Should:** keep the accents, not turn them into gibberish.

**Subject:** Contact Form Submission - Joe's Plumbing

```
Name: Jose Ramirez
Phone: (216) 555-0512
Email: jose.ramirez@example.com
Service Needed: Garbage Disposal Repair
Message: Disposal hums but does not turn.
```

**Type the name with its accents before sending** — José Ramírez. That is the
whole point of this one. **Check:** the reply says "Hi José," correctly.

---

## C9. The same enquiry twice
Send **C1 again**, unchanged, straight after the first one — same subject, same
body, same photo. C1 and C9 are the ONE pair that must stay identical; that is
the whole point of the test.

Gmail will probably collapse the two into a single conversation because they
share a subject. That is fine and worth seeing — but check the spreadsheet, not
your inbox, to confirm both arrived.

**Should:** treat it as a second lead and reply again.

**Check:** two entries in `leads.csv`. Worth knowing, because a website form
that misfires will send duplicates and you should know what the client sees.

---

## C10. One long paragraph, no line breaks
**Should:** still find the facts.

**Subject:** plumbing question

```
Hello my name is Barbara Nolan and I have been having trouble with my downstairs bathroom for about three weeks now, it started with a slow drain which I thought was just hair so I tried one of those chemical things from the hardware store twice actually and it helped for maybe a day, now the toilet gurgles whenever the washing machine drains which my neighbour says means something about the main line, I am home most days except Wednesday, my number is 216-555-0644 if that is easier than email, thank you.
```

**Check:** name Barbara Nolan, phone found, job worked out from the words.

---
---

# GROUP D — the known weak spots
*We expect these to be imperfect. Send them so you know exactly how imperfect,
before a client finds out.*

## D1. A form field literally called "Subject" ⚠️
**Known limitation.** We deliberately ignore anything called "Subject", because
the email's own subject line caused Bug A.

**Subject:** Form Submission

```
Name: Helen Ward
Phone: (330) 555-0119
Email: helen.ward@example.com
Subject: Faucet replacement
Message: Kitchen mixer tap needs replacing.
```

**Check:** it will probably work the job out from the message instead. **Note
whether the reply still makes sense.** If it says "your plumbing job", that's the
limitation showing.

---

## D2. A routine job containing the word "urgent" ⚠️
**Known limitation.** Emergency detection is deliberately aggressive.

**Subject:** New Contact Form Submission

```
Name: Gerald Pike
Phone: (216) 555-0800
Email: g.pike@example.com
Service Needed: Faucet Replacement
Message: Not urgent at all, just whenever you have a free slot next month.
```

**Check:** does it wrongly cry EMERGENCY? The customer literally said *"not
urgent"*. If it alerts the plumber, we've found a real false alarm.

---

## D3. A Thumbtack-style lead ⚠️
**Unverified format** — built from the real form you filled in, but nobody has
seen the email a plumber actually receives.

**Subject:** New lead: Plumbing

```
Customer: Denise W.
Is any part of the building currently flooded?: No
Which appliances, if any, are affected?: Kitchen faucet
What type of property do you have?: Condo
When do you need this job to start?: Within a few days
Send a message to the pro: Bathroom faucet dripping constantly.
Zip: 44113
Phone: (216) 555-0355
```

**Check:** does it get name, job, zip and timing? Real Thumbtack hides the
customer email, so in real life the plumber would be told to call.

---

## D4. An Angi-style lead ⚠️
**Should:** handle their question wording and the split name.

**Subject:** New lead: Plumbing

```
What plumbing do you need help with?: Sump Pump
What needs to be installed or replaced?: Sump pump
What kind of location is this?: Home
When do you need this work done?: Within a week
Please tell us a little about your project: Basement pump making a grinding noise.
What's your project address?: 4180 Oak Ridge Rd, Cleveland OH 44121
First Name: Tomas
Last Name: Reyes
Phone: (216) 555-0288
Email: t.reyes@example.com
```

**Check:** name reads **"Tomas Reyes"**, not just "Tomas".

---

## D5. A job we never taught it
**Should:** still treat it as a real lead.

**Subject:** New Contact Form Submission

```
Name: Frank Osei
Phone: (216) 555-0611
Email: f.osei@example.com
Service Needed: Water Softener Service
Message: The salt tank has not been going down.
```

**Check:** it uses "water softener service" in the reply even though that word
isn't in its list — because the form told it directly.

---
---

# GROUP E — messy shapes real people produce

## E1. Written in capitals
**Subject:** NEW CONTACT FORM SUBMISSION

```
NAME: WALTER KIM
PHONE: (216) 555-0955
EMAIL: W.KIM@EXAMPLE.COM
SERVICE NEEDED: SEWER LINE INSPECTION
```

The email address is in capitals too — Roshan's correction, 15 Aug. Somebody
with caps lock on does not carefully switch it off for one field. It also
tests something the original version never did: that a reply addressed to an
uppercase address still works.

**Check:** the labels are recognised despite the capitals, the reply goes to
`W.KIM@EXAMPLE.COM`, and it greets him **"Hi Walter,"** — not "Hi WALTER,".
Shouting a customer's name back at them reads as machine-made.

---

## E2. Two phone numbers
**Subject:** New Contact Form Submission

```
Name: Ian Prescott
Phone: (216) 555-0733
Email: ian.prescott@example.com
Service Needed: Leak Detection
Message: Call my mobile 216-555-0801 if the house phone doesn't answer.
```

**Check:** it uses the labelled one, `(216) 555-0733`.

---

## E3. Somebody else's email in the message
**Subject:** New Contact Form Submission

```
Name: Owen Fletcher
Phone: (216) 555-0777
Email: owen.f@example.com
Service Needed: Water Heater Repair
Message: I rent - my landlord is manager@bigrealty.example.com, copy him if
there's a cost.
```

**Check:** reply goes to Owen, **not** the landlord.

---

## E4. Colons inside the customer's writing
**Subject:** New Contact Form Submission

```
Name: Sarah Klein
Phone: (216) 555-0311
Email: s.klein@example.com
Message: Here's the problem: the shower runs cold after 2 minutes.
Times that suit: mornings, any day
```

---

## E5. Form questions we've never seen
**Subject:** New Contact Form Submission

```
Name: Martin Doyle
Phone: (330) 555-0119
Email: m.doyle@example.com
How did you hear about us?: Facebook
Do you own or rent?: Own
Preferred technician: no preference
Service Needed: Faucet Replacement
```

**Check:** the three unfamiliar lines are ignored harmlessly.

---

## E6. An out-of-office auto-reply
**Should:** say nothing at all.

**Subject:** Automatic reply: Your enquiry

```
I am out of the office until August 24th with limited access to email.
For urgent matters please call 216-555-0400.
```

**Check:** no reply written. **This is the robot-loop danger** — two machines
emailing each other until Google marks the client's domain as a spammer.

---
---

# How to run and what to look at

After each group:

```
python run_agent.py
```

Then read:

| File | What's in it |
|---|---|
| `replies-it-wrote.txt` | Every reply, in full |
| `leads.csv` | The spreadsheet the plumber checks |
| `needs_review.log` | Anything it wasn't sure about |

**Write down anything that looks wrong**, however small. Bugs E and I were both
found by somebody reading output and thinking *"that's not quite right"* — not
by any test.

---

# What this set does NOT cover, honestly

| Not covered | Why |
|---|---|
| Replying to a `noreply@` robot address | You can't send from one. B4 covers the closest real case. |
| The agent not knowing the plumber's existing jobs | Needs the calendar, which isn't built yet |
| A settings file with a typo | Covered by `check_client.py` instead |
| Genuine Thumbtack / Angi / Google formats | Nobody has seen the real emails. One forwarded lead from a client settles it. |
| Windows that don't divide evenly into the working day | Would need a client config built to break it |
