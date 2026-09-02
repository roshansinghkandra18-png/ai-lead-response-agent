# Test log — Speed-to-Lead agent

A running history of everything we have tested on this agent, what broke, and
what was done about it. Add to it every time something new gets tested.

Written in plain English on purpose. No code.

**To run the tests yourself:**

```
cd "agents/speed-to-lead"
python test_samples.py
```

**Current result: 24 tests, 24 passing.**

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

---

# The six bugs we found

Full detail with fixes is in `BUGS.md`. Summary:

| Bug | What it did | Found in |
|---|---|---|
| **A** | Replied to a supplier's junk-mail advert | The newsletter test |
| **B** | Addressed the reply to the website's own robot, so the customer never got it | Two tests that were **marked PASS** |
| **C** | Binned a customer that a colleague had forwarded | The forwarded enquiry test |
| **D** | Put spam in the "please check this" tray instead of the bin | The spam test |
| **E** | Didn't notice "Hi, I'm John" means his name is John | The no-labels test — **spotted by Roshan, not by the test** |
| **F** | Sent the customer's confirmation to the colleague who forwarded it | The forwarded test, *after* Bug C was fixed |

**Two of these six passed their tests at the time.** They surfaced only because
somebody read the output line by line and asked "is that actually right?"

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

---

# The lesson worth keeping

Bugs B and F both **passed their tests** when they were written. They were only
caught because somebody read the actual output, line by line, and asked whether
each value was really correct.

A test only catches what you tell it to look at. So every time a bug is found,
the test that missed it gets tightened too — otherwise the same bug walks back
in later wearing a different hat.
