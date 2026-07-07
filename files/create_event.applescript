-- create_event.applescript
--
-- Creates a single event in Apple Calendar for a Codeforces contest,
-- unless an event for that contest already exists (idempotent).
--
-- Arguments (all passed as strings from the calling script):
--   1  calendarName
--   2  contestId
--   3  eventTitle
--   4  startYear   5 startMonth   6 startDay   7 startHour   8 startMinute
--   9  endYear    10 endMonth    11 endDay    12 endHour    13 endMinute
--   14 alarmMinutesBefore   (minutes before start date to show a Calendar alert)
--
-- Prints one of: CREATED | SKIPPED_EXISTS  (used by the Python caller)

on run argv
    set calName to item 1 of argv
    set contestId to item 2 of argv
    set eventTitle to item 3 of argv

    set sYear to (item 4 of argv) as integer
    set sMonth to (item 5 of argv) as integer
    set sDay to (item 6 of argv) as integer
    set sHour to (item 7 of argv) as integer
    set sMin to (item 8 of argv) as integer

    set eYear to (item 9 of argv) as integer
    set eMonth to (item 10 of argv) as integer
    set eDay to (item 11 of argv) as integer
    set eHour to (item 12 of argv) as integer
    set eMin to (item 13 of argv) as integer

    set alarmMinutesBefore to (item 14 of argv) as integer

    set marker to "cf-contest-id:" & contestId

    tell application "Calendar"
        if not (exists calendar calName) then
            error "Calendar '" & calName & "' does not exist. Create it in Calendar.app first (or change CALENDAR_NAME)."
        end if

        tell calendar calName
            -- Idempotency check: has this contest already been added?
            set existing to (every event whose description contains marker)
            if (count of existing) > 0 then
                return "SKIPPED_EXISTS"
            end if

            -- Build start date. "day" is reset to 1 first to avoid
            -- overflow when the current day doesn't exist in the target month.
            set startDate to current date
            set day of startDate to 1
            set year of startDate to sYear
            set month of startDate to sMonth
            set day of startDate to sDay
            set hours of startDate to sHour
            set minutes of startDate to sMin
            set seconds of startDate to 0

            set endDate to current date
            set day of endDate to 1
            set year of endDate to eYear
            set month of endDate to eMonth
            set day of endDate to eDay
            set hours of endDate to eHour
            set minutes of endDate to eMin
            set seconds of endDate to 0

            set newEvent to make new event with properties {summary:eventTitle, start date:startDate, end date:endDate, description:marker}

            -- Alert X minutes before the contest starts. Trigger interval
            -- is in minutes relative to the start date; negative = before.
            tell newEvent
                make new display alarm at end of display alarms with properties {trigger interval:-alarmMinutesBefore}
            end tell

            return "CREATED"
        end tell
    end tell
end run