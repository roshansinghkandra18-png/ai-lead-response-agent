"""
distance.py  --  how far apart two places are, and how long the drive takes.

Two jobs to do:

  1. TRAVEL TIME between jobs, so the agent never promises a customer a slot
     the plumber physically cannot reach. First job of the day is measured
     from his home; every job after that from the previous customer's address.

  2. THE SERVICE AREA, so the agent turns away work that is too far to be
     worth the drive - instead of booking it and letting him find out when he
     opens his spreadsheet. Always measured from his BASE, never from wherever
     he happens to be standing: a customer must not be accepted on Monday and
     rejected on Friday for the same address.

HOW IT KNOWS
    A file of every US zip code and where it sits on the map. Downloaded once,
    read from disk, no internet needed, nothing charged per lookup, and nothing
    that can be down when a customer is waiting.

WHAT IT IS NOT
    This is straight-line distance with an adjustment for real roads. It does
    not know about traffic, roadworks, rivers or rain. Google Maps does, and
    slots in behind `minutes_between` later without anything else changing -
    see calendar-decisions.md.
"""

import csv
import os
import re
from math import radians, sin, cos, asin, sqrt


ZIP_FILE = "zipcodes.csv"

# A US zip is five digits. The "+4" part after a dash is a delivery route and
# tells us nothing useful about position, so it is ignored.
ZIP_PATTERN = re.compile(r"\b(\d{5})(?:-\d{4})?\b")

_places = None          # zip -> (latitude, longitude), loaded once and kept


def load(path=ZIP_FILE):
    """Read the zip code file into memory. Done once, then reused."""
    global _places
    if _places is not None:
        return _places
    if not os.path.exists(path):
        _places = {}
        return _places

    found = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = (row.get("ZIP") or "").strip()
            try:
                found[code] = (float(row["LAT"]), float(row["LNG"]))
            except (TypeError, ValueError, KeyError):
                continue        # a blank or broken line - skip it, don't crash
    _places = found
    return _places


def zip_from(text):
    """
    Pull the zip code out of whatever the customer wrote.

    Handles "1428 Detroit Ave, Lakewood, OH 44107" and "44107-1234" alike.
    Returns None when there is no zip in there at all, which is a normal thing
    to happen - people leave it off.
    """
    if not text:
        return None
    # Last match wins: a US address ends with the zip, and a house number at
    # the start can also be five digits ("44120 State Route 7").
    matches = ZIP_PATTERN.findall(str(text))
    known = load()
    for code in reversed(matches):
        if code in known:
            return code
    return matches[-1] if matches else None


def miles_between(zip_a, zip_b, road_factor=1.3):
    """
    Road miles between the middle of two zip codes.

    The straight-line distance is multiplied by `road_factor`, because roads
    bend, rivers need bridges and nobody drives through buildings. 1.3 is the
    usual rule of thumb for US towns.

    Returns None when either zip is unknown - the caller then falls back to the
    plumber's default travel time rather than guessing.
    """
    known = load()
    if zip_a not in known or zip_b not in known:
        return None
    if zip_a == zip_b:
        return 0.0

    lat1, lon1 = known[zip_a]
    lat2, lon2 = known[zip_b]

    # Haversine: distance across the surface of a sphere.
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = (sin((lat2 - lat1) / 2) ** 2
         + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2)
    straight = 2 * asin(sqrt(a)) * 3958.8      # earth's radius in miles
    return straight * road_factor


def _setting(cfg, key, fallback):
    """
    One travel setting, or a sensible standard if the client's file predates
    this section. An older settings file must never crash the agent - it just
    means that client has not been asked these questions yet.
    """
    if not cfg.has_section("travel"):
        return fallback
    value = cfg.get("travel", key, fallback="").strip()
    return value or fallback


def minutes_between(zip_a, zip_b, cfg):
    """
    How long the drive takes, in minutes, rounded up to the next 5.

    Rounded because "23.4 minutes" is false precision - nobody drives to a
    schedule that exact, and the plumber reading his diary would rightly
    distrust it.

    Falls back to his default travel time when either zip is unknown. That is
    the honest answer: better a sensible standard gap than a made-up number.

    THIS is the single place Google Maps will slot into later. Everything else
    calls this and does not care how the answer was reached.
    """
    default = int(_setting(cfg, "default_minutes", 30))
    miles = miles_between(zip_a, zip_b, float(_setting(cfg, "road_factor", 1.3)))
    if miles is None:
        return default

    speed = float(_setting(cfg, "average_speed_mph", 40))
    minutes = (miles / speed) * 60
    return max(5, int(-(-minutes // 5) * 5))


def too_far(customer_zip, cfg):
    """
    Is this customer outside the area the plumber is willing to cover?

    Measured from his BASE, always. Returns (True, minutes) when it is too far,
    (False, minutes) when it is fine.

    When the customer's zip is unknown we say NO rather than turning them away.
    Refusing a real customer because a file is missing a row is a far worse
    mistake than driving a bit further than usual.
    """
    base = _setting(cfg, "base_zip", "")
    limit = _setting(cfg, "max_travel_minutes", "")
    # No base or no limit set means this client was never asked how far he
    # travels. Turn nobody away on a question we never put to him.
    if not base or not limit or not customer_zip:
        return False, None

    miles = miles_between(customer_zip, base,
                          float(_setting(cfg, "road_factor", 1.3)))
    if miles is None:
        return False, None

    limit = int(limit)

    minutes = minutes_between(customer_zip, base, cfg)
    return minutes > limit, minutes
