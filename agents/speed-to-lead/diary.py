"""
diary.py  --  reads and writes the plumber's real calendar.

This is the only file that talks to Google Calendar. Everything else works on
plain lists of (start, finish) times, which is why the booking rules can be
tested without any Google account existing at all.

WHY THIS MATTERS
    Without it the agent knows the plumber's working hours but not what he has
    already booked. Every time it offers is a guess, and sooner or later two
    customers are told to expect him at once.

WHY IT WRITES AS WELL AS READS
    The agent's own bookings have to go INTO the calendar. If they don't, the
    agent cannot see the jobs it promised itself - so it books Joe 4-5pm,
    forgets, and offers 4-5pm to somebody else. That is worse than not reading
    the diary at all, because it looks like it is working.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import distance


# Read AND write. The narrower "readonly" scope was the original plan and was
# dropped - see the "WHY IT WRITES" note above.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# How the agent marks its own bookings, so it can tell them apart from jobs the
# plumber entered himself. Stored on the event, invisible to him.
OURS = "speed-to-lead"


class DiaryUnavailable(Exception):
    """
    Raised when the calendar cannot be reached or read.

    This is deliberately NOT the same as "the diary is empty". An unreachable
    calendar must never be treated as a free day - that is exactly how you
    double-book a man whose diary you cannot see. Callers are expected to stop
    offering times and tell the plumber why.
    """


def connect(key_file, calendar_id):
    """
    Log in as the robot account and check we can actually see the calendar.

    Fails EARLY and in plain English. A permission problem discovered here is a
    sentence on the screen; the same problem discovered mid-conversation is a
    customer being ignored.
    """
    try:
        creds = service_account.Credentials.from_service_account_file(
            key_file, scopes=SCOPES)
    except FileNotFoundError:
        raise DiaryUnavailable(
            f"Can't find the calendar key file '{key_file}'. It should be in "
            f"this folder. Check the name has not become '{key_file}.json' - "
            f"Windows hides file extensions and adds a second one silently.")
    except ValueError as oops:
        raise DiaryUnavailable(
            f"'{key_file}' is not a valid Google service account key: {oops}")

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    try:
        service.calendars().get(calendarId=calendar_id).execute()
    except HttpError as oops:
        raise DiaryUnavailable(_explain(oops, calendar_id,
                                        creds.service_account_email))
    return service


def _explain(oops, calendar_id, robot_email):
    """Turn a Google error code into something a human can act on."""
    status = getattr(oops.resp, "status", None)
    if status == 404:
        return (f"The calendar '{calendar_id}' has not been shared with the "
                f"agent. In Google Calendar: Settings -> click the calendar's "
                f"name -> Share with specific people -> add {robot_email} "
                f"-> permission 'Make changes to events'.")
    if status == 403:
        return (f"The agent can see '{calendar_id}' but is not allowed to "
                f"change it. The sharing permission needs to be 'Make changes "
                f"to events', not 'See all event details'. Robot account: "
                f"{robot_email}")
    if status == 401:
        return ("The calendar key was rejected. The service account may have "
                "been deleted, or its key revoked, in Google Cloud.")
    return f"Google Calendar said no ({status}): {oops.reason}"


def busy_periods(service, calendar_id, zone, first_day, last_day):
    """
    Every block of time the plumber is NOT free, between two dates.

    Returns a list of (start, finish) pairs in the client's own timezone,
    earliest first. An empty list means a genuinely empty diary. If the
    calendar cannot be read, this raises rather than returning empty - see
    DiaryUnavailable.
    """
    try:
        answer = service.events().list(
            calendarId=calendar_id,
            timeMin=first_day.isoformat(),
            timeMax=last_day.isoformat(),
            # Expands a repeating job into its individual days. Without this a
            # "every Tuesday" entry would come back as one item and the agent
            # would only ever block the first Tuesday.
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    except HttpError as oops:
        raise DiaryUnavailable(_explain(oops, calendar_id, "the agent"))
    except Exception as oops:
        # No internet, DNS trouble, Google having a bad day.
        raise DiaryUnavailable(f"Could not reach Google Calendar: {oops}")

    return to_busy(answer.get("items", []), zone)


def to_busy(events, zone):
    """
    Turn what Google sent back into plain (start, finish) pairs.

    Kept separate from the reading above so it can be tested with made-up
    events and no Google account - the same reason the parser could be built
    days before a mailbox existed.
    """
    busy = []
    for event in events:
        # Something he deleted but which still comes back in the feed.
        if event.get("status") == "cancelled":
            continue

        # He marked it "Free" - a reminder, a birthday, a note to himself.
        # He is telling us he can still work. Believe him.
        if event.get("transparency") == "transparent":
            continue

        start = _moment(event.get("start"), zone, end_of_day=False)
        finish = _moment(event.get("end"), zone, end_of_day=True)
        if start and finish and finish > start:
            # WHERE the job is, if he bothered to fill it in. Lets the agent
            # work out the real drive from that customer to the next one
            # instead of assuming a standard gap. Most plumbers won't fill it
            # in, and that is fine - there is a fallback.
            where = distance.zip_from(event.get("location"))
            busy.append((start, finish, where))

    busy.sort(key=lambda job: job[0])
    return busy


def _moment(edge, zone, end_of_day):
    """
    Read one end of an event, in the plumber's timezone.

    Google gives a timed job as 'dateTime' and an all-day job as 'date' with no
    time at all. An all-day entry means he is out - a holiday, a big job, a
    hospital appointment - so it blocks the whole day rather than a moment of
    it.
    """
    if not edge:
        return None
    if edge.get("dateTime"):
        return datetime.fromisoformat(edge["dateTime"]).astimezone(zone)
    if edge.get("date"):
        day = datetime.fromisoformat(edge["date"]).replace(tzinfo=zone)
        # Google's all-day END date is the morning AFTER the last day, which is
        # already what we want, so it needs no adjustment either way.
        return day
    return None


def clashes(start, finish, busy, travel=timedelta(0)):
    """
    Would a job from `start` to `finish` collide with anything already booked?

    `travel` is padding either side, so the plumber is not expected to teleport
    from one customer's kitchen to the next. A job that ends exactly when the
    next begins is a clash once travel time is more than zero.
    """
    for taken_from, taken_to in busy:
        if start < taken_to + travel and finish + travel > taken_from:
            return True
    return False


def add_booking(service, calendar_id, start, finish, title, notes=""):
    """
    Write a job the agent has just promised into the plumber's own calendar.

    Two reasons this is not optional. He sees the agent's jobs in the same
    diary as his own, so nothing needs reconciling. And the agent sees them
    next time it looks, so it cannot double-book him with a slot it sold five
    minutes ago.
    """
    event = {
        "summary": title,
        "description": notes,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": finish.isoformat()},
        # Marks it as ours without cluttering anything he looks at.
        "extendedProperties": {"private": {"bookedBy": OURS}},
    }
    try:
        return service.events().insert(calendarId=calendar_id,
                                       body=event).execute()
    except HttpError as oops:
        raise DiaryUnavailable(
            f"Booked the customer but could NOT write it to the calendar: "
            f"{_explain(oops, calendar_id, 'the agent')}")


def booked_by_us(event):
    """Did the agent create this, or did the plumber type it in himself?"""
    private = (event.get("extendedProperties") or {}).get("private") or {}
    return private.get("bookedBy") == OURS
