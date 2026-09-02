"""
parse_lead.py  --  the parsing engine for the Speed-to-Lead agent.

WHAT THIS DOES
    Takes the raw text of an email and decides three things:
      1. Is this actually a customer enquiry?
      2. If so, what are the facts (name, phone, job type, address, urgency)?
      3. If we're not sure, say so instead of guessing.

WHAT THIS DOES NOT DO
    Does not read an inbox, does not send anything, does not call any AI.
    Costs nothing to run.

TO TEST IT
    python test_samples.py
"""

import re
import html


# ---------------------------------------------------------------------------
# 1. THE LABEL DICTIONARY  --  the heart of the product.
#
# Every form names its fields differently. This maps all the variations we can
# anticipate onto the handful of facts we actually want.
#
# When a client's form uses a label that isn't here, you add it to the right
# list. One line. No other change needed anywhere.
# ---------------------------------------------------------------------------
FIELD_LABELS = {
    "name": [
        "name", "your name", "full name", "your full name",
        "please enter your full name", "customer name", "contact name",
        "client name", "homeowner", "homeowner name",
        # marketplace wordings (Angi / Thumbtack / HomeAdvisor style)
        "customer", "client", "requester", "submitted by", "lead name",
    ],
    # CHANGE 2: Angi and Squarespace split the name into two boxes. These are
    # kept separate and joined back together after parsing, so we get
    # "John Smith" instead of just "John".
    "first_name": [
        "first name", "your first name", "firstname", "given name",
        "your given name",
    ],
    "last_name": [
        "last name", "your last name", "lastname", "surname", "your surname",
        "family name", "your family name",
    ],
    "phone": [
        "phone", "your phone", "phone number", "phone no", "tel", "telephone",
        "mobile", "mobile number", "cell", "cell phone", "contact number",
        "contact phone", "best number", "best contact number", "primary phone",
        "daytime phone", "callback number", "call back number",
    ],
    "email": [
        "email", "your email", "e-mail", "email address", "e-mail address",
        "contact email", "customer email",
    ],
    "job_type": [
        "service", "services", "service type", "service needed",
        "services needed", "service requested", "type of service",
        "subject", "reason for contact", "how can we help", "job type",
        "what do you need", "work needed", "request type", "trade",
        # marketplace wordings
        "project", "project type", "category", "task", "job", "need",
        "i need help with", "type of work",
        # CHANGE 1: taken from the real Angi and Thumbtack forms
        "what plumbing do you need help with", "what do you need help with",
        "what needs to be installed or replaced", "what needs to be installed",
        "what can we help you with",
    ],
    "address": [
        "address", "service address", "street address", "property address",
        "job address", "service location", "location", "city", "city state",
        "area", "zip", "zipcode", "zip code", "postal code", "where",
        # CHANGE 1: real Angi wordings
        "what's your project address", "whats your project address",
        "project address", "project zip",
    ],
    "urgency": [
        "when do you need service", "when do you need this done", "when",
        "timeframe", "time frame", "urgency", "how soon", "start date",
        "preferred date", "desired date", "preferred time",
        "preferred contact time", "preferred schedule", "time preference",
        "availability",
        # marketplace wordings
        "requested", "requested date", "timing",
        # CHANGE 1: real Angi and Thumbtack wordings
        "when do you need this work done", "when do you need this job to start",
        "when do you need it done", "when would you like this done",
    ],
    "message": [
        "message", "your message", "details", "detail", "comments", "comment",
        "describe the problem", "description", "job description",
        "additional information", "additional details", "more information",
        "tell us more", "notes", "project details", "details of request",
        "issue", "problem description",
        # CHANGE 1: real Angi and Thumbtack wordings
        "please tell us a little about your project",
        "tell us a little about your project", "tell us about your project",
        "send a message to the pro", "message to the pro",
        "project description",
    ],

    # CHANGE 4: extra context. The agent never acts on these, but passing them
    # to the plumber means he arrives with the right parts.
    "property_type": [
        "what type of property do you have", "what kind of location is this",
        "property type", "location type", "type of property",
    ],
    "appliances": [
        "which appliances if any are affected", "which appliances are affected",
        "appliances affected", "appliances",
    ],

    # CHANGE 3: a direct yes/no emergency question. Certainty, not guesswork.
    "flooded": [
        "is any part of the building currently flooded",
        "is any part of the property currently flooded",
        "is anything flooded", "is the property flooded",
    ],
}


# An email's own envelope uses "Label: value" exactly like a form field does.
# Without this, the parser reads the email's Subject and calls it the job type.
EMAIL_HEADERS = {
    "from", "to", "cc", "bcc", "subject", "date", "sent", "reply-to",
    "return-path", "message-id", "mime-version", "content-type",
    "content-transfer-encoding", "x-mailer", "delivered-to", "received",
    "auto-submitted", "precedence", "x-autoreply", "importance",
}


# BUG B FIX: addresses that are machines, not people. Replying to one of these
# means the customer never hears anything and the message dies in a mailbox
# nobody reads.
NOREPLY_HINTS = (
    "noreply", "no-reply", "no_reply", "donotreply", "do-not-reply",
    "mailer-daemon", "postmaster", "bounce",
)


# Lead marketplaces. An email from one of these is ALWAYS about a real customer,
# even when we can't read the details -- so it must never be binned as junk.
# Google Local Services in particular sends only a link to their dashboard.
LEAD_SOURCE_DOMAINS = (
    "thumbtack.com", "angi.com", "angieslist.com", "homeadvisor.com",
    "porch.com", "networx.com", "yelp.com", "houzz.com", "bark.com",
    "localservicesads.google.com", "localservices.google.com",
)


# CHANGE 3: words that mean "do not politely offer Wednesday". When any of these
# appear, the agent alerts the plumber to call instead of trying to book.
#
# Split in two, 15 August 2026, after a routine drain cleaning was declared an
# emergency. The difference is whether the word describes a THING HAPPENING or
# only a FEELING.
#
# Strong words name the thing. Nobody writes "gushing" or "gas leak" casually.
STRONG_EMERGENCY_WORDS = (
    "emergency", "flood", "flooding", "flooded", "burst", "gushing",
    "no water", "gas leak", "sewage", "overflowing",
)

# Weak words are a feeling, and they turn up in marketing copy, form templates
# and ordinary polite requests all day long. They still count - but they can be
# argued with, which is why "not urgent at all" must never mean urgent.
WEAK_EMERGENCY_WORDS = ("urgent", "asap", "right now", "immediately")

EMERGENCY_WORDS = STRONG_EMERGENCY_WORDS + WEAK_EMERGENCY_WORDS

# "Not urgent at all, just whenever you have a free slot next month" is a
# customer going out of their way to say the opposite.
NOT_REALLY = re.compile(r"\b(?:not|no|never|isn't|isnt|nothing|non)\b")


# If any of these appear in the subject line, a machine sent it, not a person.
# Replying can start an endless loop between two mail servers, which gets the
# client's real business domain flagged as a spammer.
AUTO_REPLY_SUBJECTS = [
    "automatic reply", "auto-reply", "autoreply", "auto reply",
    "out of office", "out of the office", "vacation response",
    "away from my desk", "undeliverable", "delivery status notification",
    "mail delivery failed", "returned mail", "delivery failure",
]

AUTO_REPLY_HEADERS = ["auto-submitted", "x-autoreply", "x-auto-response-suppress"]


# BUG C FIX: these two used to be one list, which is why forwarded enquiries got
# binned. They mean OPPOSITE things:
#   a REPLY  -> the old conversation sits BELOW the marker, so cut it off
#   a FORWARD-> the real new customer sits BELOW the marker, so keep reading
REPLY_MARKERS = [
    r"^On .{4,120}\bwrote:\s*$",
    r"^-{2,}\s*Original Message\s*-{2,}",
    r"^_{10,}\s*$",
    r"^From:.*\bSent:",
]

FORWARD_MARKERS = [
    r"^-{2,}\s*Forwarded message\s*-{2,}",
    r"^Begin forwarded message:",
]


# Words that tell us what trade the job is, when the form gave us no job field.
# Longest phrases first so "water heater" wins over "water".
TRADE_KEYWORDS = [
    # Emergencies first. These used to be missing entirely, so "my basement is
    # flooding" produced no job type at all and the agent fell back to a bland
    # phrase -- on the most urgent email it will ever receive.
    ("gas leak", "Gas Leak"),
    ("sewage backup", "Sewage Backup"),
    ("sewage", "Sewage"),
    ("water damage", "Water Damage"),
    ("frozen pipe", "Frozen Pipe"),
    ("flooding", "Flooding"),
    ("flooded", "Flooding"),
    ("flood", "Flooding"),
    ("overflowing", "Overflow"),
    ("overflow", "Overflow"),
    ("no hot water", "No Hot Water"),
    ("no water", "No Water"),
    ("water heater", "Water Heater"),
    ("hot water", "Water Heater"),
    ("garbage disposal", "Garbage Disposal"),
    ("sump pump", "Sump Pump"),
    ("air conditioning", "Air Conditioning"),
    ("septic", "Septic"),
    ("sewer", "Sewer"),
    ("water softener", "Water Softener"),
    ("water pressure", "Water Pressure"),
    ("low pressure", "Water Pressure"),
    ("no pressure", "Water Pressure"),
    ("washing machine", "Washing Machine"),
    ("dishwasher", "Dishwasher"),
    ("furnace", "Heating"),
    ("boiler", "Boiler"),
    ("radiator", "Heating"),
    ("toilet", "Toilet"),
    ("cistern", "Toilet"),
    ("faucet", "Faucet"),
    # Added 15 August 2026. Louise wrote "the bathroom tap has been dripping"
    # and got back "your plumbing job", because the word list was built from
    # American plumbing vocabulary and she used the British word. Americans
    # say faucet, but plenty of them say tap too - and the reply says
    # "faucet" either way, because the client is American.
    ("tap", "Faucet"),
    ("spigot", "Faucet"),
    ("shower", "Shower"),
    ("bathtub", "Bathtub"),
    ("basin", "Sink"),
    ("drain", "Drain Cleaning"),
    ("clog", "Drain Cleaning"),
    ("blocked", "Drain Cleaning"),
    ("gurgl", "Drain Cleaning"),
    ("backflow", "Backflow"),
    ("burst", "Burst Pipe"),
    ("pipe", "Pipe Repair"),
    ("valve", "Valve"),
    ("leak", "Leak"),
    ("drip", "Leak"),
    ("sink", "Sink"),
    ("plumb", "Plumbing"),
]

# Endings a customer will add to any of those words. "leaking", "clogged" and
# "drips" all have to find "leak", "clog" and "drip".
TRADE_ENDINGS = r"(?:s|es|ed|ing|ged|ging|ping|pping)?"


# BUG E FIX: ways a person introduces themselves when no form field exists.
# The (?i:...) part makes only the opening words case-insensitive, so "My name
# is" and "my name is" both match -- while the name itself must still start
# with a capital letter, which is what stops it grabbing ordinary words.
NAME_PATTERNS = [
    r"(?i:\bmy name(?:'s| is))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    r"(?i:\bi'?m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    r"(?i:\bi am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    r"(?i:\bthis is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
]


# Statuses the parser can return. The agent acts on these.
LEAD = "LEAD"                      # reply to this
SKIP_AUTO_REPLY = "SKIP_AUTO"      # a machine sent it - never reply
SKIP_NOT_A_LEAD = "SKIP_NOT_LEAD"  # newsletter, spam, noise - bin it
THREAD_REPLY = "THREAD_REPLY"      # customer replying to us - booking flow
NEEDS_REVIEW = "NEEDS_REVIEW"      # a real form we couldn't fully read


def normalize(text):
    """
    Reduce a label to a plain comparable form so small differences don't matter.

        "Phone (we'll call you back ASAP):"  ->  "phone"
        "When do you need service?"          ->  "when do you need service"
    """
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


LABEL_LOOKUP = {}
for field_name, variations in FIELD_LABELS.items():
    for variation in variations:
        LABEL_LOOKUP[normalize(variation)] = field_name


def get_subject(raw):
    """Pull the Subject line out of the envelope, or return an empty string."""
    match = re.search(r"^subject:\s*(.+)$", raw, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def sender_address(raw):
    """The address in the From: line. Sometimes this IS the customer (they
    emailed directly); sometimes it's a website robot (see NOREPLY_HINTS)."""
    match = re.search(r"^from:\s*.*?([\w.+-]+@[\w-]+\.[\w.-]{2,})",
                      raw, re.IGNORECASE | re.MULTILINE)
    return match.group(1) if match else None


def is_machine_address(address):
    """True if replying to this address means nobody will ever read it."""
    if not address:
        return False
    return any(hint in address.lower() for hint in NOREPLY_HINTS)


def is_auto_reply(raw):
    """True if a machine sent this. The most damaging thing we could reply to."""
    subject = get_subject(raw).lower()
    if any(marker in subject for marker in AUTO_REPLY_SUBJECTS):
        return True
    lowered = raw.lower()
    return any(f"\n{h}:" in lowered or lowered.startswith(f"{h}:")
               for h in AUTO_REPLY_HEADERS)


def is_thread_reply(raw):
    """True if the customer is replying inside a conversation we started."""
    subject = get_subject(raw).lower()
    if subject.startswith("re:"):
        return True
    return any(re.search(p, raw, re.MULTILINE | re.IGNORECASE)
               for p in REPLY_MARKERS)


def is_forwarded(raw):
    """
    True if somebody passed this along rather than sending it themselves.
    BUG F FIX: when an email is forwarded, the From: address belongs to the
    person who forwarded it - never to the customer inside.
    """
    subject = get_subject(raw).lower()
    if subject.startswith("fwd:") or subject.startswith("fw:"):
        return True
    return any(re.search(p, raw, re.MULTILINE | re.IGNORECASE)
               for p in FORWARD_MARKERS)


def strip_quoted_reply(text):
    """Keep only what the sender actually wrote this time."""
    # A forward: the real enquiry is BELOW the marker, so keep that part.
    for pattern in FORWARD_MARKERS:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            text = text[match.end():]
            break

    # A reply: old history is BELOW the marker, so cut it off.
    earliest = len(text)
    for pattern in REPLY_MARKERS:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match and match.start() < earliest:
            earliest = match.start()
    text = text[:earliest]

    # Lines the mail client prefixed with ">" are quoted too.
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith(">"))


# A sign-off on a line of its own means the message has ended and the
# boilerplate has begun. Everything below is a signature block: job title,
# switchboard, fax, website - the same on every email this person ever sends,
# whether they are ordering stationery or reporting a leak.
SIGN_OFFS = re.compile(
    r"^\s*(?:thanks|thank you|many thanks|thanks again|regards|"
    r"kind regards|best regards|warm regards|best wishes|best|"
    r"sincerely|yours sincerely|yours faithfully|cheers|"
    r"all the best|speak soon)\s*[,.!]?\s*$",
    re.IGNORECASE)


def strip_signature(text):
    """
    Everything the customer actually wrote, without the boilerplate underneath.

    Barbara wrote "Best number for me is 216-555-0644" and then signed off. Her
    signature carries the office switchboard. Read together, the switchboard
    wins on a technicality - it is the one with the word "Tel" in front of it.
    Read apart, the number she actually gave is the only one there.

    Cutting at a sign-off ON ITS OWN LINE. "thank you." at the end of a long
    sentence is not a sign-off, and must not chop the sentence in half.

    NOTE: this is deliberately used as a FIRST look, not the only look. Plenty
    of people put their only phone number under "Thanks, John" - so anything
    still missing afterwards is hunted for again in the full text, signature
    included. Preferred, not exclusive.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if SIGN_OFFS.match(line):
            return "\n".join(lines[:i])
    return text


def html_to_text(raw):
    """
    Many form plugins (WPForms especially) send HTML tables, not plain text.
    Turn row/cell/break tags into newlines BEFORE deleting the rest, or the
    label and its value get mashed onto one line.
    """
    if "<" not in raw:
        return raw
    text = re.sub(r"(?i)<\s*(br|/p|/div|/tr|/td|/th|/li|/h[1-6])[^>]*>", "\n", raw)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def body_only(text):
    """
    BUG A FIX: drop the envelope lines (From:, Subject:, Date:...) so that
    pattern-hunting only ever sees what a human actually typed. Without this,
    "the first email address in the message" is always the sender.

    A header that is too long to fit on one line gets FOLDED - continued on
    the next line, indented by a space. Those continuation lines carry no
    label, so dropping only the labelled line left the rest of the header
    sitting in the message looking exactly like something the customer wrote.
    """
    kept = []
    after_header = False
    for line in text.splitlines():
        if ":" in line and normalize(line.partition(":")[0]) in EMAIL_HEADERS:
            after_header = True
            continue
        if after_header and line.strip() and line[:1] in (" ", "\t"):
            continue                      # folded continuation of that header
        after_header = False
        kept.append(line)
    return "\n".join(kept)


# An invisible mark meaning "a new form field starts here". Never shown to
# anybody - it exists so the agent can tell a wrapped line apart from the edge
# of a box. A mail program wraps a long sentence wherever it likes, so a line
# break inside a message means nothing; a line break between two form fields
# means everything.
FIELD_EDGE = "\x00"


def customer_words(text):
    """
    Only what the CUSTOMER actually wrote - never the questions the form asked.

    Thumbtack prints this on every lead it ever sends:

        Is any part of the building currently flooded?: No

    Denise answered No. She had a dripping bathroom faucet. But the word
    "flooded" is sitting there in the QUESTION, so a hunt for emergency words
    found it, declared an emergency, told the plumber to drop everything and
    call - and refused her the appointment times she should have been offered.

    A form label is boilerplate. It is identical on every submission whether
    the customer is standing in six inches of water or asking about a tap. It
    can never be evidence about THIS customer. Her answer can.

    The separate, certain check is untouched: a form that asks whether the
    building is flooded and gets "Yes" is still an emergency, and always was.
    """
    kept = []
    for line in body_only(text).splitlines():
        if ":" in line:
            label, _, value = line.partition(":")
            # A known field, or anything phrased as a question - both are the
            # form talking, not the customer.
            if normalize(label) in LABEL_LOOKUP or label.rstrip().endswith("?"):
                # Marked as the start of its own box. A form field is a box,
                # and a sentence cannot start in one box and finish in another
                # - the note explaining Ian's second phone number ran
                # backwards out of the message, swept up the tail of his email
                # address and the words "Leak Detection", and read
                # "com Leak Detection Call my mobile 216-555-0801...".
                kept.append(FIELD_EDGE + value)
                continue
        kept.append(line)
    return "\n".join(kept)


PHONE_SHAPE = r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"

# Words that mean the number about to follow belongs to SOMEBODY ELSE.
#
# NOT a reason to throw the number away. A husband emailing about a leak while
# his wife is at work, and giving her number, is one of the most ordinary
# things in home services. What matters is that the plumber KNOWS whose number
# he is dialling - ringing Sarah while expecting Greg sounds like a cold call;
# ringing Sarah knowing she is Greg's wife is a completely different
# conversation.
SOMEONE_ELSE = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+"
    r"(wife|husband|partner|girlfriend|boyfriend|son|daughter|mother|mum|mom|"
    r"father|dad|landlord|landlady|tenant|roommate|flatmate|housemate|"
    r"neighbour|neighbor|boss|manager|assistant|secretary|office|work|"
    r"company|employer|agent|realtor|property manager|building manager|"
    r"caretaker|super|superintendent)"
    r"(?:'s|s')?\b", re.IGNORECASE)


def _sentence_around(text, position):
    """
    The customer's own sentence containing a given point in the text.

    "Call my landlord if you come after 2, he'll let you in" is worth as much
    to the plumber as the number itself. Summarising it would lose exactly the
    part he needs on the day, so it is quoted back to him whole.

    A single line break is NOT a sentence ending. Mail clients wrap long lines
    wherever they like, and treating a wrap as a full stop chopped Rita's
    instruction in half. Only a blank line ends a passage.
    """
    # Same length, so every position still lines up - only the boundaries move.
    flat = text.replace("\n\n", "\x00\x00").replace("\n", " ")
    starts = [flat.rfind(c, 0, position) for c in (".", "!", "?", "\x00")]
    start = max(starts)
    start = 0 if start < 0 else start + 1
    ends = [e for e in (flat.find(c, position) for c in (".", "!", "?", "\x00"))
            if e != -1]
    end = min(ends) + 1 if ends else len(flat)
    sentence = " ".join(flat[start:end].replace("\x00", " ").split()).strip()
    return sentence[:200]


def _digits(number):
    return re.sub(r"\D", "", number)


def find_numbers(text):
    """
    Every phone number in the message, each tagged with whose it is.

    Returns a list of (number, whose, sentence). `whose` is None when the
    number belongs to the person writing - the ordinary case.

    Whose it is, is decided by the words between THIS number and the one
    before it. A fixed window of characters was not enough: "call me on
    216-555-0311 if you come by 2, or else my landlord will open the door to
    you, he is on 216-555-0912" has the owner of the second number mentioned
    far too early for a short lookback, and the owner of the FIRST number
    would be wrong if the whole sentence were searched.
    """
    numbers = []
    seen = set()
    previous_end = 0
    for match in re.finditer(PHONE_SHAPE, text):
        lead_in = text[previous_end:match.start()]
        # Don't look back past the start of the passage either.
        break_at = max(lead_in.rfind("."), lead_in.rfind("!"),
                       lead_in.rfind("?"), lead_in.rfind("\n\n"),
                       lead_in.rfind(FIELD_EDGE))
        if break_at != -1:
            lead_in = lead_in[break_at + 1:]

        owner = SOMEONE_ELSE.findall(lead_in)
        previous_end = match.end()

        number = match.group(0).strip()
        if _digits(number) in seen:
            continue
        seen.add(_digits(number))

        numbers.append((
            number,
            owner[-1].lower() if owner else None,
            _sentence_around(text, match.start()),
        ))
    return numbers


# Bold and italic, as they arrive in the plain-text copy of an email.
#
# Gmail sends every formatted message TWICE - once as a web page and once as
# plain text - and in the plain-text copy it writes bold as *asterisks* and
# italic as _underscores_. We read the plain-text copy, so those marks arrive
# as though they were letters. That is how a customer got greeted as
# "Hi *Marcus," and how his phone number was filed as "* (216) 555-0700".
EMPHASIS = re.compile(r"(?<!\w)([*_~]{1,3})(\S(?:.*?\S)?)\1(?!\w)")


def unformat(text):
    """
    Take the words and leave the decoration behind, across a whole message.

    Done BEFORE anything is looked for, not after. "Hi, I'm *Marcus*" has to be
    cleaned first or the search for a name finds nothing at all - it is looking
    for a capital letter after "I'm", and an asterisk is not one.

    An email address is safe from this. The pattern only matches a mark that
    starts at a non-letter, so the underscore inside jose_ramirez@example.com
    is never touched.
    """
    return EMPHASIS.sub(r"\2", text) if text else text


# What a name is actually made of: letters from any language, spaces, and the
# punctuation that lives inside real names - O'Brien, Mary-Anne, Nolan Jr.
#
# Accented letters count as letters, so Jose Ramirez keeps his accents. Emoji
# and symbols do not, so a customer decorating the form does not put a smiley
# face in the plumber's spreadsheet next to her name.
NOT_NAME_EDGE = re.compile(r"^[^\w'’.-]+|[^\w'’.-]+$", re.UNICODE)


# Emoji and pictographs, wherever they appear.
#
# Roshan's decision, 15 August 2026: the agent is a professional service, so
# nothing it hands the plumber should have smiley faces in it - not the name,
# not the message, not the alert. The cost is real and accepted: a crying face
# after "the ceiling is dripping" did tell the plumber something about how
# frightened the customer was. The words still do.
#
# Deliberately does NOT touch accented letters, currency, dashes or ordinary
# punctuation - only the pictures.
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF"      # emoji, pictographs, symbols, flags
    "\U00002600-\U000027BF"       # weather, zodiac, dingbats
    "\U00002B00-\U00002BFF"       # arrows and stars
    "\U00002300-\U000023FF"       # watches, hourglasses, media buttons
    "\U0001F1E6-\U0001F1FF"       # regional indicators
    "️‍⃣]+",       # the invisible joiners that glue them up
    re.UNICODE)


def strip_emoji(text):
    """Take the pictures out and tidy up the gap they leave behind."""
    if not text:
        return text
    cleaned = EMOJI.sub("", text)
    # "Chloe Barnett  " and "help  ." - the emoji is gone but its spacing isn't.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return re.sub(r" +([.,!?])", r"\1", cleaned)


# Words that are SUPPOSED to be shouted. Without these, calming down a
# capitalised form would turn "HVAC REPAIR" into "Hvac Repair" - and Maria's
# whole business is HVAC.
ACRONYMS = {"HVAC", "AC", "PVC", "CPVC", "ABS", "GFCI", "PEX", "TV", "USA",
            "US", "UV", "RO", "LP", "BBQ", "ADA", "II", "III", "IV"}


def calm_down(value):
    """
    Take a value that is entirely in capitals and give it normal capitals.

    Walter had caps lock on. The agent copied his shouting straight back at
    him - "Hi WALTER," - and filed him in the plumber's spreadsheet as "WALTER
    KIM" doing a "SEWER LINE INSPECTION". Nothing was mis-read; it just looked
    like being yelled at by a machine, on the first contact a customer ever
    has with the business.

    ONLY when the value is entirely capitals. A name that already has small
    letters in it is left exactly alone, so nothing normal is ever "corrected".
    """
    if not value or any(c.islower() for c in value):
        return value

    calmed = value.title()
    # title() would flatten the acronyms too, so put them back.
    return " ".join(
        word.upper() if word.upper() in ACRONYMS else word
        for word in calmed.split(" "))


def tidy_name(value):
    """
    Trim decoration off the ends of a name, and nothing else.

    Only the ENDS, and only for names. If a customer writes "the ceiling is
    dripping please help" with a crying face after it, the plumber should see
    that - her panic is information he can act on. It is her NAME that has to
    look like a name.
    """
    if not value:
        return value
    cleaned = NOT_NAME_EDGE.sub("", value).strip()
    return cleaned or value


def strip_formatting(value):
    """
    The same, for a single value, plus any mark left stranded on the ends
    where its partner didn't survive: "*Marcus Webb" as well as "*Marcus Webb*".
    """
    if not value:
        return value
    return unformat(value).strip("*_~` \t")


EMAIL_SHAPE = r"[\w.+-]+@[\w-]+\.[\w.-]{2,}"


def just_the_address(value):
    """
    Keep the email address and throw the packaging away.

    Formatting marks are deliberately NOT stripped from this field - an
    underscore is an ordinary character inside a real address, and removing it
    would break the one thing the whole reply depends on. So instead of
    cleaning the value, we find the address inside it.

    Gmail sent "*m.webb@example.com *" for an address that had been made bold.
    Taking the value whole meant writing to an address that does not exist, and
    the reply would have bounced - while the log said sent.
    """
    if not value:
        return value
    match = re.search(EMAIL_SHAPE, value)
    return match.group(0).strip() if match else value


def just_the_number(value):
    """
    Keep the phone number and throw the rest of the line away.

    A signature line reads "Tel: 216-555-9000  |  Fax: 216-555-9001". Taking
    everything after "Tel:" put that whole string into the plumber's phone
    column - a field with the word "Fax" in it that nobody could dial.
    """
    if not value:
        return value
    match = re.search(PHONE_SHAPE, value)
    return match.group(0).strip() if match else value


def find_by_pattern(text):
    """
    Fallback for forms with no labels at all - just a person typing a sentence.
    A phone number, an email address and a self-introduction all have a
    recognisable SHAPE, so we can find them even when nothing is labelled.
    """
    result = {"name": None, "phone": None, "email": None, "job_type": None,
              "phone_belongs_to": None, "phone_said": None,
              "other_phone": None, "other_phone_note": None,
              "other_phone_said": None}
    # The same rule as emergencies: the form's own questions are not evidence.
    # Denise's job came back as "Flooding" from that same Thumbtack question.
    text = customer_words(text)

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}", text)
    if email_match and not is_machine_address(email_match.group(0)):
        result["email"] = email_match.group(0)

    # The customer's own number is the one to ring first. A number they have
    # named somebody else for is kept too, but as a SECOND contact, labelled
    # with whose it is and why they mentioned it.
    numbers = find_numbers(text)
    own = [n for n in numbers if n[1] is None]
    others = [n for n in numbers if n[1] is not None]

    if own:
        result["phone"] = own[0][0]
        if others:
            result["other_phone"] = others[0][0]
            result["other_phone_note"] = f"their {others[0][1]}"
            result["other_phone_said"] = others[0][2]
        elif len(own) > 1:
            # Two numbers, neither pinned to anybody else - "call me on X, or
            # try Y". Both are the customer's, so hand the plumber both rather
            # than quietly dropping one.
            result["other_phone"] = own[1][0]
            result["other_phone_note"] = "also given"
            result["other_phone_said"] = own[1][2]
    elif others:
        # No number of their own. The person they named IS the way to reach
        # them - a husband emailing while his wife is at work, say. Use it,
        # but never let the plumber think it is the customer's own line.
        result["phone"] = others[0][0]
        result["phone_belongs_to"] = f"their {others[0][1]}"
        result["phone_said"] = others[0][2]

    for pattern in NAME_PATTERNS:
        name_match = re.search(pattern, text)
        if name_match:
            result["name"] = name_match.group(1).strip()
            break

    # BUG A FIX: strip out addresses and web links before hunting for trade
    # words, so "plumbingsupply.com" can't be mistaken for a plumbing job.
    scan = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}", " ", text)
    scan = re.sub(r"https?://\S+|www\.\S+|\b[\w-]+\.(com|net|org|biz|co)\b", " ", scan)
    scan = scan.lower()
    # Matched as whole words, not as letters buried inside other words. Plain
    # substring matching was fine while every word was long, but "tap" would
    # have found "tape", "tapping" and "adaptor", and turned a dictation about
    # sticky tape into a plumbing job.
    for keyword, label in TRADE_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + TRADE_ENDINGS + r"\b", scan):
            result["job_type"] = label
            break

    return result


def is_lead_source(raw):
    """True if a lead marketplace sent this (Angi, Thumbtack, Google, ...)."""
    sender = (sender_address(raw) or "").lower()
    body = raw.lower()
    return any(d in sender or d in body for d in LEAD_SOURCE_DOMAINS)


def detect_emergency(text, found):
    """
    CHANGE 3: decide whether this needs a phone call right now instead of a
    polite offer of Wednesday.

    A form that asks "is any part of the building currently flooded?" and gets
    "Yes" is certainty. Everything else is word-spotting, which is a guess.
    """
    flooded = (found.get("flooded") or "").strip().lower()
    if flooded.startswith(("yes", "y ")) or flooded == "y":
        return True

    lowered = customer_words(text).lower()

    if any(word in lowered for word in STRONG_EMERGENCY_WORDS):
        return True

    # A weak word only counts if the customer wasn't talking it DOWN.
    for word in WEAK_EMERGENCY_WORDS:
        for match in re.finditer(re.escape(word), lowered):
            before = lowered[max(0, match.start() - 30):match.start()]
            if NOT_REALLY.search(before):
                continue
            return True
    return False


def extract_fields(text):
    """Walk the email line by line and pull out every labelled field we know."""
    lines = [line.strip() for line in text.splitlines()]
    found = {field: None for field in FIELD_LABELS}

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        # --- Layout A: "Label: value" on one line ---
        if ":" in line:
            label_part, _, value_part = line.partition(":")

            if normalize(label_part) in EMAIL_HEADERS:
                i += 1
                continue

            field = LABEL_LOOKUP.get(normalize(label_part))
            if field:
                value = value_part.strip()

                # A message often continues on the lines below its label.
                if field == "message":
                    collected = [value] if value else []
                    j = i + 1
                    while j < len(lines):
                        ahead = lines[j].partition(":")[0] if ":" in lines[j] else lines[j]
                        if normalize(ahead) in LABEL_LOOKUP:
                            break
                        collected.append(lines[j])
                        j += 1
                    value = "\n".join(collected).strip()
                    i = j
                    if value and found[field] is None:
                        found[field] = value
                    continue

                if field == "email":
                    value = just_the_address(value)
                else:
                    value = strip_formatting(value)
                if field == "phone":
                    value = just_the_number(value)

                if value and found[field] is None:
                    found[field] = value
                i += 1
                continue

        # --- Layout B: label alone, value on a line below (HTML emails) ---
        field = LABEL_LOOKUP.get(normalize(line))
        if field:
            j = i + 1
            while j < len(lines) and not lines[j]:
                j += 1
            if j < len(lines):
                value = lines[j].strip()
                if field == "email":
                    value = just_the_address(value)
                else:
                    value = strip_formatting(value)
                if field == "phone":
                    value = just_the_number(value)
                if value and normalize(value) not in LABEL_LOOKUP:
                    if found[field] is None:
                        found[field] = value
                    i = j + 1
                    continue

        i += 1

    return found


def parse_email(raw):
    """
    The main entry point. Returns the facts we found plus a `status` saying
    what the agent should do about this email.
    """
    if is_auto_reply(raw):
        return {"status": SKIP_AUTO_REPLY, "reason": "machine-generated message"}

    if is_thread_reply(raw):
        return {"status": THREAD_REPLY,
                "reason": "reply inside an existing conversation"}

    text = html_to_text(raw)
    text = strip_quoted_reply(text)
    text = unformat(text)
    text = strip_emoji(text)

    # WHERE A FACT CAME FROM DECIDES HOW MUCH IT IS WORTH.
    #
    # `core` is what the customer actually typed. Everything below their
    # sign-off is boilerplate that rides on every email they ever send, whether
    # they are ordering stationery or reporting a leak.
    #
    # Barbara wrote "Best number for me is 216-555-0644" and her signature
    # carried "Tel: 216-555-9000" - the office switchboard. Read together the
    # switchboard wins on a technicality, because it has the word "Tel" in
    # front of it. So they are read apart, best source first:
    #
    #   1. labelled in the message      ("Phone: 216-555-0455")
    #   2. recognised in the message    ("my number is 216-555-0455")
    #   3. labelled in the signature    ("Tel: 216-555-9000")
    #   4. recognised in the signature  (a bare number under "Thanks, John")
    #
    # Steps 3 and 4 still happen. Preferring the message must never mean
    # losing the only contact details in the email.
    core = strip_signature(text)
    has_signature = core != text

    labelled = extract_fields(core)
    sources = [labelled, find_by_pattern(core)]
    if has_signature:
        signature_labelled = extract_fields(text)
        sources.append(signature_labelled)
        # A signature can supply a phone number of last resort, but it must
        # never supply a SECOND contact. A switchboard sitting in boilerplate
        # is not the customer offering the plumber another way to reach them,
        # and dressing it up as one puts a stranger's line in front of him
        # with a scrap of the footer quoted underneath as if she had said it.
        from_signature = find_by_pattern(text)
        for key in ("phone_belongs_to", "phone_said", "other_phone",
                    "other_phone_note", "other_phone_said"):
            from_signature[key] = None
        sources.append(from_signature)

    found = {field: None for field in FIELD_LABELS}
    for source in sources:
        for field, value in source.items():
            if found.get(field) is None and value:
                found[field] = value

    # CHANGE 2: Angi and Squarespace put the name in two separate boxes. Join
    # them, or the reply says "Hi John" when his name is John Smith.
    if not found["name"]:
        parts = [found["first_name"], found["last_name"]]
        joined = " ".join(p for p in parts if p).strip()
        if joined:
            found["name"] = joined

    # Done last, so they catch the value whichever way it was found.
    found["name"] = calm_down(tidy_name(found["name"]))
    found["job_type"] = calm_down(found["job_type"])

    # How many real LABELLED fields did the form give us? A genuine enquiry
    # form has several. Spam usually has one at most. (BUG D FIX uses this.)
    # Counted from labels only - a phone number spotted by its shape in a
    # scam email is not evidence that a human filled in a form.
    label_sources = [labelled] + ([signature_labelled] if has_signature else [])
    labelled_count = sum(
        1 for f in FIELD_LABELS
        if any(source.get(f) for source in label_sources))

    # Last resort for an email address: the sender themselves - but only when
    # the sender could plausibly BE the customer.
    #   BUG B FIX: not if it's a robot address nobody reads.
    #   BUG F FIX: not if the email was forwarded - that's the forwarder.
    if found["email"] is None and not is_forwarded(raw):
        candidate = sender_address(raw)
        if candidate and not is_machine_address(candidate):
            found["email"] = candidate

    has_contact = bool(found["phone"] or found["email"])
    has_context = bool(found["job_type"] or found["message"] or found["name"])

    # When somebody just types a sentence with no form fields at all, their
    # whole email IS the message. Without this the plumber gets an emergency
    # alert with no idea what the emergency is.
    if found["message"] is None and labelled_count == 0:
        typed = " ".join(line.strip() for line in body_only(text).splitlines()
                         if line.strip())
        if typed:
            found["message"] = typed[:400]

    # An email from a lead marketplace is always a real customer, even when the
    # details are locked behind their dashboard. Never bin one.
    from_lead_source = is_lead_source(raw)

    if has_contact and has_context:
        found["status"] = LEAD
        found["reason"] = ""
    elif (has_contact and labelled_count >= 2) or from_lead_source:
        # A real enquiry we couldn't fully read. Stay silent, save it for review.
        found["status"] = NEEDS_REVIEW
        found["reason"] = ("lead from a marketplace we can't read fully"
                           if from_lead_source
                           else "looks like a form, but no job description found")
    else:
        # BUG D FIX: spam and newsletters land here and get binned, instead of
        # cluttering the review pile.
        found["status"] = SKIP_NOT_A_LEAD
        found["reason"] = "not enough to identify a genuine enquiry"

    # CHANGE 3: is this an emergency? A direct "flooded? yes" beats guessing.
    found["emergency"] = detect_emergency(text, found)

    found["missing"] = [f for f in ("address", "urgency") if not found.get(f)]
    return found


def log_for_review(raw, result, path="needs_review.log"):
    """
    Append an email we couldn't confidently read, so you can add the missing
    label later. This is why the agent can stay silent without losing anything.
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\nREASON: {result.get('reason')}\n{'=' * 60}\n")
        f.write(raw.strip() + "\n")
