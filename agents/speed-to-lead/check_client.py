"""
check_client.py  --  checks a client's settings file BEFORE anything runs.

Run this on the onboarding call, in front of the client. It either says the
settings look good and reads them back in plain English, or it tells you exactly
which line is wrong and what to write instead.

The point is that you never see a page of red technical error text while
somebody is watching you.

RUN IT
    python check_client.py clients/joes_plumbing.ini
"""

import configparser
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo, available_timezones

from make_reply import WEEKDAYS, us_holidays


problems = []


def problem(setting, whats_wrong, what_to_write):
    problems.append((setting, whats_wrong, what_to_write))


def _section(cfg, name):
    if not cfg.has_section(name):
        problem(f"[{name}]", "this whole section is missing",
                f"add a line saying [{name}] and the settings that go under it")
        return False
    return True


def _text(cfg, section, key, example):
    """A setting that must be there and must not be empty."""
    if not cfg.has_section(section):
        return None
    value = cfg.get(section, key, fallback="").strip()
    if not value:
        problem(f"{key} (under [{section}])", "is missing or left blank",
                f"{key} = {example}")
        return None
    return value


def _whole_number(cfg, section, key, example, smallest=1):
    value = _text(cfg, section, key, example)
    if value is None:
        return None
    try:
        number = int(value)
    except ValueError:
        problem(f"{key} (under [{section}])",
                f'says "{value}", which is not a number',
                f"{key} = {example}   (digits only, no words)")
        return None
    if number < smallest:
        problem(f"{key} (under [{section}])",
                f"says {number}, which is too small",
                f"{key} = {example}   (must be {smallest} or more)")
        return None
    return number


def _clock(cfg, section, key, example, required=True):
    value = cfg.get(section, key, fallback="").strip() if cfg.has_section(section) else ""
    if not value:
        if required:
            problem(f"{key} (under [{section}])", "is missing or left blank",
                    f"{key} = {example}")
        return None
    try:
        hour, minute = value.split(":")
        return datetime.strptime(f"{int(hour):02d}:{int(minute):02d}", "%H:%M").time()
    except ValueError:
        problem(f"{key} (under [{section}])",
                f'says "{value}", which is not a time',
                f"{key} = {example}   (24-hour clock, so 5pm is 17:00)")
        return None


def check(path):
    # Start fresh, or checking a second file would inherit the first one's
    # problems and report them against the wrong client.
    problems.clear()

    cfg = configparser.ConfigParser()
    if not cfg.read(path, encoding="utf-8"):
        print(f"Could not find a settings file at: {path}")
        return None, 1

    for name in ("business", "hours", "booking", "questions", "emergency"):
        _section(cfg, name)

    # --- who they are ---
    name = _text(cfg, "business", "name", "Joe's Plumbing")
    email = _text(cfg, "business", "owner_email", "joe@joesplumbing.com")
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        problem("owner_email (under [business])",
                f'says "{email}", which is not an email address',
                "owner_email = joe@joesplumbing.com")

    # --- where they are ---
    zone = _text(cfg, "hours", "timezone", "America/New_York")
    if zone and zone not in available_timezones():
        problem("timezone (under [hours])",
                f'says "{zone}", which is not a timezone the computer knows',
                "timezone = America/New_York   (or America/Chicago, "
                "America/Denver, America/Phoenix, America/Los_Angeles)")
        zone = None

    # --- when they work ---
    days_text = _text(cfg, "hours", "working_days", "mon,tue,wed,thu,fri")
    days = []
    if days_text:
        for piece in days_text.split(","):
            piece = piece.strip().lower()
            if piece in WEEKDAYS:
                days.append(piece)
            elif piece:
                problem("working_days (under [hours])",
                        f'contains "{piece}", which is not a day',
                        "use only: mon, tue, wed, thu, fri, sat, sun")

    opens = _clock(cfg, "hours", "start", "08:00")
    closes = _clock(cfg, "hours", "end", "17:00")
    if opens and closes and opens >= closes:
        problem("start and end (under [hours])",
                f"say he opens at {opens.strftime('%H:%M')} and closes at "
                f"{closes.strftime('%H:%M')} - that is backwards",
                "start must be earlier than end, e.g. start = 08:00 and end = 17:00")

    # --- lunch: both or neither ---
    lunch_from = _clock(cfg, "hours", "lunch_start", "12:00", required=False)
    lunch_to = _clock(cfg, "hours", "lunch_end", "13:00", required=False)
    if bool(lunch_from) != bool(lunch_to):
        problem("lunch_start / lunch_end (under [hours])",
                "only one of the two is filled in",
                "fill in both, or leave both blank if there is no fixed break")
    if lunch_from and lunch_to and lunch_from >= lunch_to:
        problem("lunch_start / lunch_end (under [hours])",
                "the break ends before it starts",
                "e.g. lunch_start = 12:00 and lunch_end = 13:00")

    # --- how they take bookings ---
    window = _whole_number(cfg, "booking", "window_hours", "2")
    _whole_number(cfg, "booking", "minimum_notice_hours", "4", smallest=0)
    _whole_number(cfg, "booking", "max_offers_per_day", "3")
    _whole_number(cfg, "booking", "options_to_offer", "2")

    if window and opens and closes:
        day_length = closes.hour - opens.hour
        if window > day_length:
            problem("window_hours (under [booking])",
                    f"is {window} hours, but his working day is only "
                    f"{day_length} hours long - no appointment would ever fit",
                    f"window_hours = 2   (must be {day_length} or less)")

    # --- what it asks customers ---
    _text(cfg, "questions", "missing_address", "What's your full street address?")
    _text(cfg, "questions", "missing_urgency", "how soon do you need this?")
    _text(cfg, "emergency", "words", "emergency,flood,burst,no water")

    # --- holidays ---
    known = us_holidays(date.today().year)
    observed = []
    for piece in cfg.get("holidays", "observed", fallback="").split(","):
        piece = piece.strip().lower()
        if piece in known:
            observed.append(piece)
        elif piece:
            problem("observed (under [holidays])",
                    f'contains "{piece}", which is not a holiday name I know',
                    "choose from: " + ", ".join(sorted(known)))

    extra_days = []
    for piece in cfg.get("holidays", "extra", fallback="").split(","):
        piece = piece.strip()
        if not piece:
            continue
        try:
            month, day, year = piece.split("/")
            extra_days.append(date(int(year), int(month), int(day)))
        except ValueError:
            problem("extra (under [holidays])",
                    f'contains "{piece}", which is not a date I can read',
                    "write dates as MM/DD/YYYY, e.g. 08/25/2026")

    summary = {"name": name, "email": email, "zone": zone, "days": days,
               "opens": opens, "closes": closes, "lunch_from": lunch_from,
               "lunch_to": lunch_to, "observed": observed, "extra": extra_days}
    return summary, 0


def report(path, summary):
    if problems:
        print(f"Found {len(problems)} problem"
              f"{'s' if len(problems) > 1 else ''} in {path}:\n")
        for number, (setting, whats_wrong, fix) in enumerate(problems, start=1):
            print(f"  {number}. {setting} {whats_wrong}.")
            print(f"     Write:  {fix}\n")
        print("Fix those and run this again.")
        return 1

    day_names = ", ".join(d.capitalize() for d in summary["days"])
    print(f"{summary['name']} - settings look good.\n")
    print(f"  Where      : {summary['zone']}")
    print(f"  Works      : {day_names}")
    print(f"  Hours      : {summary['opens'].strftime('%H:%M')} to "
          f"{summary['closes'].strftime('%H:%M')}")
    if summary["lunch_from"]:
        print(f"  Lunch      : {summary['lunch_from'].strftime('%H:%M')} to "
              f"{summary['lunch_to'].strftime('%H:%M')} - never booked")
    else:
        print("  Lunch      : no fixed break")
    print(f"  Alerts go to: {summary['email']}")
    public = len(summary["observed"])
    own = len(summary["extra"])
    detail = f"{public} public holiday{'s' if public != 1 else ''}"
    if own:
        detail += f" plus {own} day{'s' if own != 1 else ''} of their own"
    print(f"  Days closed: {detail}")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Tell me which settings file to check, for example:")
        print("    python check_client.py clients/joes_plumbing.ini")
        return 1
    path = sys.argv[1]
    summary, failed = check(path)
    if failed:
        return failed
    return report(path, summary)


if __name__ == "__main__":
    sys.exit(main())
