"""
inbox.py  --  reads and sends real email.

This is the only file that talks to Gmail. Everything else works on plain text,
which is why the parser and reply engine could be built and tested for days
without a single account existing.

Uses only what comes with Python - nothing to install.
"""

import imaplib
import os
import smtplib
import email
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr


IMAP_HOST = "imap.gmail.com"      # where mail is READ from
SMTP_HOST = "smtp.gmail.com"      # where mail is SENT from
SMTP_PORT = 465                   # the encrypted one

# The agent's own memory of what it has already dealt with.
#
# It used to rely on Gmail's read/unread mark instead, and that had two holes.
# Google hides suspected spam from the inbox entirely, so a misfiled enquiry
# was never answered. And if the plumber opened an enquiry on his phone before
# the agent got to it, the mail counted as read and the agent walked past it
# forever - while the plumber assumed it had been handled.
#
# Now the agent keeps its own list and stops caring whether mail is read.
HANDLED_FILE = "already-handled.txt"

# How far back to look. Long enough to catch anything that arrived while the
# agent was switched off overnight, short enough that it is never wading
# through years of a plumber's email every 60 seconds.
DAYS_BACK = 3


def read_env(path=".env"):
    """
    Read the .env file. Deliberately hand-written rather than using a package -
    it is ten lines, and it keeps this agent free of extra downloads.
    """
    settings = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                settings[key.strip()] = value.strip()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find {path}.\n"
            "Copy example.env to .env and fill in your details first.")
    return settings


def connect(address, app_password):
    """Log in to the inbox. Spaces in the app password are ignored."""
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(address, app_password.replace(" ", ""))
    mail.select("INBOX")
    return mail


def load_handled(path=HANDLED_FILE):
    """
    Everything the agent has already dealt with, as a set of Message-IDs.

    A Message-ID is a unique stamp the sending mail server puts on every email
    ever written. It stays the same wherever the message is moved to, which is
    exactly what we need - dragging a mail out of Spam does not change it.
    """
    if not os.path.exists(path):
        return None            # None means "no memory yet" - the first run
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def remember_handled(message_id, path=HANDLED_FILE):
    """Write one Message-ID down, so it is never answered twice."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(message_id + "\n")


def _spam_folder(mail):
    """
    Find the Spam folder by asking the server which one it is.

    Never guessed by name - Gmail calls it different things in different
    languages, and a wrong guess would mean silently watching nothing.
    """
    status, folders = mail.list()
    if status != "OK":
        return None
    for row in folders or []:
        line = row.decode(errors="replace") if isinstance(row, bytes) else str(row)
        if "\\Junk" in line or "\\Spam" in line:
            return line.split(' "/" ')[-1].strip().strip('"')
    return None


def _identity(message):
    """
    The unique stamp for one email.

    Almost every email has a Message-ID. For the rare one that doesn't, fall
    back to who sent it, what it was called and when - which is close enough
    to unique to stop a repeat reply.
    """
    stamp = _header(message, "Message-ID").strip()
    if stamp:
        return stamp
    return "|".join([_header(message, "From"),
                     _header(message, "Subject"),
                     _header(message, "Date")])


def _header(message, name):
    """
    Read a header and turn any encoded gibberish back into readable text.

    Flattened onto ONE line. A long subject is transmitted "folded" across
    several lines, and the parser only knows to skip the first - so the rest
    dropped into the message body as though the customer had typed it. That is
    how a routine drain cleaning was declared an emergency: the website's own
    subject wording contained the word "urgent", and half of it landed in the
    body.
    """
    raw = message.get(name, "")
    try:
        value = str(make_header(decode_header(raw)))
    except Exception:
        value = raw
    return " ".join(value.split())


def _body(message):
    """
    Pull the readable text out of an email.

    Real emails often carry the same message twice - once as plain text and
    once as a web page. We prefer the plain text; if there isn't any, we hand
    the HTML to the parser, which knows how to flatten it.
    """
    if not message.is_multipart():
        return message.get_payload(decode=True).decode(
            message.get_content_charset() or "utf-8", errors="replace")

    plain, html = None, None
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_filename():          # an attachment, not the message
            continue
        kind = part.get_content_type()
        try:
            text = part.get_payload(decode=True).decode(
                part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if kind == "text/plain" and plain is None:
            plain = text
        elif kind == "text/html" and html is None:
            html = text

    return plain or html or ""


def _scan_folder(mail, folder, since):
    """
    Every message in one folder from the last few days, read or unread.

    Deliberately does NOT filter on unread. Whether the plumber has glanced at
    an email on his phone has nothing to do with whether a customer has been
    answered, and treating those as the same thing lost leads silently.
    """
    if mail.select(f'"{folder}"', readonly=False)[0] != "OK":
        return []

    status, data = mail.uid("search", None, f'(SINCE {since})')
    if status != "OK" or not data or not data[0]:
        return []

    found = []
    for uid in data[0].split():
        # BODY.PEEK leaves the read/unread mark exactly as the plumber left
        # it. The agent looks at his post without opening it for him.
        status, raw = mail.uid("fetch", uid, "(BODY.PEEK[])")
        if status != "OK" or not raw or not raw[0]:
            continue
        message = email.message_from_bytes(raw[0][1])

        rebuilt = (
            f"From: {_header(message, 'From')}\n"
            f"To: {_header(message, 'To')}\n"
            f"Subject: {_header(message, 'Subject')}\n"
            f"Date: {_header(message, 'Date')}\n"
            f"\n"
            f"{_body(message)}"
        )
        found.append({
            "folder": folder,
            "uid": uid,
            "id": _identity(message),
            "text": rebuilt,
            # Kept so the reply can be stamped as a genuine answer to this
            # exact message, instead of a fresh email with "Re:" typed on it.
            "message_id": _header(message, "Message-ID").strip(),
            "references": _header(message, "References").strip(),
            # Who actually sent it, address only. Used to check the reply is
            # really going back to this person before claiming to answer them.
            "from_address": parseaddr(_header(message, "From"))[1].lower(),
        })
    return found


def new_emails(mail, handled):
    """
    Everything the agent has not dealt with yet, from the inbox AND from spam.

    `handled` is the set of Message-IDs it already knows about. Pass an empty
    set and it will hand back everything from the last few days.

    Spam is included because Google routinely misfiles genuine enquiries -
    website contact forms are the usual casualty - and a customer sitting in
    the spam folder is still a customer who has had no reply.
    """
    since = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%d-%b-%Y")

    folders = ["INBOX"]
    spam = _spam_folder(mail)
    if spam:
        folders.append(spam)

    everything = []
    for folder in folders:
        everything.extend(_scan_folder(mail, folder, since))

    return [item for item in everything if item["id"] not in handled]


def mark_as_read(mail, folder, uid):
    """
    Tidy the plumber's inbox after answering, so his unread count means
    something. Spam is left strictly alone - the agent does not reorganise a
    folder the plumber never asked it to touch.
    """
    if folder != "INBOX":
        return
    if mail.select('"INBOX"', readonly=False)[0] != "OK":
        return
    mail.uid("store", uid, "+FLAGS", "\\Seen")


def build_message(address, to, subject, body, in_reply_to="", references=""):
    """
    Build the reply, ready to send.

    Kept separate from actually sending it so the finished email can be
    inspected in a test without a single message leaving the building.

    ABOUT THE STAMP (in_reply_to)
    Every email carries a hidden reference number. When a person hits Reply,
    their mail program copies that number onto the answer, which is what makes
    a conversation stack up neatly instead of scattering into loose messages.
    Without it we are sending a brand new email with the word "Re:" typed at
    the front - it looks like a reply to a human and is not one to a machine.

    That matters because the recipient's mail provider is constantly asking
    "did this person ask for it?" A message carrying the reference number of
    an email they sent five minutes ago is about as clearly wanted as mail
    gets - and until now we were throwing that away.
    """
    message = EmailMessage()
    message["From"] = address
    message["To"] = to
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        # References is the whole conversation so far, oldest first. Keeping
        # the chain means a long back-and-forth stays as one conversation
        # rather than splitting in two halfway through.
        chain = (references + " " + in_reply_to).split()
        message["References"] = " ".join(chain)
    message.set_content(body)
    return message


def send(address, app_password, to, subject, body,
         in_reply_to="", references=""):
    """Send one reply. Only ever called when SEND_FOR_REAL is switched on."""
    message = build_message(address, to, subject, body,
                            in_reply_to, references)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(address, app_password.replace(" ", ""))
        server.send_message(message)
