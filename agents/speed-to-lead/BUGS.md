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

---

# Part two — the reply engine

Bugs A to F were all about the receptionist **reading** the mail. These four are
about the receptionist **writing the answer back**.

They were found the first time the reply engine ran, before it had sent anything
to anyone.

---

## Bug G — Wrote broken English

**Found in:** every single customer email it produced. The worst example was the
lead where somebody just typed a sentence with no form at all:

> *"Thanks for reaching out about leak."*

It should say **"about your leak."** The word "your" was missing everywhere:
*"about water heater repair"*, *"about shower"*, *"about sump pump"*.

**Cost if shipped:** a sentence that isn't English tells the customer instantly
that no human wrote it. The entire product depends on them believing one did.

**How it was fixed:** the sentence now supplies the word "your" itself.

**Status: fixed and tested.**

---

## Bug H — Said the same word twice in a subject line

**Found in:** the lead where Tom wrote *"my basement is flooding right now"*.

> *Subject: Re: your **your plumbing job** request*

The subject line is a fill-in-the-blank sentence — *"Re: your ___ request"* —
and the blank normally holds the job type. Tom's email had no form and no job
name we recognised, so the agent used a safe fallback phrase: *"your plumbing
job"*. That phrase already contained the word "your", so the sentence ended up
saying it twice. Like a letter addressed to *"Dear Mr. Mr. Smith"*.

**Cost if shipped:** on the most urgent email the agent will ever handle, the
subject line looked broken.

**How it was fixed:** two changes. The fallback phrase no longer contains the
word "your" — and, more importantly, see Bug I.

**Status: fixed and tested.**

---

## Bug I — Didn't know that flooding is a plumbing job

**Found in:** the same flooding lead. **Spotted by Roshan.**

The agent keeps a list of plumbing words so it can work out the job when a form
doesn't say — drain, toilet, water heater, burst pipe and so on.

**"Flooding" was not on that list.** Neither was gas leak, sewage, water damage,
frozen pipe, or no hot water. So on the single most urgent kind of email it
will ever receive, the agent had no idea what the job was and fell back to a
bland phrase.

**Cost if shipped:** the customer's emergency was described back to them as
"your plumbing job". Everything about that reply said *routine* when the
situation was anything but.

**How it was fixed:** the list now begins with the emergencies — gas leak,
sewage, water damage, frozen pipe, flooding, overflow, no hot water, no water —
before any of the ordinary jobs.

**Status: fixed and tested.**

---

## Bug J — Told the plumber to drop everything, without saying why

**Found in:** all three emergency leads.

Tom's basement is flooding. This is the entire message the plumber received:

```
EMERGENCY - CALL NOW
Name  : Tom
Phone : 312-555-9034
Job   : not stated
```

The agent had **read** the words "my basement is flooding right now". It simply
never passed them on. The plumber was being asked to walk off a paying job and
phone a stranger, while knowing less about the situation than the software did.

**Cost if shipped:** either he ignores the alert, or he abandons work on a
guess. Both are bad, and both are his software's fault.

**How it was fixed:** every alert now carries a "Said" line with the customer's
own words. As a side benefit, ordinary call-back alerts get it too, so the
plumber knows what somebody wants before he dials.

**Status: fixed and tested.**

---

---

## Bug K — Read the clock in the wrong country

**Found in:** nothing. No test caught this one. It was noticed while reviewing
what the agent still couldn't do.

The receptionist was looking at the clock on the wall **of our office in
India**, then writing appointment times as though it were the clock in the
customer's kitchen in Ohio. Those two clocks are nine and a half hours apart.

Two separate things went wrong because of it:

**Same-day jobs were being thrown away.** A customer in Ohio emails at 9am
hoping for someone that afternoon. In India it is already 6:30pm, so the
receptionist thinks the working day is over and replies *"tomorrow morning"* —
when the plumber had the whole afternoon free. That is the one thing this entire
product is sold on.

**Appointments were being offered in the past.** Early morning in India is the
previous evening in America. The receptionist would offer *"today at 10am"* — a
time that, for the customer, was already ten hours ago.

**Cost if shipped:** every single appointment time wrong, for every client,
forever. And it would not look broken — 2pm is a perfectly believable time.

**Why no test caught it:** every test used a pretend time like "Tuesday 10am".
Tuesday 10am **where?** Nobody had ever asked, so the mistake was invisible.

**How it was fixed:** each client's settings file now says where they are
(`timezone = America/New_York`). The receptionist works entirely on that clock
and ignores ours completely. New tests pretend the laptop is in India and check
the times still come out right for Ohio — and for a second client in Texas, an
hour behind, at the very same instant.

This needed one small download, `tzdata`, because Windows does not come with a
list of the world's timezones. It is the only thing this agent needs installed.

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
| Working out what time it is | Use the client's clock, never ours |
| A public holiday falls in the way | Skip it, and tell the customer why |
| The client takes a lunch break | Never offer a window that runs through it |

---

## The lesson worth keeping

Bugs B and F both **passed their tests** at the time. They only surfaced because
somebody looked at the output line by line and asked "is that actually right?"

A test only catches what you tell it to look at. Every time a bug is found, the
test that missed it gets tightened too — otherwise the same bug walks back in
later wearing a different hat.
