# Bugs found in the Speed-to-Lead agent

Think of the agent as **a new receptionist on their first day.** You hand them a
stack of mail and say: *"Reply to anyone who wants plumbing work. Ignore
everything else."*

These are the mistakes they made, what they should do instead, and what was
changed to stop each one happening again.

All six were found before the agent ever touched a real inbox.

---

## Bug A — Replied to a junk mail advert

**Found in:** the test with a supplier's newsletter, "August deals on copper fittings."

A supplier's advertising email arrived. The receptionist saw the word "plumbing"
printed somewhere on the page, decided it must be a customer, and wrote back
offering to fix their pipes.

**Should do instead:** bin it, silently.

**Cost if shipped:** your client's business address sends automated "thanks for
reaching out" replies to every supplier newsletter they receive.

**How it was fixed:** the receptionist now covers up the envelope before reading.
They only look at what the person actually typed, never the printed sender
details at the top. They also ignore website addresses when deciding what trade
a job is — so "plumbingsupply.com" no longer counts as somebody wanting
plumbing work.

**Status: fixed and tested.**

---

## Bug B — Wrote the reply to the wrong person

**Found in:** two tests that were originally marked PASS — Sarah Chen (colons in
her message) and Robert Lee (unfamiliar form fields).

Sarah filled in the website form. The receptionist read it correctly: her name,
her phone number, her burst pipe.

Then they addressed the envelope to **the website's own automatic mail system**
instead of to Sarah. Sarah never hears back. The letter goes into a drawer nobody
opens. And the receptionist writes in the logbook: *"Replied to Sarah — done."*

**Should do instead:** notice the form gave no email address for Sarah, and not
send anything to the website's robot address.

**Cost if shipped:** the worst of the six. Nothing errors. Nothing looks broken.
The client quietly gets no results and tells you your product doesn't work — and
your own logs say everything succeeded.

**How it was fixed:** the receptionist now recognises robot addresses on sight —
anything containing "noreply", "do-not-reply", "mailer-daemon" and similar — and
refuses to treat them as a customer. If that leaves no email address at all, they
say so plainly rather than inventing one.

**Status: fixed and tested.**

---

## Bug C — Binned a customer that a colleague passed along

**Found in:** the forwarded enquiry test — Dave Wilson, toilet installation.

The plumber's assistant passed a customer enquiry along. The receptionist saw a
note attached to the top, assumed the whole thing was old paperwork from last
week, and filed it away without reading it.

**Should do instead:** understand that a passed-along letter contains a *new*
customer, and read it.

**Cost if shipped:** forwarding is the easiest way for a first client to feed the
agent — they never have to touch their website settings. This breaks the simplest
onboarding path you have.

**How it was fixed:** the receptionist now tells the difference between two
things that used to look identical to them:

| Kind of letter | What sits underneath the note | What they do |
|---|---|---|
| A **reply** to us | Last week's conversation | Ignore it |
| A **forwarded** enquiry | A brand new customer | Read it |

**Status: fixed and tested.**

---

## Bug D — Put junk mail in the "ask the boss" tray

**Found in:** the spam / phishing test.

A phishing scam arrived. The receptionist didn't reply to it — that part was
right. But instead of binning it, they put it in the tray marked *"things I
wasn't sure about, please check."*

**Should do instead:** bin it.

**Cost if shipped:** that tray fills with rubbish, you stop looking in it, and
eventually a real customer sits in there unnoticed.

**How it was fixed:** the "please check" tray now has an entry requirement. A
genuine enquiry form fills in several boxes — name, phone, service, and so on.
Spam usually fills in one at most. If fewer than two real form boxes were filled
in and there's no sign of a plumbing job, it goes in the bin instead of the tray.

**Status: fixed and tested.**

---

## Bug E — Didn't notice the customer said their own name

**Found in:** the test where someone typed a message with no form fields at all.
**Spotted by Roshan, not by the test.**

A customer wrote: *"Hi, I'm John. My kitchen sink is leaking. My number is
555-402-8871."*

The receptionist got the phone number and understood it was a leak. But wrote
back **"Hi there"** — because nobody had printed the word *"Name:"* in front of
"John", so they didn't register it as a name.

**Should do instead:** understand that "I'm John" means his name is John.

**Cost if shipped:** small, but it's the exact moment a customer thinks *"nobody
actually read this."* The whole product depends on them believing a person
replied.

**How it was fixed:** the receptionist now recognises the ordinary ways people
introduce themselves — *"I'm John"*, *"I am John"*, *"my name is John"*, *"this
is John"* — and takes the name from there when the form didn't provide one.

**Status: fixed and tested.**

---

## Bug F — Sent the customer's confirmation to the colleague who forwarded it

**Found in:** the same forwarded enquiry test, *after* Bug C was fixed. The test
was passing at the time.

Once the receptionist learned to read forwarded letters, a subtler version of
Bug B appeared. Dave Wilson's form gave a phone number but no email address. So
the receptionist fell back on "whoever sent me this envelope" — and that was the
plumber's **assistant**, not Dave.

The assistant is a real person with a real mailbox, so the robot-address check
from Bug B didn't catch it. Dave's confirmation would have gone to a colleague,
and Dave would have heard nothing.

**Should do instead:** understand that on a forwarded letter, the person who sent
it is never the customer.

**Cost if shipped:** identical to Bug B — silent failure, confident logs, a
client who says the product doesn't work.

**How it was fixed:** the receptionist now checks whether a letter was passed
along before falling back to the sender. If it was forwarded, the sender is
ruled out as the customer entirely.

**Status: fixed and tested.**

---

## Agreed behaviour

| The situation | What the agent does |
|---|---|
| Junk mail advert arrives | Bin it, silently |
| Customer's own email address missing from the form | Don't send to the website robot — flag it instead |
| A colleague forwards an enquiry | Read it, treat as a new customer |
| Someone forwards it on the customer's behalf | Never reply to the forwarder |
| Spam arrives | Bin it, don't put it in the review tray |
| Customer writes "I'm John" | Call him John |

---

## The lesson worth keeping

Bugs B and F both **passed their tests** at the time. They only surfaced because
somebody looked at the output line by line and asked "is that actually right?"

A test only catches what you tell it to look at. Every time a bug is found, the
test that missed it gets tightened too — otherwise the same bug walks back in
later wearing a different hat.
