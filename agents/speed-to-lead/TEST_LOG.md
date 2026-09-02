# Test log — Speed-to-Lead agent

A running history of everything we have tested on this agent, what broke, and
what was done about it. Add to it every time something new gets tested.

Written in plain English on purpose. No code.

**To run the tests yourself — one command:**

```
cd "agents/speed-to-lead"
python run_all_tests.py
```

It runs everything and writes the full results, including what was fed into each
test and what came back, to:

```
what-the-tests-checked/latest.txt
```

**Current result: 84 tests, 84 passing.**
(24 on the parser, 60 on the reply engine.)

---

# The story so far

## Round 1 — three samples (all we started with)

The parser was tested against three fake emails: a plain text contact form, an
HTML contact form, and a supplier newsletter.

**Result: 1 passed, 2 failed.** Two bugs found (A and the HTML one below).

The important lesson: three clean samples prove almost nothing.

## Round 2 — eleven tests

Eight deliberately awkward scenarios were added: someone typing with no form at
all, a customer replying to us, a forwarded enquiry, a marketplace lead, stray
colons, an out-of-office auto-reply, spam, and unknown form fields.

**Result: 8 passed, 3 failed — and one of the "passes" was hiding the worst bug
of the lot.** Six bugs total were found and fixed across this round.

## Round 3 — twenty-four tests

Roshan went to Thumbtack and Angi and filled in their real plumbing forms, then
wrote down every question. Web research added the published formats for
Squarespace, Gravity Forms, WPForms and Google Local Services.

Thirteen new tests were built from those real formats.

**Result: 24 passed, 0 failed.**

## Round 4 — the reply engine

The parser could read an email but not answer one. The reply engine was built:
it works out arrival windows from the plumber's settings, writes the email, and
decides who receives what — the customer, the plumber, or both.

It was run against all 24 test emails on its first day.

**Result: it worked, and produced four problems, all found before anything was
sent to anyone.** Those are bugs G, H, I and J below.

A fifth, smaller wording problem was fixed straight after: job names that are a
condition or a bare appliance read clipped on their own — *"about your
flooding"*, *"about your shower"* — so the word "issue" is now added to those.
Job names that already describe work (*"water heater repair"*) are left alone.

**To see the emails it writes:**

```
python demo_replies.py
```

## Round 5 — the clock, holidays and lunch breaks

Three things the agent had no idea about were added, and the reply engine got
its own inspection equipment for the first time.

**The clock.** The agent had been asking *our* laptop what time it was. Our
laptop is in India; the clients are in America. Every appointment it offered was
out by nine and a half hours. Each client's settings file now carries a
timezone, so the agent works entirely on the client's local clock. This needed
one small download — see the note at the bottom of this file.

**Public holidays.** The agent would happily have offered *"Thursday 2-4pm"* on
Thanksgiving. It now works out every US public holiday from the rules rather
than from a typed-in list, so it keeps working in 2030 without anyone updating
anything. Each client chooses which ones they close for, and can add their own
days off.

**Lunch breaks.** A client can now say "don't book me 12 to 1" and the agent
will never offer a window that runs through it. Optional — Joe doesn't take one,
Maria does, so both paths are tested.

**Telling the customer why.** If a holiday is the reason the first free slot
isn't sooner, the email now says so — *"We're closed Friday for the 4th of
July"* — including when the customer writes to us on the holiday itself. Without
that line the plumber just looks slow.

**Result: 84 passing.** The reply engine went from having no tests at all to
having 60.

## Round 6 — the settings checker

Until now, a typo in a client's settings file made the agent crash with a page
of technical error text. That is fine when it happens to you alone at your desk.
It is not fine on an onboarding call with the client watching your screen.

`check_client.py` now reads a settings file and either reads it back in plain
English, or lists every problem with the exact line to write instead.

```
python check_client.py clients/joes_plumbing.ini
```

A deliberately broken file, `clients/EXAMPLE-broken-on-purpose.ini`, is kept on
purpose. It contains the ten mistakes a person actually makes filling one in for
the first time — an email address with no @, a timezone that doesn't exist,
"mun" instead of "mon", "8am" instead of "08:00", a number written as "four", a
date written the British way round. The checker catches all ten and explains
each one.

**Result: 97 passing** (24 on the parser, 73 on the reply engine and checker).

---

# The eleven bugs we found

Full detail with fixes is in `BUGS.md`. Summary:

| Bug | What it did | Found in |
|---|---|---|
| **A** | Replied to a supplier's junk-mail advert | The newsletter test |
| **B** | Addressed the reply to the website's own robot, so the customer never got it | Two tests that were **marked PASS** |
| **C** | Binned a customer that a colleague had forwarded | The forwarded enquiry test |
| **D** | Put spam in the "please check this" tray instead of the bin | The spam test |
| **E** | Didn't notice "Hi, I'm John" means his name is John | The no-labels test — **spotted by Roshan, not by the test** |
| **F** | Sent the customer's confirmation to the colleague who forwarded it | The forwarded test, *after* Bug C was fixed |
| **G** | Wrote broken English — *"thanks for reaching out about leak"* | Every customer email |
| **H** | Said the same word twice — *"Re: your your plumbing job request"* | Tom's flooding basement |
| **I** | Didn't know flooding is a plumbing job at all | Tom's flooding basement — **spotted by Roshan** |
| **J** | Told the plumber to drop everything without saying why | All three emergencies |
| **K** | Used our laptop's clock, so every appointment time was 9½ hours wrong | No test caught it — every test used times with no country attached |

**Two of these passed their tests at the time** (B and F). They surfaced only
because somebody read the output line by line and asked "is that actually
right?" **Two more (E and I) were spotted by Roshan reading the output**, not by
any test.

---

# What each of the 24 tests proves

## The everyday cases

**1. Plain text contact form** — the normal case. A `Name: / Phone: / Service
Needed:` email from a website form. Proves the basic reading works.

**2. HTML table contact form** — the same information sent as a web-page table
instead of plain text, which is what WPForms does. This one originally failed
completely and found nothing at all.

**3. Supplier newsletter** — an advert, not a customer. Must be binned silently.
This is where Bug A was caught.

## The awkward cases

**4. No labels at all** — *"Hi, I'm John. My kitchen sink is leaking. My number
is 555-402-8871."* No form, no labels, just a person talking. Proves the agent
can find a phone number and a name by their shape. Bug E was caught here.

**5. Customer replying in our own thread** — they wrote "Tuesday works", and the
whole old conversation is quoted underneath. The agent must recognise this as a
reply, not greet them as a stranger all over again.

**6. Forwarded enquiry** — the plumber's assistant passed a customer along. Bugs
C and F both lived here.

**7. Marketplace lead (early guess)** — written before we had real formats.
Kept because it still proves marketplace-style wording is read. **See the known
limitations below — this one is not fully trustworthy.**

**8. Colons inside the customer's own message** — the customer wrote *"Here's
the situation: Problem: burst pipe"*. Ordinary punctuation must not confuse it.

**9. Out-of-office auto-reply** — the most dangerous email on the list. If the
agent replies, two machines email each other in a loop and the client's business
domain gets flagged as a spammer. Must stay silent.

**10. Spam / phishing** — must be binned, not replied to and not put in the
review tray.

**11. Unknown extra form fields** — *"How did you hear about us?"*, *"Preferred
technician"*. Fields we've never seen must be ignored harmlessly. This is the
most common situation of all, because every form has surprises.

## The real-format cases

**12. Angi lead** — built from the actual Angi form. Uses their real question
wording (*"What plumbing do you need help with?"*, *"When do you need this work
done?"*) and splits the name into First Name and Last Name boxes. Proves the
agent produces "Michael Torres" and not just "Michael".

**13. Thumbtack lead** — built from the actual Thumbtack form. Phone number but
**no email**, because Thumbtack tells customers *"we don't share your email with
pros."* Also answers *"Is any part of the building currently flooded? Yes"* —
proving the agent raises an emergency alert instead of politely offering
Wednesday. It also captures which appliances are affected and the property type,
so the plumber packs the right parts.

**14. Google Local Services** — their email contains no customer details at all,
just a link to a dashboard. Proves the agent never bins a marketplace lead, even
when it can't read it — it flags it for a human instead.

**15. Squarespace form** — first and last name in separate boxes again, this
time from a different platform.

**16. Gravity Forms** — an HTML table where the label and the value sit side by
side in the same row, rather than stacked. Also a phone number written with dots
(408.555.7712) instead of dashes.

**17. Emergency in plain words** — *"this is Tom. My basement is flooding right
now."* No form, no emergency checkbox — proves the agent still raises the alarm.

**18. Routine job** — a quote for two bathroom faucets, next month. Proves the
agent does **not** cry emergency at everything. Without this test, an
over-eager alarm would look fine.

**19. Messy form** — stray spaces and SHOUTING labels. Proves formatting sloppiness
doesn't break it.

**20. Bounce message** — mail could not be delivered. Machine-generated, must
stay silent.

**21. Yelp quote request** — details locked inside Yelp's app. Same treatment as
Google: never binned, always flagged.

**22. Someone else's email inside the message** — the customer mentions their
landlord's address. Proves the agent replies to the customer, not the landlord.

**23. "my name is" mid-sentence** — a lower-case introduction buried in a
sentence, plus a sump pump job. Proves name-spotting isn't fragile.

**24. HTML using `&amp;`** — web pages write an ampersand oddly. Proves the
agent turns it back into "Drain & Sewer Cleaning" and doesn't show the customer
gibberish.

---

# Known limitations — the honest list

These are not bugs. They are things we know the agent cannot do yet.

**1. The old marketplace test (Test 7) is not trustworthy.** It was written
before we had real formats, and it currently treats Thumbtack's own address as
the customer's. Since Thumbtack hides customer emails, that reply may go nowhere.
**Resolved only by one real forwarded lead from a client.**

**2. A form field named literally "Subject" is ignored.** Squarespace allows
this. We deliberately ignore anything called "Subject" because the email's own
subject line caused Bug A. Losing an occasional form field is the safer trade.

**3. Emergency detection is deliberately aggressive.** A "burst pipe" now counts
as an emergency, which means more phone alerts and fewer automatic bookings. If
clients complain about being interrupted, this is the setting to loosen.

**4. Thumbtack and Google Local Services are weak fits.** Neither reliably gives
the agent a way to email the customer. For those, the agent is a fast alarm
bell, not an auto-responder. **Sell on the client's own website form first.**

**5. Nothing has touched a real inbox yet.** Every test above uses a written-out
sample email. The first real inbox will find something none of this did.

**6. The agent doesn't know the plumber's existing jobs.** It offers times that
fit his working hours and his notice period, but it cannot see what he has
already booked. Until the calendar is connected these are **proposals, not
guarantees** — so don't sell firm automatic booking yet.

**7. Ten of eighteen test leads had no email address**, so the plumber has to
phone them instead. That is the agent refusing to invent an address, which is
correct. But it means "every enquiry gets an instant reply" is not a promise you
can make — some get an instant phone alert instead.

**8. Odd window arithmetic is unchecked.** A client wanting 3-hour windows in a
9-to-5 day would quietly get two a day instead of three, because the last one
would run past closing. Nobody notices unless they count.

**9. Nobody finds out when a reply fails to arrive.** If a customer's mail
provider rejects or bounces our reply, the bounce lands back in the client's
inbox and the agent ignores it. From every angle it looks like the customer was
answered — the log says sent, the spreadsheet has a row — while the customer
heard nothing. **The fix:** watch for bounce-backs and turn one into a "CALL
THIS PERSON" alert, the same as an enquiry with no email address. Not built.
This is the highest-value item on this list, because it is the one failure the
plumber cannot see.

**10. Replies to forwarded enquiries carry no conversation stamp — correctly.**
When a customer emails direct, the reply is stamped as an answer to their own
message, which is a strong signal to their mail provider that they wanted it.
When the enquiry arrives forwarded, or from a website form, the only stamp
available belongs to somebody else's email, which the customer has never seen —
so the agent deliberately sends none. That is right (a stamp pointing at a
message not in their mailbox earns nothing and looks like a spammer trick), but
it does mean those replies rely on the ordinary signals alone: sent from the
client's own real mailbox, plain text, no links, low volume. Modest risk, not
zero.

**11. A client on their own domain needs mail records set up.** If the client
sends as `joe@joesplumbing.com` rather than a plain Gmail address, their domain
needs records proving Google is allowed to send on their behalf. Most small
businesses have never done this, and without it their replies are more likely to
be filtered. This is a client setup step, not code — **it belongs in the
README** when the README is written.

**Fixed since this list was first written:** public holidays, lunch breaks,
crashing on a bad settings file, mail the agent could not see (spam, and mail
already marked read), and replies not being attached to the customer's own
message. All now handled and tested.

---

# Where the output lives

**One file, overwritten every run:**

```
what-the-tests-checked/latest.txt
```

For every test — passing ones too — it shows the test name in plain English,
what was fed in, what was expected, and what actually came back. You never need
to open any code to understand a test.

The older `test-output/` folder is kept as history. The one worth keeping there
is `2026-08-11_reply-engine_BEFORE-fixes.txt` — that's what bugs G, H and J
actually looked like before they were fixed.

---

# The one thing this agent needs installed

Everything else uses only what comes with Python. The exception:

**`tzdata`** — the list of the world's timezones and when each one changes for
daylight saving. Windows doesn't ship it. Without it the agent cannot work out
what time it is where the client lives.

```
pip install tzdata
```

Free, about 600KB, pure data with no program code in it. **This must also be
installed wherever the agent runs for a real client.**

---

# The lesson worth keeping

Bugs B and F both **passed their tests** when they were written. They were only
caught because somebody read the actual output, line by line, and asked whether
each value was really correct.

A test only catches what you tell it to look at. So every time a bug is found,
the test that missed it gets tightened too — otherwise the same bug walks back
in later wearing a different hat.
