#!/usr/bin/env python3
"""
cf_calendar_sync.py

Fetches upcoming Codeforces contests from the official Codeforces API
and blocks the corresponding time slot in Apple Calendar (macOS) as an
event, so the user's calendar automatically reflects contest times.

Designed to run unattended (e.g. via launchd). Safe to run repeatedly:
each contest is only added once (idempotent, tracked via a hidden
marker in the event's notes field).

Requirements: macOS, Python 3.8+, Calendar.app.
"""

import json
import logging
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration (edit these two values to taste)
# --------------------------------------------------------------------------
CALENDAR_NAME = "Codeforces"     # Must exist in Calendar.app
LOOKAHEAD_DAYS = 30              # Ignore contests further out than this
ALARM_MINUTES_BEFORE = 30        # Calendar alert this many minutes before start
# --------------------------------------------------------------------------

CODEFORCES_API_URL = "https://codeforces.com/api/contest.list?gym=false"
SCRIPT_DIR = Path(__file__).resolve().parent
APPLESCRIPT_PATH = SCRIPT_DIR / "create_event.applescript"

LOG_DIR = Path.home() / "Library" / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "cf_calendar_sync.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def fetch_upcoming_contests(retries: int = 3, backoff_seconds: int = 5):
    """Return upcoming (not-yet-started) Codeforces contests within the
    configured lookahead window, sorted by start time. Retries on
    transient network errors."""
    req = urllib.request.Request(
        CODEFORCES_API_URL, headers={"User-Agent": "cf-calendar-sync/1.0"}
    )

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                payload = json.load(resp)
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            log.warning("Fetch attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff_seconds)
    else:
        raise RuntimeError(f"Could not reach Codeforces API after {retries} attempts: {last_error}")

    if payload.get("status") != "OK":
        raise RuntimeError(f"Codeforces API returned an error: {payload.get('comment')}")

    now = datetime.now().timestamp()
    horizon = now + LOOKAHEAD_DAYS * 86400

    upcoming = [
        c
        for c in payload["result"]
        if c.get("phase") == "BEFORE" and now <= c.get("startTimeSeconds", 0) <= horizon
    ]
    upcoming.sort(key=lambda c: c["startTimeSeconds"])
    return upcoming


def add_event(contest: dict) -> None:
    """Call the AppleScript helper to add (or skip, if already present)
    one calendar event for a single contest."""
    start = datetime.fromtimestamp(contest["startTimeSeconds"])
    end = start + timedelta(seconds=contest["durationSeconds"])
    title = f"Codeforces: {contest['name']}"

    args = [
        "osascript",
        str(APPLESCRIPT_PATH),
        CALENDAR_NAME,
        str(contest["id"]),
        title,
        str(start.year), str(start.month), str(start.day),
        str(start.hour), str(start.minute),
        str(end.year), str(end.month), str(end.day),
        str(end.hour), str(end.minute),
        str(ALARM_MINUTES_BEFORE),
    ]

    result = subprocess.run(args, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"AppleScript failed for '{title}': {result.stderr.strip()}")

    status = result.stdout.strip()
    if status == "CREATED":
        log.info("Added event: %s  (%s -> %s)", title, start, end)
    elif status == "SKIPPED_EXISTS":
        log.info("Already on calendar, skipped: %s", title)
    else:
        log.warning("Unexpected response for '%s': %s", title, status)


def main() -> None:
    log.info("=== Codeforces -> Apple Calendar sync starting ===")

    if not APPLESCRIPT_PATH.exists():
        log.error("Missing helper file: %s", APPLESCRIPT_PATH)
        sys.exit(1)

    try:
        contests = fetch_upcoming_contests()
    except RuntimeError as exc:
        log.error(str(exc))
        sys.exit(1)

    if not contests:
        log.info("No upcoming contests within the next %d days.", LOOKAHEAD_DAYS)
        return

    error_count = 0
    for contest in contests:
        try:
            add_event(contest)
        except RuntimeError as exc:
            error_count += 1
            log.error(str(exc))

    log.info(
        "Sync finished. %d contest(s) checked, %d error(s).",
        len(contests), error_count,
    )
    if error_count:
        sys.exit(1)


if __name__ == "__main__":
    main()