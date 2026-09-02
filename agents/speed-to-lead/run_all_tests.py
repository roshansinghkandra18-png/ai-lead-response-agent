"""
run_all_tests.py  --  runs EVERY test and writes ONE results file.

This is the only test command you need:

    python run_all_tests.py

It runs both suites, prints everything to the screen, and saves the whole lot
to:

    what-the-tests-checked/latest.txt

...containing the test names, what was fed in, what was expected, and what
actually came back.

ONE file. Overwritten every run, so it is always the current picture and never
turns into a pile of similar filenames.

PART 3 IS SAFE. Parts 1 and 2 are rewritten from scratch every run, but
anything from the "PART 3" heading downwards is written by hand - the results
of sending real emails through Gmail - and this script carries it across
untouched. Adding a real-email test to that section will never be undone by
running the automated tests.
"""

import io
import os
import sys
from contextlib import redirect_stdout
from datetime import datetime

import test_samples
import test_replies
import test_calendar


OUTPUT_DIR = "what-the-tests-checked"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "latest.txt")

# Everything from this point in the old file downwards is hand-written and must
# survive. It's the record of real emails sent through Gmail, which no script
# can reproduce - lose it and the only way back is to send them all again.
KEEP_FROM = "=" * 70 + "\n  PART 3"


def capture(runner):
    """Run a test suite and grab everything it prints."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        runner()
    return buffer.getvalue()


def rescue_part_three():
    """
    Read the results file as it stands and hand back the hand-written Part 3,
    so it can be put straight back after the automated parts are rewritten.

    Returns an empty string if there's no Part 3 yet - which is the normal
    situation the very first time, and nothing to worry about.
    """
    if not os.path.exists(OUTPUT_FILE):
        return ""
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        old = f.read()
    at = old.find(KEEP_FROM)
    return "" if at == -1 else old[at:].rstrip() + "\n"


def main():
    stamp = datetime.now().strftime("%d %B %Y at %I:%M%p").lstrip("0")

    # Grab Part 3 BEFORE anything is written, or it goes over the cliff with
    # the rest of the old file.
    part_three = rescue_part_three()

    parser_output = capture(test_samples.run)
    reply_output = capture(test_replies.run)
    calendar_output = capture(test_calendar.run)

    report = []
    report.append("=" * 70)
    report.append("  SPEED-TO-LEAD AGENT - FULL TEST RESULTS")
    report.append(f"  Run on {stamp}")
    report.append("=" * 70)
    report.append("")
    report.append("This file contains every test we run on the agent, what was fed")
    report.append("into each one, what we expected back, and what actually came back.")
    report.append("")
    if part_three:
        report.append("There are three suites:")
    else:
        report.append("There are two suites:")
    report.append("  PART 1  - the PARSER      : does it READ an email correctly?")
    report.append("  PART 2  - the REPLY ENGINE: does it ANSWER one correctly?")
    report.append("  PART 2B - the DIARY       : does it know where the customer")
    report.append("                              is and when the plumber is free?")
    if part_three:
        report.append("  PART 3 - the WHOLE AGENT : does it work on REAL email, sent by")
        report.append("                             hand through Gmail?")
        report.append("")
        report.append("Parts 1 and 2 are rewritten by run_all_tests.py every time it runs.")
        report.append("Part 3 is written by hand and is carried across untouched.")
    report.append("")

    report.append("=" * 70)
    report.append("  PART 1 - THE PARSER")
    report.append("  Feeds the agent 24 different emails and checks what it")
    report.append("  understood from each one.")
    report.append("=" * 70)
    report.append("")
    report.append(parser_output)

    report.append("=" * 70)
    report.append("  PART 2 - THE REPLY ENGINE")
    report.append("  Checks the times it offers, who it decides to contact, and")
    report.append("  the exact words it writes.")
    report.append("=" * 70)
    report.append("")
    report.append(reply_output)

    report.append("=" * 70)
    report.append("  PART 2B - THE DIARY AND THE DRIVING")
    report.append("  Checks it knows WHERE the customer is, and WHEN the")
    report.append("  plumber is actually free. None of these touch Google -")
    report.append("  they run on made-up calendar entries and a zip code file.")
    report.append("=" * 70)
    report.append("")
    report.append(calendar_output)

    text = "\n".join(report)
    if part_three:
        text = text.rstrip() + "\n\n\n" + part_three

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(text)
    print(f"\nSaved to {OUTPUT_FILE}")
    if part_three:
        print("Part 3 (the real-email results) was kept, untouched.")
    else:
        print("No Part 3 found in the file - nothing to keep. That's normal the "
              "first time.")

    # Non-zero exit if anything failed, so a failure is impossible to miss.
    if "[FAIL]" in text:
        sys.exit(1)


if __name__ == "__main__":
    main()
