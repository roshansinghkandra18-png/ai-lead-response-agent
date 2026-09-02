"""
run_agent.py  --  THE AGENT. This is the thing you actually run.

Every 60 seconds it checks the inbox. For each new email it works out whether
it's a real customer, what they want, and what to say back - then either sends
the reply or, in practice mode, just shows you what it would have sent.

BEFORE YOU RUN IT
    1. Copy example.env to .env and fill in your details
    2. Leave SEND_FOR_REAL=no until you're happy with what it writes

RUN IT
    python run_agent.py
"""

import csv
import os
import sys
import time
import traceback
from datetime import datetime, timedelta

import check_client
import diary
import inbox
from make_reply import handle, load_config, now_for_client, client_timezone
from parse_lead import parse_email, LEAD, NEEDS_REVIEW, log_for_review


LEADS_FILE = "leads.csv"
REPLIES_FILE = "replies-it-wrote.txt"
COLUMNS = ["seen_at", "status", "action", "name", "phone", "whose_phone",
           "other_phone", "whose_other_phone", "about_the_numbers", "email",
           "job_type", "address", "urgency", "emergency", "sent"]


def fix_spreadsheet_headings():
    """
    Make sure the heading row matches the columns we are about to write.

    The headings are written once, when the file is first created, and never
    again. So the day a new column is added, every heading in the plumber's
    spreadsheet points at the wrong column - the data is all correct and all
    mislabelled, which is worse than being wrong, because he cannot tell.

    Old rows are kept and slotted into the right places under the new
    headings. Nothing is lost and there is nothing for the client to do.
    """
    if not os.path.exists(LEADS_FILE):
        return

    with open(LEADS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if not rows or rows[0] == COLUMNS:
        return                      # already correct, or an empty file

    old_columns = rows[0]
    rebuilt = []
    for row in rows[1:]:
        # A file can hold rows of TWO different shapes: ones written before a
        # column was added, and ones written after, while the heading row was
        # still the old one. Reading every row as though it matched the old
        # heading shuffled the newer rows into the wrong columns - which is
        # how this function made things worse the first time it ran.
        if len(row) == len(COLUMNS):
            rebuilt.append(row)                    # already the new shape
        elif len(row) == len(old_columns):
            was = dict(zip(old_columns, row))
            rebuilt.append([was.get(column, "") for column in COLUMNS])
        else:
            # Neither shape. Keep what is there rather than guess, padded out
            # so the row still lines up with the headings.
            rebuilt.append((row + [""] * len(COLUMNS))[:len(COLUMNS)])

    with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rebuilt)

    print(f"  {LEADS_FILE}: column headings brought up to date, "
          f"{len(rebuilt)} existing row(s) kept.")


def log_lead(parsed, outcome, sent, when):
    """
    Every lead lands in a spreadsheet the plumber can open in Excel.

    `when` is the time in the CLIENT's country, not ours. The plumber checks
    this log against his own day - timestamps from a different timezone make it
    useless to him, and a log he can't trust is a log he stops opening.
    """
    new_file = not os.path.exists(LEADS_FILE)
    with open(LEADS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "seen_at": when.strftime("%m/%d/%Y %I:%M%p"),
            "status": parsed.get("status"),
            "action": outcome.get("action"),
            "name": parsed.get("name") or "",
            "phone": parsed.get("phone") or "",
            # Blank in the ordinary case, where the number is the customer's
            # own. Filled in only when it belongs to somebody they named, so
            # the plumber never rings a stranger thinking it is the customer.
            "whose_phone": parsed.get("phone_belongs_to") or "",
            "other_phone": parsed.get("other_phone") or "",
            "whose_other_phone": parsed.get("other_phone_note") or "",
            "about_the_numbers": (parsed.get("phone_said")
                                  or parsed.get("other_phone_said") or ""),
            "email": parsed.get("email") or "",
            "job_type": parsed.get("job_type") or "",
            "address": parsed.get("address") or "",
            "urgency": parsed.get("urgency") or "",
            "emergency": "YES" if parsed.get("emergency") else "",
            "sent": sent,
        })


def save_reply(outcome, when, sent):
    """
    Keep every reply the agent writes, so you can read them later instead of
    watching them scroll past in the terminal.
    """
    with open(REPLIES_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 66 + "\n")
        f.write(f"{when.strftime('%m/%d/%Y %I:%M%p')}   "
                f"{'SENT' if sent == 'yes' else 'NOT SENT - practice mode'}\n")
        f.write("=" * 66 + "\n")
        f.write(f"To     : {outcome['send_to']}\n")
        f.write(f"Subject: {outcome['subject']}\n\n")
        f.write(outcome["customer_email"] + "\n")


def show(parsed, outcome, sending):
    """Print what happened, so you can watch it work."""
    print("-" * 66)
    who = parsed.get("name") or "unknown"
    print(f"  {who} - {parsed.get('status')}")

    if outcome["action"] == "NOTHING":
        print(f"  ignored: {parsed.get('reason', '')}")
        return

    if outcome.get("owner_alert"):
        headline, details = outcome["owner_alert"]
        print(f"\n  >>> FOR THE PLUMBER: {headline}")
        print(details)

    if outcome.get("customer_email"):
        label = "SENDING TO" if sending else "WOULD SEND TO (practice mode)"
        print(f"\n  {label}: {outcome['send_to']}")
        print(f"  SUBJECT   : {outcome['subject']}")
        for line in outcome["customer_email"].splitlines():
            print(f"      {line}")


def whats_he_doing(calendar, cfg, env, now):
    """
    What the plumber already has booked, for the next fortnight.

    Returns None when there is no calendar connected or it cannot be read.
    That is NOT the same as an empty diary, and the difference matters: an
    unreachable calendar must never be mistaken for a free week.
    """
    if calendar is None:
        return None
    try:
        return diary.busy_periods(calendar, env["CALENDAR_ID"],
                                  client_timezone(cfg), now,
                                  now + timedelta(days=14))
    except diary.DiaryUnavailable as oops:
        print(f"  >>> FOR THE PLUMBER: could not read your calendar, so no "
              f"appointment times are being offered.\n      {oops}")
        return None


def process(mail, item, cfg, env, sending, busy=None):
    """One email, from arrival to logged."""
    raw = item["text"]
    their_time = now_for_client(cfg)
    parsed = parse_email(raw)
    outcome = handle(parsed, cfg, now=their_time, busy=busy,
                     travel_minutes=int(cfg.get("travel", "default_minutes",
                                                fallback="30")))

    # Never reply to ourselves - that is how two machines end up emailing each
    # other forever and get the client's domain marked as a spammer.
    recipient = (outcome.get("send_to") or "").lower()
    if recipient and recipient == env["GMAIL_ADDRESS"].lower():
        print("  refusing to reply to our own address")
        outcome["customer_email"] = None

    # Stamp the reply as a genuine answer to this exact message - but ONLY if
    # we are writing back to the person who actually sent it.
    #
    # A forwarded enquiry looks the same from here and isn't. When the office
    # assistant forwards a website form, the reference number belongs to HER
    # email, not to anything the customer ever saw. Claiming to answer a
    # conversation the customer was never part of helps nobody.
    replying_to_sender = bool(recipient) and recipient == item.get("from_address")
    in_reply_to = item.get("message_id", "") if replying_to_sender else ""
    references = item.get("references", "") if replying_to_sender else ""

    show(parsed, outcome, sending)

    if outcome.get("customer_email"):
        if in_reply_to:
            print("  threaded : yes - stamped as a reply to their own email")
        else:
            print("  threaded : no - not writing back to whoever sent this")

    sent = ""
    if sending and outcome.get("customer_email"):
        try:
            inbox.send(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"],
                       outcome["send_to"], outcome["subject"],
                       outcome["customer_email"],
                       in_reply_to=in_reply_to, references=references)
            sent = "yes"
            print("  ...sent")
        except Exception as oops:
            sent = f"FAILED: {oops}"
            print(f"  COULD NOT SEND: {oops}")

    if outcome.get("customer_email"):
        save_reply(outcome, their_time, sent)

    if parsed.get("status") == NEEDS_REVIEW:
        log_for_review(raw, parsed)
        print("  saved to needs_review.log for you to look at")

    if parsed.get("status") in (LEAD, NEEDS_REVIEW):
        log_lead(parsed, outcome, sent, their_time)

    # Written down LAST, and only once everything above has worked. If the
    # agent dies halfway through, this email is still unfinished business and
    # gets picked up again next time - better a second look than a lost lead.
    inbox.remember_handled(item["id"])
    inbox.mark_as_read(mail, item["folder"], item["uid"])


def main():
    try:
        env = inbox.read_env()
    except FileNotFoundError as oops:
        print(oops)
        return 1

    for needed in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "CLIENT_CONFIG"):
        if not env.get(needed):
            print(f"Your .env file is missing {needed}. See example.env.")
            return 1

    # Check the client's settings before touching anything else.
    summary, failed = check_client.check(env["CLIENT_CONFIG"])
    if failed or check_client.problems:
        check_client.report(env["CLIENT_CONFIG"], summary)
        return 1

    fix_spreadsheet_headings()

    cfg = load_config(env["CLIENT_CONFIG"])

    # The plumber's diary. Checked NOW rather than when the first customer
    # emails, so a permission problem is a sentence on the screen at setup
    # instead of a customer being ignored an hour later.
    calendar = None
    if env.get("GOOGLE_SERVICE_ACCOUNT_FILE") and env.get("CALENDAR_ID"):
        try:
            calendar = diary.connect(env["GOOGLE_SERVICE_ACCOUNT_FILE"],
                                     env["CALENDAR_ID"])
        except diary.DiaryUnavailable as oops:
            print("\nCannot open the plumber's calendar:\n")
            print(f"  {oops}\n")
            return 1
    sending = env.get("SEND_FOR_REAL", "no").strip().lower() in ("yes", "true", "1")
    gap = int(env.get("CHECK_EVERY_SECONDS") or 60)
    stop_after = env.get("STOP_AFTER_CHECKS", "").strip()
    stop_after = int(stop_after) if stop_after else None

    print("=" * 66)
    print(f"  {summary['name']} - Speed-to-Lead agent")
    print("=" * 66)
    print(f"  Watching   : {env['GMAIL_ADDRESS']}")
    print("  Folders    : Inbox and Spam (Google misfiles real enquiries)")
    print(f"  Their time : {now_for_client(cfg).strftime('%A %d %b, %I:%M%p %Z')}")
    if calendar:
        print(f"  Calendar   : {env['CALENDAR_ID']} - reading his real diary")
    else:
        print("  Calendar   : NOT CONNECTED - times offered are guesses, "
              "not promises")
    print(f"  Checking   : every {gap} seconds")
    if sending:
        print("  MODE       : SENDING FOR REAL - customers will receive these")
    else:
        print("  MODE       : practice - nothing will actually be sent")
    print("  Stop with Ctrl+C")
    print("=" * 66)

    try:
        mail = inbox.connect(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"])
    except Exception as oops:
        print(f"\nCould not log in to Gmail: {oops}\n")
        print("The usual causes:")
        print("  - the app password was typed wrong (16 letters, from Google)")
        print("  - 2-Step Verification isn't switched on for that account")
        print("  - the email address in .env has a typo")
        return 1

    handled = inbox.load_handled()

    # FIRST RUN EVER. The agent has no memory yet, so everything already in
    # the mailbox looks new to it. Left alone it would answer months of old
    # email at once. Instead it writes today's contents down as already dealt
    # with, replies to nothing, and starts fresh from the next check.
    if handled is None:
        print("\n  First run - the agent has no memory of this mailbox yet.")
        print("  Writing down what's already here so it does NOT reply to old")
        print("  email. Nothing will be answered on this pass. Anything that")
        print("  arrives from now on is treated as new.\n")
        handled = set()
        try:
            for item in inbox.new_emails(mail, handled):
                inbox.remember_handled(item["id"])
                handled.add(item["id"])
            print(f"  {len(handled)} existing message(s) noted. Watching from now on.\n")
        except Exception:
            print("  could not read the mailbox to do that:")
            traceback.print_exc()
            return 1

    checks = 0
    try:
        while True:
            checks += 1
            try:
                waiting = inbox.new_emails(mail, handled)
            except Exception:
                # A dropped connection shouldn't kill the agent overnight.
                print("  connection dropped, reconnecting...")
                mail = inbox.connect(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"])
                waiting = inbox.new_emails(mail, handled)

            stamp = datetime.now().strftime("%H:%M:%S")
            if waiting:
                print(f"\n[{stamp}] {len(waiting)} new email(s)")
                # Read the diary once per batch, not once per email. His
                # bookings do not change between two emails arriving in the
                # same minute, and it saves hammering Google.
                busy = whats_he_doing(calendar, cfg, env, now_for_client(cfg))
                if busy is not None:
                    print(f"  diary    : {len(busy)} job(s) already booked")
                for item in waiting:
                    where = "" if item["folder"] == "INBOX" else "  (found in SPAM)"
                    if where:
                        print(where)
                    try:
                        process(mail, item, cfg, env, sending, busy=busy)
                        handled.add(item["id"])
                    except Exception:
                        print("  something went wrong with this one:")
                        traceback.print_exc()
            else:
                print(f"[{stamp}] nothing new")

            if stop_after and checks >= stop_after:
                print(f"\nStopping after {checks} checks (set by STOP_AFTER_CHECKS).")
                break
            time.sleep(gap)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
