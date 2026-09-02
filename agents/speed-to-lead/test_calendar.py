"""
test_calendar.py  --  the inspection equipment for THE DIARY AND THE DRIVING.

test_samples.py  checks the agent READS an email correctly.
test_replies.py  checks it ANSWERS one correctly.
This file checks it knows WHERE the customer is and WHEN the plumber is free.

None of these checks touch Google. The calendar's event-reading and the
distance maths are both plain functions fed made-up data, which is why they can
run in a second with no account, no key file and no internet.

RUN IT
    python test_calendar.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import diary
import distance
from make_reply import load_config, next_windows, collides, handle
from parse_lead import parse_email

JOE = load_config("clients/joes_plumbing.ini")
OHIO = ZoneInfo("America/New_York")

JOE_RULES = ("Joe: based in zip 44113 (downtown Cleveland), will travel up to "
             "90 minutes, assumes 40mph, works Mon-Fri 8am-5pm with lunch 12-1")

results = []


def check(label, actual, expected, given):
    results.append((label, actual == expected, actual, expected, given))


def check_true(label, condition, given, expected="yes"):
    results.append((label, bool(condition), "yes" if condition else "NO",
                    expected, given))


def at(hour, minute=0, day=19):
    """A moment on Wednesday 19 August 2026, in Joe's timezone."""
    return datetime(2026, 8, day, hour, minute, tzinfo=OHIO)


def shown(windows):
    return [f"{w[0]:%a %d %b %H:%M}-{w[1]:%H:%M}" for w in windows]


# ===========================================================================
# PART A - FINDING THE CUSTOMER ON A MAP
# ===========================================================================

check("pulls the zip out of a normal American address",
      distance.zip_from("1428 Detroit Ave, Lakewood, OH 44107"), "44107",
      'Fed in the address a customer would actually type')

check("understands a ZIP+4",
      distance.zip_from("44107-1234"), "44107",
      'The "+4" is a delivery route and says nothing about position, so it '
      'is thrown away')

check("says nothing when there is no address",
      distance.zip_from("my kitchen sink is leaking"), None,
      "A customer who never mentioned where they live. Guessing would be "
      "worse than admitting we don't know")

check("is not fooled by a house number that looks like a zip",
      distance.zip_from("44120 State Route 7, Cleveland OH 44113"), "44113",
      "Both numbers are five digits. The zip is the one at the END of a US "
      "address, and the one the agent must use")

check("handles being given nothing at all",
      distance.zip_from(None), None,
      "A lead where the address field was empty. Must not crash")


# ===========================================================================
# PART B - HOW LONG THE DRIVE TAKES
# ===========================================================================

lakewood = distance.minutes_between("44113", "44107", JOE)
bay_village = distance.minutes_between("44113", "44140", JOE)
mentor = distance.minutes_between("44113", "44060", JOE)
columbus = distance.minutes_between("44113", "43215", JOE)

check_true("the next suburb is a short drive",
           10 <= lakewood <= 20,
           f"{JOE_RULES}. Downtown Cleveland (44113) to Lakewood (44107) is "
           f"about 7 road miles. The agent said {lakewood} minutes; the real "
           f"drive is about 10",
           expected="between 10 and 20 minutes")

check_true("the outer suburbs are reachable, not rejected",
           20 <= bay_village <= 35,
           f"Downtown Cleveland to Bay Village (44140), about 16 road miles. "
           f"The agent said {bay_village} minutes; the real drive is about "
           f"20-25 on I-90. THIS CHECK EXISTS BECAUSE IT ONCE FAILED: with the "
           f"speed set to 30mph the agent called it 35 minutes and turned the "
           f"customer away",
           expected="between 20 and 35 minutes")

check_true("a job across the city is still worth doing",
           mentor <= 90,
           f"Downtown Cleveland to Mentor (44060), about 30 road miles. Agent "
           f"said {mentor} minutes, and Joe will travel up to 90",
           expected="within his 90 minute limit")

check_true("the other end of the state is not",
           columbus > 90,
           f"Cleveland to Columbus (43215), about 163 road miles. Agent said "
           f"{columbus} minutes. (The real drive is nearer 135 - our estimate "
           f"is poor over long distances, which is why the customer is never "
           f"told the number)",
           expected="beyond his 90 minute limit")

check("the same zip is never zero minutes",
      distance.minutes_between("44113", "44113", JOE), 5,
      "Two jobs in the same zip code. Even next door takes a few minutes to "
      "park and carry the tools in, so the floor is 5 minutes")

check("an unknown zip falls back to his standard gap",
      distance.minutes_between("44113", "99999", JOE),
      int(JOE["travel"]["default_minutes"]),
      "A zip that is not in the file at all. A sensible standard gap beats a "
      "made-up number")


# ===========================================================================
# PART C - IS THE CUSTOMER IN HIS AREA?
# ===========================================================================

check("a customer down the road is accepted",
      distance.too_far("44107", JOE)[0], False,
      f"{JOE_RULES}. Lakewood is 7 miles away")

check("a customer in the outer suburbs is accepted",
      distance.too_far("44140", JOE)[0], False,
      "Bay Village, 16 miles. Turning these away would cost Joe some of his "
      "best-paying work")

check("a customer two hours away is turned away",
      distance.too_far("43215", JOE)[0], True,
      "Columbus. Better a polite no in 60 seconds than a job he resents")

check("a customer in California is turned away",
      distance.too_far("90210", JOE)[0], True,
      "Beverly Hills, 2,600 miles. Somebody filled in the wrong form")

check("an unknown zip is NOT turned away",
      distance.too_far("99999", JOE)[0], False,
      "A zip missing from our file. Refusing a real customer because a data "
      "file has a gap is a far worse mistake than driving further than usual")

check("a customer with no address at all is NOT turned away",
      distance.too_far(None, JOE)[0], False,
      "We cannot judge what we do not know. The agent asks for the address "
      "instead")

no_travel_settings = load_config("clients/marias_hvac.ini")
check("a client whose settings predate all this still works",
      distance.too_far("44107", no_travel_settings)[0], False,
      "Maria's settings file has no [travel] section - she was never asked "
      "how far she travels. An older settings file must never crash the "
      "agent, and must never turn a customer away on a question nobody put "
      "to her")


# ===========================================================================
# PART D - DOES A JOB CLASH WITH ONE ALREADY BOOKED?
# ===========================================================================

booked = [(at(9), at(10))]          # one job, 9-10am Wednesday

check("a clear afternoon does not clash",
      collides(at(14), at(15), booked, timedelta(0)), None,
      "Joe is booked 9-10am. Asked about 2-3pm the same day")

check_true("a job on top of another one clashes",
           collides(at(9, 30), at(10, 30), booked, timedelta(0)) is not None,
           "Joe is booked 9-10am. Asked about 9:30-10:30, which lands on top "
           "of it")

check("back-to-back is fine when there is no travel time",
      collides(at(10), at(11), booked, timedelta(0)), None,
      "Joe is booked 9-10am. Asked about 10-11am with zero travel allowed - "
      "he walks out of one and into the next")

check_true("back-to-back CLASHES once travel time is allowed for",
           collides(at(10), at(11), booked, timedelta(minutes=30)) is not None,
           "The same 10-11am slot, but Joe needs 30 minutes to drive. He "
           "cannot be in two places at once. THIS is the fault that would "
           "have made him late to every second job")

check("says exactly when he is next genuinely free",
      collides(at(10), at(11), booked, timedelta(minutes=30)), at(10, 30),
      "Booked until 10am, needs 30 minutes to drive, so he is free at 10:30")


# ===========================================================================
# PART E - THE AGENT READING A REAL CALENDAR ENTRY
# ===========================================================================

timed = diary.to_busy([{
    "summary": "Running toilet",
    "start": {"dateTime": "2026-08-19T09:00:00-04:00"},
    "end": {"dateTime": "2026-08-19T10:00:00-04:00"},
}], OHIO)
check("an ordinary job blocks exactly its own hour",
      shown(timed), ["Wed 19 Aug 09:00-10:00"],
      "A normal 9-10am entry in the plumber's calendar")

all_day = diary.to_busy([{
    "summary": "Bathroom refit",
    "start": {"date": "2026-08-20"},
    "end": {"date": "2026-08-21"},
}], OHIO)
check("an all-day entry blocks the whole day",
      shown(all_day), ["Thu 20 Aug 00:00-00:00"],
      "An all-day entry, which is how a plumber marks a big job, a holiday or "
      "a hospital appointment. Google gives no times at all, so it must block "
      "the entire day rather than a moment of it")

free_marked = diary.to_busy([{
    "summary": "Someone's birthday",
    "transparency": "transparent",
    "start": {"dateTime": "2026-08-19T09:00:00-04:00"},
    "end": {"dateTime": "2026-08-19T10:00:00-04:00"},
}], OHIO)
check("an entry he marked FREE does not block anything",
      shown(free_marked), [],
      "A birthday reminder, marked 'Free' in Google Calendar. He is telling "
      "us he can still work. Believe him")

cancelled = diary.to_busy([{
    "summary": "Cancelled job",
    "status": "cancelled",
    "start": {"dateTime": "2026-08-19T09:00:00-04:00"},
    "end": {"dateTime": "2026-08-19T10:00:00-04:00"},
}], OHIO)
check("a cancelled job does not block anything",
      shown(cancelled), [],
      "A job he deleted. Google still sends it in the feed, and blocking it "
      "would cost him a slot he had deliberately freed up")

junk = diary.to_busy([{"summary": "broken entry"}], OHIO)
check("a broken entry is skipped rather than crashing",
      shown(junk), [],
      "An entry with no start or end at all. One bad row must never stop the "
      "agent answering the rest of the day's customers")


# ===========================================================================
# PART F - WHAT THE CUSTOMER ACTUALLY GETS OFFERED
# ===========================================================================

morning_job = [(at(9), at(10))]
offers = next_windows(JOE, at(8), count=3, busy=morning_job, travel_minutes=30)
check("the booked hour and the drive around it are both skipped",
      shown(offers)[:1], ["Wed 19 Aug 10:30-11:30"],
      f"{JOE_RULES}. He is booked 9-10am and a customer emails at 8am. "
      f"1 hour's notice allows 9am, but that is taken; +30 minutes to drive "
      f"means 10:30 is the first honest offer. Got: {shown(offers)}")

full_day = [(at(8, 0, 20), at(17, 0, 20))]
after_full = next_windows(JOE, at(8), count=2, busy=full_day,
                          travel_minutes=30)
check_true("a day booked wall-to-wall offers nothing at all that day",
           all(w[0].day != 20 for w in after_full),
           f"Thursday 20 Aug is booked 8am-5pm solid. Nothing on Thursday may "
           f"be offered. Got: {shown(after_full)}")

two_days = [(datetime(2026, 8, 24, 8, tzinfo=OHIO),
             datetime(2026, 8, 25, 17, tzinfo=OHIO))]
across = next_windows(JOE, datetime(2026, 8, 24, 8, tzinfo=OHIO), count=2,
                      busy=two_days, travel_minutes=30)
check_true("a job spanning two days blocks BOTH days",
           all(w[0].day not in (24, 25) for w in across),
           f"A whole-house repipe running Monday 8am to Tuesday 5pm. Neither "
           f"day may be offered. Got: {shown(across)}")

with_diary = next_windows(JOE, at(8), count=3, busy=morning_job,
                          travel_minutes=30)
without_diary = next_windows(JOE, at(8), count=3)
check_true("knowing the diary changes the answer",
           shown(with_diary) != shown(without_diary),
           f"The same customer, same moment, with and without reading the "
           f"calendar.\n"
           f"         Blind : {shown(without_diary)}\n"
           f"         Seeing: {shown(with_diary)}")

check("an empty diary behaves exactly as before",
      shown(next_windows(JOE, at(8), count=3, busy=[], travel_minutes=30)),
      shown(next_windows(JOE, at(8), count=3)),
      "A plumber with nothing booked. Reading an empty calendar must not "
      "change a thing")


# ===========================================================================
# PART F2 - THE DRIVE FROM THE PREVIOUS CUSTOMER
#
# When the plumber fills the address in on his own calendar entry, the agent
# works out the real drive from THAT job to this one, instead of assuming a
# standard gap. Most plumbers won't fill it in, so the fallback matters as
# much as the clever bit.
# ===========================================================================

# The same 9-10am job, with an address on it. Once next door to the customer,
# once right across the city.
next_door = [(at(9), at(10), "44113")]      # same zip as the customer
across_town = [(at(9), at(10), "44060")]    # Mentor, 30 miles east

close_offers = next_windows(JOE, at(8), count=1, busy=next_door,
                            travel_minutes=30, customer_zip="44113")
far_offers = next_windows(JOE, at(8), count=1, busy=across_town,
                          travel_minutes=30, customer_zip="44113")

check("a job on the same street is offered at the very next slot",
      shown(close_offers), ["Wed 19 Aug 10:30-11:30"],
      "Joe finishes at 10am in zip 44113 and the new customer is also in "
      "44113 - a 5 minute drive, so he is free at 10:05. Appointments start "
      "every 30 minutes, so 10:00 is too early and 10:30 is the next honest "
      "offer. A short drive gets absorbed by the grid, which is exactly why "
      "it is not worth measuring drives to the minute")

check("a job across the city pushes the next one much later",
      shown(far_offers), ["Wed 19 Aug 11:00-12:00"],
      "The same 9-10am job, but that customer is in Mentor (44060), 30 miles "
      "from the new one. Roughly a 50 minute drive, so the earliest honest "
      "offer is 11")

check_true("a long drive DOES change the answer",
           shown(close_offers) != shown(far_offers),
           f"Same plumber, same diary, same moment - only the distance "
           f"between the two customers changed. Short drives vanish into the "
           f"30-minute grid; long ones do not, which is where knowing the "
           f"real distance earns its keep.\n"
           f"         Next door  : {shown(close_offers)}\n"
           f"         Across town: {shown(far_offers)}")

no_address_on_it = [(at(9), at(10), None)]
fallback = next_windows(JOE, at(8), count=1, busy=no_address_on_it,
                        travel_minutes=30, customer_zip="44113")
check("a diary entry with no address falls back to the standard gap",
      shown(fallback), ["Wed 19 Aug 10:30-11:30"],
      "Joe left the location blank on his own calendar entry, which is what "
      "most plumbers do. The agent uses his standard 30 minute gap rather "
      "than guessing, so 10:30 is the first offer")


# ===========================================================================
# PART G - THE WHOLE REPLY, FOR A CUSTOMER TOO FAR AWAY
# ===========================================================================

def lead(address):
    return parse_email(
        "From: Ann Petrakis <ann@example.com>\n"
        "Subject: New enquiry from your website\n\n"
        "Name: Ann Petrakis\n"
        "Phone: 216-555-0142\n"
        "Email: ann@example.com\n"
        f"Address: {address}\n"
        "Message: My kitchen faucet has been dripping for a week.\n")


near = handle(lead("1428 Detroit Ave, Lakewood, OH 44107"), JOE, now=at(8))
far = handle(lead("88 High St, Columbus, OH 43215"), JOE, now=at(8))

check_true("a nearby customer is offered times",
           len(near["windows"]) > 0,
           "Ann in Lakewood, 7 miles away. She should get appointment times")

check("a faraway customer is offered nothing",
      len(far["windows"]), 0,
      "Ann in Columbus, 163 miles away. Offering her a time would either "
      "waste Joe's whole day or leave her waiting")

check_true("she is told she is outside the area, politely",
           "outside the area we cover" in far["customer_email"],
           "The same Columbus lead. The email said:\n"
           + "\n".join(f"            {l}"
                       for l in far["customer_email"].splitlines()))

check_true("the customer is NOT told our guessed drive time",
           "245" not in far["customer_email"]
           and "minute drive" not in far["customer_email"],
           "The same email. Our estimate called Cleveland-to-Columbus a 4 "
           "hour drive when it is really about 2h15. Telling a customer that "
           "makes the plumber look like he doesn't know his own state")

check_true("but the plumber IS told how far it was",
           far.get("out_of_area") is not None,
           f"The same lead, from Joe's side. He gets the number "
           f"({far.get('out_of_area')} minutes) in case he fancies the job "
           f"anyway - it is his business, not the agent's")


# ===========================================================================

def run():
    print("=" * 70)
    print("  THE DIARY AND THE DRIVING")
    print("  Does the agent know where the customer is, and when the")
    print("  plumber is actually free?")
    print("=" * 70)
    print()
    passed = 0
    for label, ok, actual, expected, given in results:
        print(f"[{'pass' if ok else 'FAIL'}] {label}")
        print(f"       fed in  : {given}")
        print(f"       expected: {expected}")
        print(f"       got     : {actual}")
        print()
        passed += ok
    print("-" * 70)
    print(f"  {passed} passed, {len(results) - passed} failed, "
          f"{len(results)} total")
    print("-" * 70)
    return passed == len(results)


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
