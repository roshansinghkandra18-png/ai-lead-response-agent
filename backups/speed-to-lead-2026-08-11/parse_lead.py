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
EMERGENCY_WORDS = (
    "emergency", "flood", "flooding", "flooded", "burst", "gushing",
    "no water", "gas leak", "sewage", "overflowing", "urgent", "asap",
    "right now", "immediately",
)


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
    ("water heater", "Water Heater"),
    ("hot water", "Water Heater"),
    ("garbage disposal", "Garbage Disposal"),
    ("sump pump", "Sump Pump"),
    ("air conditioning", "Air Conditioning"),
    ("septic", "Septic"),
    ("sewer", "Sewer"),
    ("furnace", "Heating"),
    ("boiler", "Boiler"),
    ("radiator", "Heating"),
    ("toilet", "Toilet"),
    ("faucet", "Faucet"),
    ("shower", "Shower"),
    ("bathtub", "Bathtub"),
    ("drain", "Drain Cleaning"),
    ("clog", "Drain Cleaning"),
    ("blocked", "Drain Cleaning"),
    ("burst", "Burst Pipe"),
    ("pipe", "Pipe Repair"),
    ("leak", "Leak"),
    ("sink", "Sink"),
    ("plumb", "Plumbing"),
]


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
    """
    kept = []
    for line in text.splitlines():
        if ":" in line and normalize(line.partition(":")[0]) in EMAIL_HEADERS:
            continue
        kept.append(line)
    return "\n".join(kept)


def find_by_pattern(text):
    """
    Fallback for forms with no labels at all - just a person typing a sentence.
    A phone number, an email address and a self-introduction all have a
    recognisable SHAPE, so we can find them even when nothing is labelled.
    """
    result = {"name": None, "phone": None, "email": None, "job_type": None}
    text = body_only(text)

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}", text)
    if email_match and not is_machine_address(email_match.group(0)):
        result["email"] = email_match.group(0)

    phone_match = re.search(
        r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b", text)
    if phone_match:
        result["phone"] = phone_match.group(0).strip()

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
    for keyword, label in TRADE_KEYWORDS:
        if keyword in scan:
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

    lowered = body_only(text).lower()
    return any(word in lowered for word in EMERGENCY_WORDS)


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

    found = extract_fields(text)

    # CHANGE 2: Angi and Squarespace put the name in two separate boxes. Join
    # them, or the reply says "Hi John" when his name is John Smith.
    if not found["name"]:
        parts = [found["first_name"], found["last_name"]]
        joined = " ".join(p for p in parts if p).strip()
        if joined:
            found["name"] = joined

    # How many real labelled fields did the form give us? A genuine enquiry form
    # has several. Spam usually has one at most. (BUG D FIX uses this.)
    labelled_count = sum(1 for f in FIELD_LABELS if found[f])

    # Fill any gaps using shapes rather than labels.
    patterns = find_by_pattern(text)
    for field in ("name", "phone", "email", "job_type"):
        if found[field] is None and patterns[field]:
            found[field] = patterns[field]

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
