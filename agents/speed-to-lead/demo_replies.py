"""
demo_replies.py  --  shows the actual emails the agent would send.

Runs every test email through the parser AND the reply engine, then prints
exactly what the customer would receive and what the plumber would be told.

Nothing is sent. Nothing leaves your laptop.

RUN IT
    python demo_replies.py
"""

from datetime import datetime

from parse_lead import parse_email
from make_reply import handle, load_config, NOTHING
from test_samples import SAMPLES


# A fixed moment so the output is the same every time you run it.
# Tuesday 11 August 2026, 10:00am - the plumber is mid-job.
NOW = datetime(2026, 8, 11, 10, 0)

CONFIG = load_config("clients/joes_plumbing.ini")


def main():
    print(f"Pretending it is {NOW.strftime('%A %d %B %Y, %I:%M%p').lstrip('0')}")
    print(f"Client: {CONFIG['business']['name']}")
    print(f"Works {CONFIG['hours']['working_days']} "
          f"{CONFIG['hours']['start']}-{CONFIG['hours']['end']}, "
          f"{CONFIG['booking']['minimum_notice_hours']}h minimum notice\n")

    sent = alerts = silent = 0

    for s in SAMPLES:
        parsed = parse_email(s["raw"])
        outcome = handle(parsed, CONFIG, now=NOW)

        if outcome["action"] == NOTHING:
            silent += 1
            continue

        print("=" * 66)
        print(s["title"])
        print("=" * 66)

        if outcome["customer_email"]:
            sent += 1
            print(f"\n  TO      : {outcome['send_to']}")
            print(f"  SUBJECT : {outcome['subject']}")
            print("  " + "-" * 62)
            for line in outcome["customer_email"].splitlines():
                print(f"  {line}")
            print("  " + "-" * 62)

        if outcome["owner_alert"]:
            alerts += 1
            headline, details = outcome["owner_alert"]
            print(f"\n  >>> TO THE PLUMBER: {headline}")
            print(details)

        print()

    print("=" * 66)
    print(f"  {sent} customer emails written, {alerts} alerts to the plumber, "
          f"{silent} ignored")
    print("=" * 66)


if __name__ == "__main__":
    main()
