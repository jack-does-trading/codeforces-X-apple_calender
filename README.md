# Codeforces 💻 → Apple Calendar Sync 📅

## Why this exists

I kept doing the same dumb thing every week: forget a Codeforces round was
happening, schedule a call right through it, then rage-decline the call at
minute two of the contest. My calendar had no idea rounds existed. Codeforces
had no idea my calendar existed. Nobody was talking to anybody.

So this exists to make my calendar and Codeforces talk to each other, without
me in the loop. It asks Codeforces "what's coming up," then tells Calendar.app
"block this, I'm busy, don't @ me" — and it gives me a 30-minute heads-up so
I can actually be at my desk when the round starts, not still in the shower.

That's it. That's the whole app. No dashboard, no login, no "premium tier."
It does one thing and then gets out of your way, which is honestly more than
I can say for most of the apps on my phone.

## What it actually does

1. Asks the official Codeforces API which contests haven't started yet.
2. For each one coming up in the next 30 days, drops an event on a Calendar
   named **"Codeforces"**, sized exactly to the contest's start/end time.
3. Pings you with a Calendar alert **30 minutes before** it starts.
4. Runs again and again (hourly, daily, whenever) without ever double-booking
   the same contest twice — it remembers what it already added.

## Requirements
- macOS with Calendar.app
- Python 3.8+ (already on your Mac, you don't need to install anything extra)

## Setup (one-time)

1. **Copy this folder** somewhere it'll stay put, e.g.:
   ```bash
   mkdir -p ~/cf_calendar_sync
   cp cf_calendar_sync.py create_event.applescript ~/cf_calendar_sync/
   ```

2. **Create the target calendar**: Open Calendar.app → File → New Calendar →
   name it `Codeforces` (or point `CALENDAR_NAME` in `cf_calendar_sync.py`
   at a calendar you already have — your call).

3. **Run it once by hand** so macOS can ask your permission:
   ```bash
   cd ~/cf_calendar_sync
   python3 cf_calendar_sync.py
   ```
   macOS will pop up a dialog asking if Terminal can control Calendar.
   Say yes — that's the whole app talking to Calendar.app, not some rogue
   process. (Said no by accident? Fix it under
   *System Settings → Privacy & Security → Automation*.)

4. Peek at Calendar.app. You should see something like
   "Codeforces: Round 1234", fully blocked out, alarm attached.

## Make it automatic (the whole point)

Manually running a script defeats the purpose of automating your life.
Use `launchd` so this just... happens, forever, in the background:

1. Open `com.user.cfcalendarsync.plist` and swap
   `/Users/YOUR_USERNAME/cf_calendar_sync/cf_calendar_sync.py` for the real
   path to your copy of the script.

2. Install and start it:
   ```bash
   cp com.user.cfcalendarsync.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.user.cfcalendarsync.plist
   ```
   Runs immediately, then every 6 hours, for as long as you're logged in.
   You will never think about this again. That's the goal.

3. Want it gone?
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.cfcalendarsync.plist
   ```

## Logs
(For when it inevitably doesn't work and you want to know why.)
- App log: `~/Library/Logs/cf_calendar_sync.log`
- launchd's own stdout/stderr (only useful for scheduler-level weirdness):
  `/tmp/cf_calendar_sync.out.log`, `/tmp/cf_calendar_sync.err.log`

## Configuration
All three knobs live at the top of `cf_calendar_sync.py`:
- `CALENDAR_NAME` — which macOS calendar gets the events (default `"Codeforces"`)
- `LOOKAHEAD_DAYS` — how far ahead to look for contests (default `30`)
- `ALARM_MINUTES_BEFORE` — how early to get nagged (default `30`)

## Files
| File | Purpose |
|---|---|
| `cf_calendar_sync.py` | The brain: fetches contests, calls the AppleScript helper, logs what happened |
| `create_event.applescript` | The hands: talks to Calendar.app, skips duplicates, creates the event + alarm |
| `com.user.cfcalendarsync.plist` | The alarm clock: tells launchd to run this on a schedule so you don't have to |
