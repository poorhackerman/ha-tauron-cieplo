"""Strict response parsing, independent of Home Assistant."""

import re
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")
STAMP = r"(\d{1,2}\.\d{1,2}\.\d{4})\s*(?:r\.?\s*)?(?:godz\.?\s*)?(\d{1,2}[:.]\d{2})"
PERIOD = re.compile(r"\bod\s+" + STAMP + r"\s*do\s+" + STAMP, re.IGNORECASE)


class InvalidResponse(ValueError):
    """An upstream response cannot be safely interpreted."""


def clean(value):
    """Remove markup before storing upstream text in entity attributes."""
    return " ".join(unescape(re.sub(r"<[^>]*>", " ", str(value or ""))).split())


def parse_period(text):
    """Extract a full explicit date pair; never invent missing dates."""
    match = PERIOD.search(text)
    if not match:
        return None, None
    try:
        start = datetime.strptime(
            f"{match[1]} {match[2].replace('.', ':')}", "%d.%m.%Y %H:%M"
        ).replace(tzinfo=WARSAW)
        end = datetime.strptime(
            f"{match[3]} {match[4].replace('.', ':')}", "%d.%m.%Y %H:%M"
        ).replace(tzinfo=WARSAW)
    except ValueError:
        return None, None
    return (start, end) if end >= start else (None, None)


def parse_outages(payload):
    """Do not turn a broken response into 'no outage'."""
    if not isinstance(payload, dict) or not isinstance(payload.get("Outages"), dict):
        raise InvalidResponse("Missing Outages object")
    block = payload["Outages"]
    present = block.get("Present")
    if not isinstance(present, bool):
        raise InvalidResponse("Missing boolean Present")
    if not present:
        return {"present": False, "outages": []}
    info = block.get("outageInfo")
    rows = info.get("info") if isinstance(info, dict) else None
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or not rows:
        raise InvalidResponse("Present without outage information")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not any(
            row.get(k) for k in ("reply", "details")
        ):
            raise InvalidResponse("Invalid outage row")
        reply, details = clean(row.get("reply")), clean(row.get("details"))
        start, end = parse_period(f"{reply} {details}")
        result.append(
            {
                "address": clean(row.get("address")),
                "reply": reply,
                "details": details,
                "start": start,
                "end": end,
            }
        )
    return {"present": True, "outages": result}


def select_outage(outages, now):
    """Prefer ongoing/unknown, then earliest future, then latest expired notice."""
    ongoing = [
        o
        for o in outages
        if o["start"] is None or o["start"] <= now and o["end"] >= now
    ]
    if ongoing:
        return ongoing[0]
    future = [o for o in outages if o["start"] > now]
    if future:
        return min(future, key=lambda o: o["start"])
    return max(outages, key=lambda o: o["end"]) if outages else None
