from datetime import datetime
import re

import caldav
import icalendar

from model import Event

BASE_URL = "http://qkzk.ddns.net:81/remote.php/dav/"
USERNAME = "qkzk"
APP_PASSWORD_PATH = "/home/quentin/gclem/dev/python/boulot_utils/calpy_branches/tokens/quentin/nextcloud"


def read_app_password():
    with open(APP_PASSWORD_PATH) as f:
        return f.read().strip()


def create_nextcloud_client(app_password) -> caldav.DAVClient:
    return caldav.DAVClient(url=BASE_URL, username=USERNAME, password=app_password)


def get_calendars(client: caldav.DAVClient) -> list[caldav.Calendar]:
    principal = client.principal()
    calendars = principal.calendars()
    return calendars


def display_event(calendar: caldav.Calendar) -> None:
    events = calendar.events()
    for event in events:
        ic = event.icalendar_instance
        # print(event)
        # print(ic)
        ica = ic.to_ical().decode("utf-8")

        print(ica)
        vevent = event.icalendar_instance.subcomponents[0]
        vevent["SUMMARY"] = "tata"
        event.save(no_overwrite=False)
        # calendar.save_event(ica)
        # calendar.add_event(ic)
        # calendar.add_event(ic)

        # internal = caldav_event_to_internal(event)
        # print(event.data)
        # print(internal)
        # back_to_caldav = internal_event_to_caldav(internal, calendar)
        #
        # print(back_to_caldav.data)


def caldav_event_to_internal(event: caldav.Event) -> Event:
    """Convert a CalDAV Event to an internal Event object."""
    ical_event = event.icalendar_instance

    vevent = next(
        (
            component
            for component in ical_event.subcomponents
            if component.name == "VEVENT"
        ),
        None,
    )

    if not vevent:
        raise ValueError("Invalid iCalendar data: No VEVENT found")

    event_id = vevent.get("UID", "").to_ical().decode()
    summary = vevent.get("SUMMARY", "%").to_ical().decode()
    description = vevent.get("DESCRIPTION", "")
    description = description.to_ical().decode() if description else description
    location = vevent.get("LOCATION", "")
    location = location.to_ical().decode() if location else location

    dtstart = vevent.get("DTSTART").dt
    dtend = vevent.get("DTEND").dt

    is_all_day = isinstance(dtstart, datetime) and dtstart.time() == datetime.min.time()

    return Event(
        id=event_id,
        start=(
            {"dateTime": dtstart.isoformat()}
            if not is_all_day
            else {"date": dtstart.date().isoformat()}
        ),
        end=(
            {"dateTime": dtend.isoformat()}
            if not is_all_day
            else {"date": dtend.date().isoformat()}
        ),
        location=location,
        summary=summary,
        description=description,
        colorId="1",  # No direct equivalent in CalDAV, defaulting to "1"
        htmlLink="",  # Not available in CalDAV
        is_all_day=is_all_day,
    )


from datetime import datetime, timedelta
from pytz import timezone
from icalendar import (
    Event as ICalEvent,
    Calendar,
    Timezone,
    TimezoneStandard,
    TimezoneDaylight,
    vRecur,
    vText,
    vUTCOffset,
)


def internal_event_to_caldav(event: Event, calendar: caldav.Calendar) -> caldav.Event:
    """Convert an internal Event object to a CalDAV Event and add it to the calendar."""

    tz = timezone("Europe/Paris")

    # Convert string timestamps to datetime
    dtstart_obj = datetime.fromisoformat(
        event.start.get("dateTime", event.start.get("date"))
    ).astimezone(tz)
    dtend_obj = datetime.fromisoformat(
        event.end.get("dateTime", event.end.get("date"))
    ).astimezone(tz)

    # Create iCalendar object
    ical_event = Calendar()
    ical_event.add("prodid", "-//Nextcloud//NONSGML v1.0//EN")
    ical_event.add("version", "2.0")

    # Create VEVENT
    event_component = ICalEvent()
    event_component.add("uid", event.id)
    event_component.add("summary", event.summary or "%")
    event_component.add("description", event.description or "super")
    event_component.add("location", event.location or "")
    event_component.add("dtstamp", datetime.now().astimezone(tz))

    # Ensure `DTSTART` and `DTEND` have `TZID`
    event_component.add("dtstart", dtstart_obj, parameters={"TZID": "Europe/Paris"})
    event_component.add("dtend", dtend_obj, parameters={"TZID": "Europe/Paris"})

    ical_event.add_component(event_component)

    # Define VTIMEZONE Component
    vtimezone = Timezone()
    vtimezone.add("TZID", "Europe/Paris")

    standard = TimezoneStandard()
    standard.add("DTSTART", datetime(1970, 1, 1, 0, 0, 0))
    tt = caldav.timedelta(hours=1)
    tt2 = caldav.timedelta(hours=2)
    standard.add("TZOFFSETFROM", tt)
    standard.add("TZOFFSETTO", tt)
    standard.add("TZNAME", "CET")

    daylight = TimezoneDaylight()
    # daylight.add("DTSTART", datetime(1970, 3, 29, 2, 0, 0))
    #
    # daylight.add("RRULE", "FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3")
    # daylight.add("RRULE", vRecur({"FREQ": "YEARLY", "BYDAY": "-1SU", "BYMONTH": 3}))
    # daylight["RRULE"] = vRecur({"FREQ": "YEARLY", "BYDAY": "-1SU", "BYMONTH": 3})

    daylight.add("DTSTART", datetime(1970, 3, 29, 2, 0, 0))
    daylight.add("RRULE", vRecur({"FREQ": "YEARLY", "BYDAY": "-1SU", "BYMONTH": 3}))
    daylight.add("TZOFFSETFROM", vUTCOffset(timedelta(hours=1)))
    daylight.add("TZOFFSETTO", vUTCOffset(timedelta(hours=2)))
    daylight.add("TZNAME", "CEST")

    vtimezone.add_component(standard)
    vtimezone.add_component(daylight)

    ical_event.add_component(vtimezone)

    decoded = ical_event.to_ical().decode("utf-8")
    print(decoded)

    return calendar.add_event(ical_event.to_ical().decode("utf-8"))


def example() -> None:
    app_password = read_app_password()
    print(app_password)
    client = create_nextcloud_client(app_password)
    calendars = get_calendars(client)
    for calendar in calendars:
        print(f"calendar {calendar.name}")
        display_event(calendar)


if __name__ == "__main__":
    example()
