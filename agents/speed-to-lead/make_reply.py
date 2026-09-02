"""
make_reply.py  --  the reply engine for the Speed-to-Lead agent.

WHAT THIS DOES
    Takes the facts the parser found and produces three things:
      1. Two arrival windows that fit the plumber's working rules
      2. The actual email to send the customer
      3. A decision about who gets what - customer, plumber, or both

WHAT THIS DOES NOT DO
    Does not send anything. Does not read an inbox. Does not know the plumber's
    existing jobs yet (that arrives with the calendar). Costs nothing to run.

TO SEE IT WORK
    python demo_replies.py
"""

import calendar
import configparser
from datetime import datetime, timedelta, time, date
from zoneinfo import ZoneInfo

import distance


# What the agent decides to do about a lead.
EMAIL_CUSTOMER = "EMAIL_CUSTOMER"          # normal - offer times by email
EMAIL_AND_ALERT = "EMAIL_AND_ALERT"        # emergency - reassure them, wake him up
ALERT_OWNER_CALL = "ALERT_OWNER_CALL"      # no email address - he must phone
NOTHING = "NOTHING"                        # junk, auto-replies, thread replies


WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def load_config(path):
    """Read a client's settings file. One file per client, no code involved."""
    parser = configparser.ConfigParser()
    read = parser.read(path, encoding="utf-8")
    if not read:
        raise FileNotFoundError(f"Could not find the client settings file: {path}")
    return parser


def client_timezone(cfg):
    """
    WHERE the client is. Without this the agent uses whatever clock the computer
    running it happens to have -- which for us is India, while the client is in
    the United States. Every appointment time would be wrong by hours.
    """
    return ZoneInfo(cfg.get("hours", "timezone", fallback="America/New_York"))


def now_for_client(cfg):
    """The time it is RIGHT NOW where the client lives, not where we live."""
    return datetime.now(ZoneInfo("UTC")).astimezone(client_timezone(cfg))


def to_client_time(cfg, moment):
    """
    Convert any moment into the client's local clock.

    A moment with no zone attached is assumed to already be the client's local
    time -- that is how the tests feed in fixed times like "Tuesday 10am".
    """
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(client_timezone(cfg))


# ---------------------------------------------------------------------------
# PUBLIC HOLIDAYS
#
# These are worked out from the rules, not typed in as a list of dates - so
# they keep working in 2027, 2030 and beyond without anyone updating anything.
# ---------------------------------------------------------------------------

MONDAY, THURSDAY = 0, 3


def _nth_weekday(year, month, weekday, n):
    """The n-th given weekday of a month. Use n = -1 for the LAST one."""
    total = calendar.monthrange(year, month)[1]
    matches = [d for d in range(1, total + 1)
               if date(year, month, d).weekday() == weekday]
    return date(year, month, matches[n - 1] if n > 0 else matches[-1])


def _observed(day):
    """
    The American rule for a fixed-date holiday landing on a weekend:
    Saturday is taken as the Friday before, Sunday as the Monday after.
    """
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def us_holidays(year):
    """Every US public holiday a home-services business might close for."""
    thanksgiving = _nth_weekday(year, 11, THURSDAY, 4)
    return {
        "new years": _observed(date(year, 1, 1)),
        "mlk day": _nth_weekday(year, 1, MONDAY, 3),
        "presidents day": _nth_weekday(year, 2, MONDAY, 3),
        "memorial day": _nth_weekday(year, 5, MONDAY, -1),
        "juneteenth": _observed(date(year, 6, 19)),
        "independence day": _observed(date(year, 7, 4)),
        "labor day": _nth_weekday(year, 9, MONDAY, 1),
        "columbus day": _nth_weekday(year, 10, MONDAY, 2),
        "veterans day": _observed(date(year, 11, 11)),
        "thanksgiving": thanksgiving,
        "day after thanksgiving": thanksgiving + timedelta(days=1),
        "christmas eve": date(year, 12, 24),
        "christmas": _observed(date(year, 12, 25)),
        "new years eve": date(year, 12, 31),
    }


def days_off(cfg, year):
    """
    The dates this particular client does not work in a given year: the public
    holidays they chose to observe, plus any extra days they told us about.
    """
    table = us_holidays(year)
    chosen = [n.strip().lower()
              for n in cfg.get("holidays", "observed", fallback="").split(",")
              if n.strip()]

    unknown = [n for n in chosen if n not in table]
    if unknown:
        raise ValueError(
            f"Unknown holiday name(s) in the settings file: {', '.join(unknown)}.\n"
            f"Valid names are: {', '.join(sorted(table))}")

    off = {table[n] for n in chosen}

    # Extra days off the client told us about, written the American way.
    for extra in cfg.get("holidays", "extra", fallback="").split(","):
        extra = extra.strip()
        if not extra:
            continue
        try:
            month, day, yr = extra.split("/")
            off.add(date(int(yr), int(month), int(day)))
        except ValueError:
            raise ValueError(
                f"Could not read the extra day off '{extra}'. "
                "Dates must be written MM/DD/YYYY, for example 08/25/2026.")
    return off


# How each holiday should be written to a customer.
HOLIDAY_NAMES = {
    "new years": "New Year's Day",
    "mlk day": "Martin Luther King Jr. Day",
    "presidents day": "Presidents' Day",
    "memorial day": "Memorial Day",
    "juneteenth": "Juneteenth",
    "independence day": "the 4th of July",
    "labor day": "Labor Day",
    "columbus day": "Columbus Day",
    "veterans day": "Veterans Day",
    "thanksgiving": "Thanksgiving",
    "day after thanksgiving": "the day after Thanksgiving",
    "christmas eve": "Christmas Eve",
    "christmas": "Christmas",
    "new years eve": "New Year's Eve",
}


def holidays_between(cfg, first_day, last_day):
    """
    Named holidays the client is closed for, between two dates.

    Used to explain a delay. A customer emailing on 2 July who is offered
    Monday the 6th should be told why, or the plumber just looks slow.
    """
    found = []
    for year in range(first_day.year, last_day.year + 1):
        table = us_holidays(year)
        closed = days_off(cfg, year)
        for key, when in table.items():
            if when in closed and first_day <= when <= last_day:
                found.append((when, HOLIDAY_NAMES.get(key, key)))
    return sorted(set(found))


def _hhmm(text):
    """Turn "08:00" from the settings file into a real time."""
    hour, minute = text.strip().split(":")
    return time(int(hour), int(minute))


def _optional_hhmm(cfg, key):
    """A time setting the client may have left blank."""
    raw = cfg.get("hours", key, fallback="").strip()
    return _hhmm(raw) if raw else None


def _next_working_morning(moment, day_start):
    """
    Jump to the start of the next day, keeping the client's timezone attached.
    (Rebuilding the date from scratch here would silently drop the timezone.)
    """
    return (moment + timedelta(days=1)).replace(
        hour=day_start.hour, minute=day_start.minute, second=0, microsecond=0)


def _on_the_grid(moment, step_minutes):
    """
    Nudge a time forward onto the next tidy start time.

    Plumbers say "between 10:30 and 11:30", not "between 10:17 and 11:17". But
    the wider the step, the more of his day gets thrown away: free at 10:30 and
    rounded up to 11:00 is half an hour he could have been earning in. That is
    why the step is a setting rather than a fixed hour.
    """
    moment = moment.replace(second=0, microsecond=0)
    over = moment.minute % step_minutes
    if over:
        moment += timedelta(minutes=step_minutes - over)
    return moment


def collides(start, finish, busy, travel, gap_for=None):
    """
    Would a job from `start` to `finish` run into anything already in the diary?

    Returns the moment the plumber is next genuinely free, or None if there is
    no clash. `travel` is padding either side, so he is never expected to
    teleport from one customer's kitchen to the next.

    `gap_for` is an optional function that works out the real drive time from a
    particular job to this customer. When it isn't given, or when a diary entry
    has no address on it, everything falls back to the flat `travel` gap.

    Deliberately kept here rather than in diary.py so it can be tested without
    a Google account existing - the same reason the parser and reply engine
    were built for days before there was a mailbox.
    """
    free_at = None
    for job in busy:
        taken_from, taken_to = job[0], job[1]

        # If we know where that job is AND where this customer is, use the real
        # drive between them. Otherwise fall back to the standard gap - which
        # is what happens whenever the plumber leaves the location blank on his
        # own calendar entries, i.e. most of the time.
        gap = travel
        if gap_for is not None:
            gap = gap_for(job[2] if len(job) > 2 else None)

        if start < taken_to + gap and finish + gap > taken_from:
            candidate = taken_to + gap
            if free_at is None or candidate > free_at:
                free_at = candidate
    return free_at


def travel_lookup(cfg, customer_zip, fallback_minutes):
    """
    Build the "how long is the drive?" function for one particular customer.

    Uses the real distance whenever both ends are known: the job already in the
    diary, and this customer. Falls back to the plumber's standard gap the
    moment either is missing - which is most of the time, because plumbers do
    not fill the address in on their own calendar entries.
    """
    def gap(job_zip):
        if job_zip and customer_zip:
            return timedelta(minutes=distance.minutes_between(
                job_zip, customer_zip, cfg))
        return timedelta(minutes=fallback_minutes)
    return gap


def next_windows(cfg, now, count=None, busy=None, travel_minutes=0,
                 customer_zip=None):
    """
    Work out the next few arrival windows the plumber could realistically take.

    It respects these rules from his settings file:
      - only on days he works
      - only inside his working hours
      - never through his lunch
      - never sooner than his minimum notice (his chance to see a job and say
        no before a customer is waiting for him)
      - never more than his daily cap

    `busy` is what his calendar says he is already doing - a list of
    (start, finish) pairs. Leave it out and the agent falls back to knowing his
    working hours only, which is a proposal rather than a promise.

    `travel_minutes` is the gap left either side of an existing job, so he is
    not booked into two places at once with no time to drive between them.
    """
    # Everything below is worked out on the CLIENT's clock.
    now = to_client_time(cfg, now)

    working_days = {WEEKDAYS[d.strip().lower()]
                    for d in cfg["hours"]["working_days"].split(",")}
    day_start = _hhmm(cfg["hours"]["start"])
    day_end = _hhmm(cfg["hours"]["end"])
    lunch_start = _optional_hhmm(cfg, "lunch_start")
    lunch_end = _optional_hhmm(cfg, "lunch_end")

    # Public holidays, worked out per year as we walk forward through the diary.
    holiday_cache = {}

    def closed_for_holiday(day):
        if day.year not in holiday_cache:
            holiday_cache[day.year] = days_off(cfg, day.year)
        return day in holiday_cache[day.year]

    window_hours = int(cfg["booking"]["window_hours"])
    notice_hours = int(cfg["booking"]["minimum_notice_hours"])
    max_per_day = int(cfg["booking"]["max_offers_per_day"])
    travel = timedelta(minutes=travel_minutes)
    step = int(cfg.get("booking", "appointment_every_minutes", fallback="60"))
    gap_for = (travel_lookup(cfg, customer_zip, travel_minutes)
               if customer_zip else None)
    if count is None:
        count = int(cfg["booking"]["options_to_offer"])

    # Earliest we're allowed to offer, nudged forward onto a tidy start time.
    cursor = _on_the_grid(now + timedelta(hours=notice_hours), step)

    windows = []
    used_today = {}
    safety = 0

    while len(windows) < count and safety < 24 * 30:
        safety += 1

        if cursor.weekday() not in working_days:
            cursor = _next_working_morning(cursor, day_start)
            continue

        # Public holidays. Nobody wants "Thursday 2-4pm" offered on Thanksgiving.
        if closed_for_holiday(cursor.date()):
            cursor = _next_working_morning(cursor, day_start)
            continue

        if cursor.time() < day_start:
            cursor = cursor.replace(hour=day_start.hour, minute=day_start.minute,
                                    second=0, microsecond=0)
            continue

        # Lunch. If the window would run through his break, start after it.
        if lunch_start and lunch_end and cursor.time() < lunch_end:
            finish_time = (cursor + timedelta(hours=window_hours)).time()
            if finish_time > lunch_start:
                cursor = cursor.replace(hour=lunch_end.hour,
                                        minute=lunch_end.minute,
                                        second=0, microsecond=0)
                continue

        finish = cursor + timedelta(hours=window_hours)
        if finish.date() != cursor.date() or finish.time() > day_end:
            cursor = _next_working_morning(cursor, day_start)
            continue

        if used_today.get(cursor.date(), 0) >= max_per_day:
            cursor = _next_working_morning(cursor, day_start)
            continue

        # What his diary says he is ALREADY doing. Everything above this point
        # only knows his working hours; this is the difference between "he
        # could in principle" and "he actually can".
        if busy:
            free_at = collides(cursor, finish, busy, travel, gap_for)
            if free_at:
                # Jump to the far side of the job that is in the way. Stepping
                # forward one window at a time would crawl through an all-day
                # booking an hour at a time.
                free_at = _on_the_grid(free_at, step)
                cursor = max(free_at, cursor + timedelta(minutes=step))
                continue

        windows.append((cursor, finish))
        used_today[cursor.date()] = used_today.get(cursor.date(), 0) + 1
        cursor = finish

    return windows


def _clock(moment, show_meridiem=True):
    """2pm, 11am, 2:30pm - the way a person writes a time."""
    hour = moment.hour % 12 or 12
    meridiem = "am" if moment.hour < 12 else "pm"
    text = f"{hour}" if moment.minute == 0 else f"{hour}:{moment.minute:02d}"
    return text + (meridiem if show_meridiem else "")


def describe_window(window, now):
    """Turn a pair of times into "Tuesday 2-4pm" the way a dispatcher would."""
    start, finish = window
    days_away = (start.date() - now.date()).days

    if days_away == 0:
        day = "today"
    elif days_away == 1:
        day = "tomorrow"
    elif days_away < 7:
        day = start.strftime("%A")
    else:
        day = start.strftime("%a %d %b")

    # "2-4pm" when both halves of the day match, "11am-1pm" when they don't.
    same_half = (start.hour < 12) == (finish.hour < 12)
    left = _clock(start, show_meridiem=not same_half)
    right = _clock(finish)
    return f"{day} {left}-{right}"


def decide_action(parsed):
    """Who should hear about this lead, and how."""
    status = parsed.get("status")
    if status != "LEAD":
        return NOTHING
    if parsed.get("emergency"):
        return EMAIL_AND_ALERT if parsed.get("email") else ALERT_OWNER_CALL
    return EMAIL_CUSTOMER if parsed.get("email") else ALERT_OWNER_CALL


def _greeting(parsed):
    """First names only. "Hi Michael" reads warmer than "Hi Michael Torres"."""
    name = (parsed.get("name") or "").strip()
    return name.split()[0] if name else "there"


# Job names that are a condition or a bare appliance rather than a piece of
# work. On their own they read clipped -- "about your flooding", "about your
# water heater" -- so the word "issue" is added to make them sound human.
# Anything already describing work ("water heater repair", "toilet installation")
# is left alone, and so are problem words that stand fine by themselves
# ("your leak", "your burst pipe").
NEEDS_ISSUE = {
    "flooding", "overflow", "sewage",
    "sewage backup", "sewer", "septic", "water damage",
    "water heater", "water supply", "boiler", "heating", "air conditioning",
    "toilet", "faucet", "shower", "bathtub", "sink",
    "sump pump", "garbage disposal", "plumbing",
}


# Some job names describe what ISN'T working rather than naming a thing. Slot
# those into "...about your ___" and you get "about your no hot water issue" --
# grammatical, and obviously written by a machine.
#
# So the customer hears the plain English a plumber would use on the phone,
# while the plumber's own spreadsheet keeps the symptom the customer reported,
# because "No Hot Water" tells him more before he sets off than "Water Heater"
# does.
SAY_INSTEAD = {
    "no hot water": "water heater",
    "no water": "water supply",
}


def _job_phrase(parsed):
    """
    The job, phrased to slot into "...about your ___" and "Re: your ___".

    The fallback deliberately does NOT contain the word "your" -- the sentences
    around it already supply that. It used to, which produced the subject line
    "Re: your your plumbing job request".
    """
    job = (parsed.get("job_type") or "").strip().lower()
    if not job:
        return "plumbing job"
    job = SAY_INSTEAD.get(job, job)
    return f"{job} issue" if job in NEEDS_ISSUE else job


def _extra_question(parsed, cfg):
    """
    Ask at most ONE thing, and only what the form didn't already tell us.
    Asking a customer for something they typed 10 seconds ago is the fastest
    way to look like a machine.
    """
    # A missing address is NOT handled here any more. It stops the reply
    # offering times at all, so it gets its own branch in build_customer_email.
    missing = parsed.get("missing") or []
    if "urgency" in missing:
        return cfg["questions"]["missing_urgency"]
    return None


def needs_address(parsed):
    """
    True when we cannot offer times yet, because we don't know where they are.

    Travel time between jobs and the service-area check BOTH need a street
    address, and both have to happen before a time is offered. Offering windows
    first and asking where they live afterwards is how you promise somebody a
    slot you then find out you can't make - or can't even drive to.
    """
    return "address" in (parsed.get("missing") or [])


def out_of_area(parsed, cfg):
    """
    Is this customer further away than the plumber is willing to drive?

    Returns (True, minutes) when they are too far, (False, minutes) otherwise.

    Worth doing BEFORE any time is offered. Without it the agent cheerfully
    books a job sixty miles away and the plumber only finds out when he opens
    his spreadsheet - by which point a customer is expecting him.
    """
    return distance.too_far(distance.zip_from(parsed.get("address")), cfg)


def build_customer_email(parsed, cfg, windows, now):
    """The email the customer actually receives."""
    business = cfg["business"]["name"]
    first = _greeting(parsed)
    job = _job_phrase(parsed)

    # --- Emergency: no booking, just reassurance and speed ---
    if parsed.get("emergency"):
        body = (
            f"Hi {first},\n\n"
            f"Thanks for reaching out about your {job} - that sounds urgent, "
            f"so I've flagged it straight away.\n\n"
            f"Someone from {business} will call you shortly to get to you as "
            f"fast as possible.\n\n"
            f"- {business}"
        )
        return f"Re: your {job}", body

    # --- We don't know where they are yet: ask, and offer nothing ---
    # Deliberately gives the reason. "What's your address" from a machine reads
    # like data collection; "so we can check we cover you and give you a time we
    # can keep" reads like someone trying to help.
    if needs_address(parsed):
        body = (
            f"Hi {first},\n\n"
            f"Thanks for reaching out about your {job}.\n\n"
            f"{cfg['questions']['missing_address']}\n\n"
            f"We check it's inside the area we cover, and it lets us give you "
            f"an arrival time we can actually keep.\n\n"
            f"- {business}"
        )
        return f"Re: your {job}", body

    # --- Too far away: say so honestly, and offer nothing ---
    # Better a polite no in 60 seconds than a booking he resents, or a customer
    # left waiting while he drives across two counties. Gives the reason, so it
    # doesn't read as a brush-off.
    far, minutes = out_of_area(parsed, cfg)
    if far:
        # Deliberately does NOT quote the drive time to the customer. Our
        # estimate is a straight line with a fudge factor, and it goes badly
        # wrong over long distances - it called Cleveland to Columbus a 4 hour
        # drive when it is really about 2 hours 15. Telling somebody that makes
        # the plumber look like he doesn't know his own state. The number is
        # still passed to HIM, in case he fancies the job anyway.
        body = (
            f"Hi {first},\n\n"
            f"Thanks for reaching out about your {job}.\n\n"
            f"Unfortunately you're outside the area we cover, and we keep to "
            f"jobs closer to home so we can turn up when we say we will.\n\n"
            f"Sorry we can't help this time, and I hope you get it sorted "
            f"quickly.\n\n"
            f"- {business}"
        )
        return f"Re: your {job}", body

    # --- Normal: offer arrival windows ---
    lines = [f"Hi {first},", "", f"Thanks for reaching out about your {job}.", ""]

    if windows:
        # If a holiday is the reason the first slot isn't sooner, say so -
        # including when the customer is writing to us ON the holiday itself.
        # Otherwise the plumber just looks slow for no reason.
        closed = holidays_between(cfg, now.date(),
                                  windows[0][0].date() - timedelta(days=1))
        if closed:
            when, what = closed[0]
            day = "today" if when == now.date() else when.strftime("%A")
            others = "" if len(closed) == 1 else " (and a couple of days around it)"
            lines.append(f"We're closed {day} for {what}{others}, so the "
                         "earliest I can get someone to you is:")
        else:
            lines.append("I can get someone out to you:")

        for number, window in enumerate(windows, start=1):
            lines.append(f"  {number} - {describe_window(window, now)}")
        lines.append("")
        choices = " or ".join(str(n) for n in range(1, len(windows) + 1))
        lines.append(f"Just reply with {choices} and I'll lock it in.")
    else:
        lines.append("I'll come straight back to you with some times.")

    question = _extra_question(parsed, cfg)
    if question:
        lines.append("")
        lines.append(f"Also, {question}")

    lines += ["", f"- {business}"]
    return f"Re: your {job}", "\n".join(lines)


def build_owner_alert(parsed, action):
    """The short note that tells the plumber a human is needed."""
    headline = ("EMERGENCY - CALL NOW" if parsed.get("emergency")
                else "CALL THIS PERSON - no email address")

    # Whose number it is matters as much as the number. Ringing a wife while
    # expecting her husband sounds like a cold call; ringing her knowing who
    # she is opens with "your husband got in touch about the sink".
    phone = parsed.get("phone") or "NONE GIVEN"
    if parsed.get("phone_belongs_to"):
        phone = f"{phone}  ({parsed['phone_belongs_to']} - not their own line)"

    details = [
        f"  Name     : {parsed.get('name') or 'unknown'}",
        f"  Phone    : {phone}",
        f"  Job      : {parsed.get('job_type') or 'not stated'}",
    ]

    if parsed.get("other_phone"):
        details.append(
            f"  {'Also try':<9}: {parsed['other_phone']}  "
            f"({parsed.get('other_phone_note') or 'someone else'})")
    for label, field in (("Address", "address"), ("Urgency", "urgency"),
                         ("Property", "property_type"), ("Affected", "appliances")):
        if parsed.get(field):
            details.append(f"  {label:<9}: {parsed[field]}")

    # The customer's own words. Without this the plumber is asked to abandon the
    # job he's on without being told why -- which is exactly what happened to
    # Tom's flooding basement.
    message = (parsed.get("message") or "").strip()
    if message:
        flattened = " ".join(message.split())
        if len(flattened) > 200:
            flattened = flattened[:200].rsplit(" ", 1)[0] + "..."
        details.append(f"  {'Said':<9}: \"{flattened}\"")

    # The customer's own instruction about the second number. "Call my
    # landlord if I don't pick up" and "he'll open the door if you come after
    # 2" are different jobs on the day, and only her own words carry that.
    said = parsed.get("phone_said") or parsed.get("other_phone_said")
    if said and said != (parsed.get("message") or "").strip():
        flattened = " ".join(said.split())
        if len(flattened) > 160:
            flattened = flattened[:160].rsplit(" ", 1)[0] + "..."
        details.append(f"  {'On calls':<9}: \"{flattened}\"")

    if action == "EMAIL_AND_ALERT":
        details.append("  (a holding reply has already gone to the customer)")

    return headline, "\n".join(details)


def handle(parsed, cfg, now=None, busy=None, travel_minutes=0):
    """
    Put it all together. Returns everything the agent would do about one email,
    without actually doing any of it.

    `busy` is what the plumber's calendar says he is already doing. Leave it
    out and the agent knows his working hours only - which makes every time it
    offers a proposal rather than a promise.
    """
    # If nobody told us the time, ask the CLIENT's clock -- never our own.
    now = to_client_time(cfg, now) if now else now_for_client(cfg)
    action = decide_action(parsed)

    result = {"action": action, "windows": [], "customer_email": None,
              "subject": None, "owner_alert": None}

    if action == NOTHING:
        return result

    # Three reasons not to work out any times at all: it's an emergency (he
    # phones instead), we don't know where they are yet, or they're outside the
    # area he covers.
    too_far, drive = out_of_area(parsed, cfg)
    result["out_of_area"] = drive if too_far else None

    if not parsed.get("emergency") and not needs_address(parsed) and not too_far:
        result["windows"] = next_windows(
            cfg, now, busy=busy, travel_minutes=travel_minutes,
            customer_zip=distance.zip_from(parsed.get("address")))

    if action in (EMAIL_CUSTOMER, EMAIL_AND_ALERT):
        subject, body = build_customer_email(parsed, cfg, result["windows"], now)
        result["subject"] = subject
        result["customer_email"] = body
        result["send_to"] = parsed.get("email")

    if action in (EMAIL_AND_ALERT, ALERT_OWNER_CALL):
        result["owner_alert"] = build_owner_alert(parsed, action)

    return result
