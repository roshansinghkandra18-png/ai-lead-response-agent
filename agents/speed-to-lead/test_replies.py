"""
test_replies.py  --  the inspection equipment for the REPLY ENGINE.

test_samples.py checks that the agent READS an email correctly.
This file checks that it ANSWERS one correctly.

Every check prints three things - what it fed in, what it expected back, and
what it actually got - so the saved results file can be read on its own without
opening any code.

RUN IT
    python test_replies.py
"""

from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo

import inbox
from make_reply import (
    load_config, next_windows, describe_window, handle, build_customer_email,
    decide_action, client_timezone, now_for_client, _job_phrase,
    EMAIL_CUSTOMER, EMAIL_AND_ALERT, ALERT_OWNER_CALL, NOTHING,
)

JOE = load_config("clients/joes_plumbing.ini")      # Mon-Fri 8-5, 2h, 4h notice
MARIA = load_config("clients/marias_hvac.ini")      # Mon-Sat 7-7, 3h, 2h notice

JOE_RULES = ("Joe: Mon-Fri 8am-5pm, lunch 12-1, 1h windows, 1h notice, "
             "max 3/day, 2 options")
MARIA_RULES = "Maria: Mon-SAT 7am-7pm, 3h windows, 2h notice, max 2/day, 3 options"

# Fixed dates, so the result never depends on the day you run this.
TUE = datetime(2026, 8, 11, 10, 0)
FRI_LATE = datetime(2026, 8, 14, 16, 0)
SAT = datetime(2026, 8, 15, 9, 0)
TUE_NIGHT = datetime(2026, 8, 11, 23, 0)
TUE_DAWN = datetime(2026, 8, 11, 6, 0)
FRI_PM = datetime(2026, 8, 14, 14, 0)


results = []


def check(label, actual, expected, given):
    results.append((label, actual == expected, actual, expected, given))


def check_true(label, condition, given, expected="yes"):
    results.append((label, bool(condition), "yes" if condition else "NO",
                    expected, given))


def offered(cfg, now, count=None):
    return [describe_window(w, now) for w in next_windows(cfg, now, count)]


def fake_lead(**fields):
    """A pretend parsed email, so the reply engine can be tested on its own."""
    lead = {"status": "LEAD", "name": None, "phone": None, "email": None,
            "job_type": None, "address": None, "urgency": None, "message": None,
            "emergency": False, "missing": []}
    lead.update(fields)
    return lead


# ===========================================================================
# PART 1 - WHEN THE AGENT OFFERS TO COME
# ===========================================================================

check("Tuesday 10am offers late morning, then skips over lunch",
      offered(JOE, TUE), ["today 11am-12pm", "today 1-2pm"],
      f"{JOE_RULES}. Pretend it is Tuesday 11 Aug, 10:00am. One hour's notice "
      "takes us to 11am. The next slot would be 12-1, which is his lunch, so "
      "it resumes at 1")

check("Friday 4pm skips the weekend and offers Monday",
      offered(JOE, FRI_LATE), ["Monday 8-9am", "Monday 9-10am"],
      f"{JOE_RULES}. Pretend it is Friday 14 Aug, 4:00pm")

check("Saturday morning knows he doesn't work weekends",
      offered(JOE, SAT), ["Monday 8-9am", "Monday 9-10am"],
      f"{JOE_RULES}. Pretend it is Saturday 15 Aug, 9:00am")

check("11pm doesn't offer the middle of the night",
      offered(JOE, TUE_NIGHT), ["tomorrow 8-9am", "tomorrow 9-10am"],
      f"{JOE_RULES}. Pretend it is Tuesday 11 Aug, 11:00pm")

check("an email before he opens waits for his opening time",
      offered(JOE, TUE_DAWN), ["today 8-9am", "today 9-10am"],
      f"{JOE_RULES}. Pretend it is Tuesday 11 Aug, 6:00am (before he opens). "
      "One hour's notice lands at 7am, which is still before he starts, so it "
      "waits for 8. Until 18 Aug this test expected \"today 12-2pm\" as an "
      "option - a window running straight through the lunch hour, passing as "
      "correct because Joe had no lunch break set at all")

check("Friday 2pm now keeps him working the same afternoon",
      offered(JOE, FRI_PM), ["today 3-4pm", "today 4-5pm"],
      f"{JOE_RULES}. Pretend it is Friday 14 Aug, 2:00pm. Under the old 4-hour "
      "notice this landed at 6pm - after he finished - so the customer was "
      "pushed to MONDAY and Joe lost the whole Friday afternoon. That wasted "
      "capacity is exactly why the notice came down to 1 hour")

# --- rules that must hold no matter what ---

many = next_windows(JOE, TUE_DAWN, count=12)
window_list = ", ".join(describe_window(w, TUE_DAWN) for w in many)

check_true("never offers before his day starts or after it ends",
           all(w[0].hour >= 8 and w[1].hour <= 17 for w in many),
           f"Asked for 12 windows in a row from Tuesday 6am. Got: {window_list}")

check_true("never offers a Saturday or Sunday",
           all(w[0].weekday() < 5 for w in many),
           "The same 12 windows, checking the day of the week on each")

check_true("never offers sooner than his 1 hour notice",
           all(w[0] >= TUE_DAWN + timedelta(hours=1) for w in many),
           "The same 12 windows, from Tuesday 6am. Nothing may be offered "
           "before 7am - and since he doesn't open until 8, the real earliest "
           "is 8am")

per_day = {}
for w in many:
    per_day[w[0].date()] = per_day.get(w[0].date(), 0) + 1
check("respects the 3-per-day cap", max(per_day.values()), 3,
      f"The same 12 windows, counted per day: "
      f"{ {str(d): n for d, n in per_day.items()} }")

check("every window is exactly 1 hour long",
      {int((w[1] - w[0]).total_seconds() // 3600) for w in many}, {1},
      "The same 12 windows, measuring start to finish on each. Changed from "
      "2 hours on 18 Aug: a window promises when Joe TURNS UP, not when he "
      "finishes, so a wider one means more of his day held back waiting")

# --- the lunch hour ---
#
# Checked against windows starting at 10am, NOT the 6am list above. From 6am
# his 3-a-day cap is used up by 11am, so those windows never reach lunchtime
# and these checks would pass without ever testing anything.
across_lunch = next_windows(JOE, TUE, count=6)
lunch_list = ", ".join(describe_window(w, TUE) for w in across_lunch)

# A window clashes with the 12-1 lunch if it starts before 1pm AND finishes
# after 12. Finishing exactly at 12 is fine, and starting exactly at 1 is fine.
clashes_with_lunch = [w for w in across_lunch
                      if w[0].hour < 13 and w[1].hour > 12]

check("no window ever runs through Joe's lunch", clashes_with_lunch, [],
      f"Six windows from Tuesday 10am: {lunch_list}. His lunch is 12-1. A "
      "window may END at 12:00 and may START at 1:00, but none may sit inside "
      "the hour or straddle it")

check_true("a window may finish exactly at the start of lunch",
           any(w[1].hour == 12 for w in across_lunch),
           f"The same six windows: {lunch_list}. 11am-12pm is fine - he stops "
           "and eats. Blocking that too would cost him an hour a day for no "
           "reason")

check_true("the window after lunch starts at 1pm, not 12",
           any(w[0].hour == 13 for w in across_lunch),
           f"The same six windows: {lunch_list}. He picks back up at 1pm once "
           "he has eaten")


# ===========================================================================
# PART 2 - A COMPLETELY DIFFERENT CLIENT
# Proves the settings file really controls the agent, rather than Joe's rules
# being baked into the code.
# ===========================================================================

maria_sat = offered(MARIA, SAT)

check("Maria DOES work Saturdays, so she gets offered Saturday",
      maria_sat[0], "today 1-4pm",
      f"{MARIA_RULES}, lunch 12-1. Pretend it is Saturday 15 Aug, 9:00am - the "
      "exact same moment where Joe was pushed to Monday. 9am + 2h notice = 11am, "
      "but an 11am-2pm window would run through her lunch, so it starts at 1pm")

check("Maria is offered 3 options, not Joe's 2", len(maria_sat), 3,
      f"Her settings say options_to_offer = 3. She got: {maria_sat}")

maria_windows = next_windows(MARIA, SAT)
check("Maria's windows are 3 hours long, not 2",
      {int((w[1] - w[0]).total_seconds() // 3600) for w in maria_windows}, {3},
      "Her settings say window_hours = 3")

check_true("Maria can come the same day; Joe cannot",
           maria_windows[0][0].date() == SAT.date()
           and next_windows(JOE, SAT)[0][0].date() != SAT.date(),
           f"Same instant, Saturday 15 Aug 9am. Maria: "
           f"{describe_window(maria_windows[0], SAT)}. Joe: "
           f"{describe_window(next_windows(JOE, SAT)[0], SAT)}")

maria_many = next_windows(MARIA, SAT, count=8)
maria_per_day = {}
for w in maria_many:
    maria_per_day[w[0].date()] = maria_per_day.get(w[0].date(), 0) + 1
check("Maria's cap is 2 a day, not Joe's 3", max(maria_per_day.values()), 2,
      f"Asked for 8 windows. Counted per day: "
      f"{ {str(d): n for d, n in maria_per_day.items()} }")


# ===========================================================================
# PART 3 - WHO GETS TOLD WHAT
# ===========================================================================

check("normal lead with an email address gets emailed",
      decide_action(fake_lead(email="a@b.com", name="Ann")), EMAIL_CUSTOMER,
      "A lead with name Ann and email a@b.com, not an emergency")

check("lead with only a phone number means the plumber must call",
      decide_action(fake_lead(phone="555-1234", name="Ann")), ALERT_OWNER_CALL,
      "A lead with a phone number but NO email address")

check("emergency with an email gets both a reply AND an alert",
      decide_action(fake_lead(email="a@b.com", emergency=True)), EMAIL_AND_ALERT,
      "A lead marked emergency, with an email address")

check("emergency with no email means call them, now",
      decide_action(fake_lead(phone="555-1234", emergency=True)), ALERT_OWNER_CALL,
      "A lead marked emergency, phone only, no email address")

check("junk mail produces nothing at all",
      decide_action({"status": "SKIP_NOT_LEAD"}), NOTHING,
      "An email the parser decided was junk")

check("an auto-reply produces nothing at all",
      decide_action({"status": "SKIP_AUTO"}), NOTHING,
      "An out-of-office or bounce message")

check("a customer replying to us is not treated as a new lead",
      decide_action({"status": "THREAD_REPLY"}), NOTHING,
      "A customer replying inside a conversation we already started")


# ===========================================================================
# PART 4 - WHAT THE EMAIL ACTUALLY SAYS
# ===========================================================================

def subject_and_body(lead, cfg=JOE, now=TUE):
    windows = [] if lead.get("emergency") else next_windows(cfg, now)
    return build_customer_email(lead, cfg, windows, now)


subj, body = subject_and_body(fake_lead(name="John", job_type="Leak",
                                        email="j@x.com"))
check("'leak' reads fine on its own - no 'issue' added", subj, "Re: your leak",
      "A lead whose job type is 'Leak'")

check_true("greets him by first name only", "Hi John," in body,
           "The same lead. Opening line of the email was: "
           f"\"{body.splitlines()[0]}\"")

subj, _ = subject_and_body(fake_lead(name="Angela", job_type="Shower",
                                     email="a@x.com"))
check("'shower' alone sounds clipped, so becomes 'shower issue'",
      subj, "Re: your shower issue",
      "A lead whose job type is just 'Shower' - a bare appliance name")

subj, _ = subject_and_body(fake_lead(name="Sam", job_type="Water Heater Repair",
                                     email="s@x.com"))
check("a job that already describes work is left alone",
      subj, "Re: your water heater repair",
      "A lead whose job type is 'Water Heater Repair' - already a piece of work,"
      " so 'issue' must NOT be added")

subj, _ = subject_and_body(fake_lead(name="Diane", job_type="No Hot Water",
                                     email="d@x.com"))
check("'no hot water' is said the way a plumber would say it",
      subj, "Re: your water heater issue",
      "A lead whose job type is 'No Hot Water' - a description of what is NOT "
      "working, not the name of a thing. Said back literally it becomes 'your "
      "no hot water issue', which is grammatical and obviously machine-written")

subj, _ = subject_and_body(fake_lead(name="Ed", job_type="No Water",
                                     email="e@x.com"))
check("'no water' is said the way a plumber would say it",
      subj, "Re: your water supply issue",
      "A lead whose job type is 'No Water' - same problem, would have read as "
      "'your no water issue'")

check_true("the plumber's log still gets the symptom, not the tidied name",
           _job_phrase({"job_type": "No Hot Water"}) == "water heater issue",
           "Only the words the CUSTOMER reads are changed. leads.csv still "
           "records 'No Hot Water', because knowing the symptom before setting "
           "off is worth more to the plumber than a tidy job name")

subj, body = subject_and_body(fake_lead(name="Tom", email="t@x.com",
                                        emergency=True))
check("unknown job never produces 'your your'", subj, "Re: your plumbing job",
      "A lead with NO job type at all - this is what produced the old bug "
      "'Re: your your plumbing job request'")

check_true("emergency email says it's urgent", "urgent" in body.lower(),
           "The same emergency lead. Email body was:\n"
           + "\n".join(f"            {l}" for l in body.splitlines()))

check_true("emergency email does NOT offer appointment times",
           "reply with 1" not in body.lower(),
           "The same emergency email - a flooding customer must never be asked "
           "to pick between Tuesday and Wednesday")

# ---------------------------------------------------------------------------
# THE ADDRESS COMES FIRST  (changed 18 August 2026)
#
# The agent used to ask only for the zip, offer times anyway, and collect the
# street later. That was reversed: it cannot work out how long the plumber
# takes to drive there, or whether the customer is even in his area, without a
# street address - and both have to be settled BEFORE a time is promised.
# ---------------------------------------------------------------------------

no_address = fake_lead(name="Ann", job_type="Leak", email="a@x.com",
                       missing=["address"])
_, body = subject_and_body(no_address)

check_true("asks for the full street address when the form didn't give one",
           "street address" in body.lower(),
           "A lead where the form captured no address. Joe's settings say to "
           "ask \"What's your full street address?\"\n"
           "         Email body was:\n"
           + "\n".join(f"            {l}" for l in body.splitlines()))

check_true("offers NO appointment times until it knows the address",
           "reply with 1" not in body.lower(),
           "The same lead. Promising a time before knowing where they live is "
           "how you promise a slot you can't keep - or can't drive to")

check_true("no times are even worked out when the address is missing",
           handle(no_address, JOE)["windows"] == [],
           "The same lead, checking the agent doesn't quietly compute windows "
           "it then hides. Nothing should be worked out at all")

check_true("tells the customer WHY it wants the address",
           "area we cover" in body.lower(),
           "The same lead. \"What's your address\" from a machine reads like "
           "data collection; giving the reason reads like someone helping")

check_true("never asks for the zip code any more",
           "zip code" not in body.lower(),
           "The same lead. The zip-only question was reversed on 18 August "
           "and must not come back")

_, body = subject_and_body(fake_lead(name="Ann", job_type="Leak",
                                     email="a@x.com", missing=[]))
check_true("asks NOTHING when the form already told us everything",
           "street address" not in body.lower() and "how soon" not in body.lower(),
           "A lead where the form gave both address and urgency - asking again "
           "would insult the customer")

check_true("still offers times normally once it has the address",
           "reply with 1" in body.lower(),
           "The same complete lead. The address rule must not stop ordinary "
           "leads getting appointment times")

_, body = subject_and_body(fake_lead(name="Ann", job_type="Leak",
                                     email="a@x.com", missing=["address", "urgency"]))
check_true("never asks two questions at once",
           not ("street address" in body.lower() and "how soon" in body.lower()),
           "A lead missing BOTH address and urgency. Only one question allowed")

check_true("asks for the address first when both are missing",
           "street address" in body.lower(),
           "The same lead. The address is the one that blocks everything else, "
           "so it wins")

_, body = subject_and_body(fake_lead(name="Ann", job_type="Leak", email="a@x.com"),
                           cfg=MARIA)
check_true("signs off with the right business name",
           "Maria's Heating & Air" in body,
           "The same lead, but run through Maria's settings instead of Joe's. "
           f"Sign-off line was: \"{body.splitlines()[-1]}\"")

outcome = handle(fake_lead(name="Tom", phone="312-555-9034", emergency=True,
                           job_type="Flooding",
                           message="My basement is flooding right now."),
                 JOE, now=TUE)
check_true("emergency alert tells the plumber WHY he's being interrupted",
           "flooding right now" in outcome["owner_alert"][1],
           "Tom, flooding basement, phone only. The plumber's alert said:\n"
           + "\n".join(f"            {l}"
                       for l in outcome["owner_alert"][1].splitlines()))

check_true("emergency alert is clearly marked as an emergency",
           "EMERGENCY" in outcome["owner_alert"][0],
           f"The same alert. Its headline was: \"{outcome['owner_alert'][0]}\"")


# ===========================================================================
# PART 5 - THE CLOCK
# The agent runs on a laptop in India. Every client is in the United States.
# These checks prove it uses the CLIENT's clock and ignores ours.
# ===========================================================================

INDIA = ZoneInfo("Asia/Kolkata")

# 6:30pm Tuesday in India is 9:00am the SAME Tuesday in Ohio.
# If the agent used our clock it would think the working day was over and
# push everything to tomorrow - losing a same-day job.
india_evening = datetime(2026, 8, 11, 18, 30, tzinfo=INDIA)

check("laptop in India, client in Ohio - uses OHIO's clock",
      offered(JOE, india_evening), ["today 10-11am", "today 11am-12pm"],
      "It is 6:30pm Tuesday in India, which is 9:00am Tuesday in Ohio. "
      f"{JOE_RULES}")

check_true("does NOT push a same-day job to tomorrow",
           "tomorrow 8-9am" not in offered(JOE, india_evening),
           "This is exactly what the bug did: our 6:30pm looked like the end of "
           "the working day, so a customer who emailed at 9am their time was "
           "told 'tomorrow'")

# The same instant, a client in Texas. One hour behind Ohio.
check("same moment, a Texas client gets Texas times",
      offered(MARIA, india_evening),
      ["today 1-4pm", "today 4-7pm", "tomorrow 7-10am"],
      "The SAME instant (6:30pm in India) but Maria is in Texas, where it is "
      f"8:00am. {MARIA_RULES}, lunch 12-1")

check("Joe is on New York time", str(client_timezone(JOE)), "America/New_York",
      "Read from the timezone line in clients/joes_plumbing.ini")

check("Maria is on Chicago time", str(client_timezone(MARIA)), "America/Chicago",
      "Read from the timezone line in clients/marias_hvac.ini")

check_true("asking 'what time is it now' returns the CLIENT's local time",
           str(now_for_client(JOE).tzinfo) == "America/New_York",
           "Called now_for_client() with Joe's settings. It returned "
           f"{now_for_client(JOE).strftime('%A %d %b, %I:%M%p %Z')}, while this "
           f"laptop says {datetime.now().strftime('%A %d %b, %I:%M%p')}")

check_true("two clients in different zones get different local times",
           now_for_client(JOE).hour != now_for_client(MARIA).hour,
           f"At this instant it is {now_for_client(JOE).strftime('%I:%M%p')} for "
           f"Joe in Ohio and {now_for_client(MARIA).strftime('%I:%M%p')} for "
           "Maria in Texas")


# ===========================================================================
# PART 6 - PUBLIC HOLIDAYS AND LUNCH BREAKS
# ===========================================================================

from make_reply import us_holidays, days_off  # noqa: E402

h26 = us_holidays(2026)

check("works out Thanksgiving 2026 without being told the date",
      h26["thanksgiving"], date(2026, 11, 26),
      "Thanksgiving is the 4th Thursday of November. Nothing is typed in - the "
      "agent counts the Thursdays itself, so this still works in 2030")

check("July 4th 2026 falls on a Saturday, so it's taken on the Friday",
      h26["independence day"], date(2026, 7, 3),
      "4 July 2026 is a Saturday. American businesses take the Friday before")

check("Memorial Day is the LAST Monday in May, not the first",
      h26["memorial day"], date(2026, 5, 25),
      "Counting backwards from the end of May 2026")

# Wednesday 25 Nov 2026, 4pm. Four hours later is 8pm, so the next option would
# be Thursday - which is Thanksgiving.
check("does not offer Thanksgiving Day",
      offered(JOE, datetime(2026, 11, 25, 16, 0)),
      ["Friday 8-9am", "Friday 9-10am"],
      "Pretend it is Wednesday 25 Nov 2026, 4:00pm. The next working morning "
      "would be Thursday 26th - Thanksgiving. Joe observes it, so it must skip "
      "to Friday")

# Thursday 2 July 2026. Friday 3rd is the observed 4th of July, then a weekend.
check("skips an observed holiday AND the weekend behind it",
      offered(JOE, datetime(2026, 7, 2, 16, 0)),
      ["Monday 8-9am", "Monday 9-10am"],
      "Pretend it is Thursday 2 July 2026, 4:00pm. Friday 3rd is Independence "
      "Day (moved from the Saturday), then Sat and Sun. Next is Monday 6th")

check_true("Joe's day off list contains 6 holidays for 2026",
           len(days_off(JOE, 2026)) == 6,
           f"From his settings file: {sorted(str(d) for d in days_off(JOE, 2026))}")

check_true("Maria's extra days off are included too",
           date(2026, 8, 24) in days_off(MARIA, 2026),
           "Her settings say extra = 08/24/2026,08/25/2026 - her own holiday")

# --- lunch breaks ---

check("a morning window that finishes BEFORE lunch is allowed",
      offered(MARIA, datetime(2026, 8, 11, 6, 0)),
      ["today 8-11am", "today 1-4pm", "tomorrow 7-10am"],
      "6am + her 2h notice = 8am. An 8-11am window finishes before her 12:00 "
      "lunch, so it is fine. The next one, 11am-2pm, would run through it - so "
      "the agent jumps to 1pm instead")

check("a window that would run through lunch is skipped",
      offered(MARIA, datetime(2026, 8, 11, 8, 0)),
      ["today 1-4pm", "today 4-7pm", "tomorrow 7-10am"],
      "8am + 2h notice = 10am. A 10am-1pm window covers her whole 12-1 lunch, "
      "so it is refused and the day restarts at 1pm")

maria_day = next_windows(MARIA, datetime(2026, 8, 11, 6, 0), count=6)
check_true("no window of Maria's overlaps 12:00-13:00",
           all(not (w[0].time() < time(13, 0) and w[1].time() > time(12, 0))
               for w in maria_day),
           "Checked every window she would ever be offered that day: "
           + ", ".join(describe_window(w, datetime(2026, 8, 11, 6, 0))
                       for w in maria_day))

# --- telling the customer WHY there's a delay ---

def body_at(now, cfg=JOE):
    lead = fake_lead(name="John", job_type="Leak", email="j@x.com")
    return build_customer_email(lead, cfg, next_windows(cfg, now), now)[1]

july = body_at(datetime(2026, 7, 2, 16, 0))
check_true("explains a holiday delay instead of just looking slow",
           "closed Friday for the 4th of July" in july,
           "Customer emails Thursday 2 July 2026 at 4pm and is offered Monday. "
           "Without an explanation the plumber looks slow. The email said:\n"
           + "\n".join(f"            {l}" for l in july.splitlines()))

thanks = body_at(datetime(2026, 11, 25, 16, 0))
check_true("names the right holiday, not a generic 'we're closed'",
           "closed Thursday for Thanksgiving" in thanks,
           "Customer emails the day before Thanksgiving 2026")

on_the_day = body_at(datetime(2026, 11, 26, 10, 0))
check_true("customer emailing ON the holiday is told it's today",
           "closed today for Thanksgiving" in on_the_day,
           "Customer emails at 10am on Thanksgiving Day itself. The email said:\n"
           + "\n".join(f"            {l}" for l in on_the_day.splitlines()))

check_true("...and is still offered the next working times",
           "1 - " in on_the_day and "reply with 1" in on_the_day.lower(),
           "Being closed today must not mean the customer is left with nothing")

xmas = body_at(datetime(2026, 12, 25, 9, 0))
check_true("works for Christmas too, not just Thanksgiving",
           "closed today for Christmas" in xmas,
           "Customer emails at 9am on Christmas Day 2026, which is a Friday")

ordinary = body_at(datetime(2026, 8, 11, 10, 0))
check_true("says nothing about holidays on an ordinary day",
           "closed" not in ordinary.lower(),
           "Customer emails Tuesday 11 Aug 2026, an ordinary working day. The "
           "email opened with: \"" + ordinary.splitlines()[4] + "\"")

check_true("Joe's lunch hour is never offered to a customer",
           not any(w[0].hour == 12 for w in across_lunch),
           "Six windows from Tuesday 10am, which is late enough to reach "
           "lunchtime. His settings say lunch_start 12:00, lunch_end 13:00. "
           "Until 18 Aug both were blank, so the agent believed he worked 8 to "
           "5 without eating and would happily promise somebody 12-2pm")


# ===========================================================================
# PART 7 - THE SETTINGS CHECKER
# Run before onboarding a client. It must explain what's wrong in plain
# English, never crash with technical error text while a client is watching.
# ===========================================================================

import check_client  # noqa: E402


def problems_in(path):
    check_client.check(path)
    return check_client.problems


check("a good settings file reports no problems at all",
      len(problems_in("clients/joes_plumbing.ini")), 0,
      "Joe's real settings file")

check("a second good file is judged on its own, not the first one's faults",
      len(problems_in("clients/marias_hvac.ini")), 0,
      "Maria's file, checked straight after Joe's - proves problems from one "
      "client don't leak into the next")

broken = problems_in("clients/EXAMPLE-broken-on-purpose.ini")
found = " | ".join(f"{setting} {wrong}" for setting, wrong, _ in broken)

check("the deliberately broken file reports 10 problems", len(broken), 10,
      "clients/EXAMPLE-broken-on-purpose.ini, which contains the mistakes a "
      "person actually makes filling one in for the first time")

for label, needle in [
    ("catches an email address with no @ in it", "owner_email"),
    ("catches a timezone that doesn't exist", "timezone"),
    ("catches a misspelled day of the week", "working_days"),
    ("catches a time written as 8am instead of 08:00", "start"),
    ("catches a lunch break with only one end filled in", "lunch_start"),
    ("catches a number written as a word", "minimum_notice_hours"),
    ("catches a required question left blank", "missing_urgency"),
    ("catches a holiday name it doesn't know", "observed"),
    ("catches a date written the British way round", "extra"),
]:
    check_true(label, any(needle in setting for setting, _, _ in broken),
               f"All problems found in the broken file: {found}")

check_true("every problem comes with the exact line to write instead",
           all(fix.strip() for _, _, fix in broken),
           "So you can fix it on the call without knowing anything technical")


# --- the envelope: is the reply really attached to their email? ---
#
# Every email carries a hidden reference number. A reply that carries the
# number of the message it answers gets filed underneath it, the way a human's
# reply does. Without it we send a loose new email with "Re:" typed on the
# front - which reads as unsolicited to the customer's mail provider, and is
# the difference between the inbox and the junk folder.

CUSTOMER_STAMP = "<abc123@mail.gmail.com>"

threaded = inbox.build_message(
    "joe@joesplumbing.com", "angela@example.com",
    "Re: your water heater repair", "Hi Angela,",
    in_reply_to=CUSTOMER_STAMP)

check("a reply is stamped as answering the customer's own email",
      threaded["In-Reply-To"], CUSTOMER_STAMP,
      "A reply to Angela, who wrote in from angela@example.com. Her email "
      f"carried the reference number {CUSTOMER_STAMP}")

check("the conversation so far is carried along too",
      threaded["References"], CUSTOMER_STAMP,
      "The same reply. 'References' is the whole conversation, oldest first, "
      "so a long back-and-forth stays as ONE conversation instead of "
      "splitting in half partway through")

longer = inbox.build_message(
    "joe@joesplumbing.com", "angela@example.com", "Re: x", "body",
    in_reply_to="<third@mail>", references="<first@mail> <second@mail>")

check("a longer conversation keeps every message in order",
      longer["References"], "<first@mail> <second@mail> <third@mail>",
      "The third reply in a conversation that already had two messages in it")

loose = inbox.build_message(
    "joe@joesplumbing.com", "rosa@example.com", "Re: your toilet", "Hi Rosa,")

check_true("no stamp is invented when there is nothing to answer",
           loose["In-Reply-To"] is None and loose["References"] is None,
           "A forwarded enquiry, where the reference number belongs to the "
           "office assistant's email and not to anything the customer ever "
           "saw. Claiming to answer a conversation she was never part of "
           "helps nobody",
           expected="no stamp at all")

check("the reply still says who it is from",
      loose["From"], "joe@joesplumbing.com",
      "The same reply - the ordinary parts must not break because of the "
      "threading change")

check("the reply still goes to the right person",
      loose["To"], "rosa@example.com",
      "The same reply")

check_true("the message body survives intact",
           "Hi Rosa," in loose.get_content(),
           "The same reply - the words the customer actually reads")


# ===========================================================================
# THE SCORE
# ===========================================================================

def run():
    passed = failed = 0
    for label, ok, actual, expected, given in results:
        mark = "pass" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"[{mark}] {label}")
        print(f"       fed in  : {given}")
        print(f"       expected: {expected}")
        print(f"       got     : {actual}")
        print()
    print("=" * 70)
    print(f"  {passed} passed, {failed} failed, {len(results)} total")
    print("=" * 70)


if __name__ == "__main__":
    run()
