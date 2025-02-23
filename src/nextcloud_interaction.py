import datetime

from os.path import exists
from pprint import pprint
from pytz import timezone

import caldav

from src.google_interaction import one_day_earlier

from .arguments_parser import read_arguments
from .calendar_python import CONFIRMATION_MSG, EXPLORING_MSG, STARTING_APPLICATION_MSG
from .colors import color_text
from .config import Agenda, agendas
from .explore_md_file import parse_events
from .logger import logger
from .model import Event
from .states import CalpyStates
from .user_interaction import WRONG_PATH_MSG, update_state_from_inputs

APP_PASSWORD_PATH = "tokens/quentin/nextcloud"

NEXTCLOUD_COLORS = {
    "11": "crimson",
    "4": "lightcoral",
    "6": "sandybrown",
    "5": "gold",
    "10": "limegreen",
    "2": "aquamarine",
    "7": "mediumturquoise",
    "9": "royalblue",
    "1": "skyblue",
    "3": "plum",
    "8": "gainsboro",
}


def create_or_update_week_events_nextcloud() -> None:
    logger.warning(STARTING_APPLICATION_MSG)
    arguments = read_arguments()
    print(arguments)
    calpy_states = CalpyStates.from_arguments_and_config(arguments, agendas)
    update_state_from_inputs(calpy_states)
    calendar = connect_nextcloud()
    if calendar is None:
        print("Couldn't find calendar")
        return
    sync_events(calpy_states.agenda, calendar, calpy_states.path_list)


def sync_events(
    agenda: Agenda, calendar: caldav.Calendar, path_list: list[str]
) -> None:
    for path in path_list:
        if not exists(path):
            logger.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        sync_event_from_md(agenda, calendar, path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


def read_setup() -> list[str]:
    with open(APP_PASSWORD_PATH) as f:
        return [line.strip() for line in f.readlines()[:3]]


def create_nextcloud_client(
    url: str, username: str, app_password: str
) -> caldav.DAVClient:
    return caldav.DAVClient(url=url, username=username, password=app_password)


def get_calendars(client: caldav.DAVClient) -> list[caldav.Calendar]:
    principal = client.principal()
    calendars = principal.calendars()
    return calendars


def find_calendar(
    calendars: list[caldav.Calendar], name: str
) -> caldav.Calendar | None:
    for calendar in calendars:
        if calendar.name == name:
            return calendar


def connect_nextcloud() -> caldav.Calendar | None:
    url, username, app_password = read_setup()
    print(url, username, app_password)
    client = create_nextcloud_client(
        url=url, username=username, app_password=app_password
    )
    calendars = get_calendars(client)
    return find_calendar(calendars, "python_calendar")


def sync_event_from_md(
    agenda: Agenda,
    calendar: caldav.Calendar,
    path: str,
) -> None:
    event_list = parse_events(agenda, path)
    pprint(event_list)
    for event_details in event_list:
        update_or_create_event(calendar, event_details)


def update_or_create_event(
    calendar: caldav.Calendar,
    event_details: Event,
) -> None:
    if not event_details.is_all_day:
        create_or_update_timed_event(calendar, event_details)
        pass
    else:
        create_or_update_day_event(calendar, event_details)


def create_or_update_day_event(
    calendar: caldav.Calendar,
    event_details: Event,
):
    existing_event = find_day_event_matching_date(event_details, calendar)
    if existing_event is None:
        create_day_event(calendar, event_details=event_details)
    else:
        update_timed_event(new_event=event_details, old_event=existing_event)


def create_or_update_timed_event(
    calendar: caldav.Calendar,
    event_details: Event,
) -> None:
    existing_event = find_timed_event_matching_time(event_details, calendar)
    if existing_event is None:
        create_timed_event(
            calendar,
            event_details,
        )
    else:
        update_timed_event(
            new_event=event_details,
            old_event=existing_event,
        )


def find_day_event_matching_date(
    event: Event,
    calendar: caldav.Calendar,
) -> caldav.Event | None:
    if not event.is_all_day:
        return None
    timeMin = event.start["date"]
    timeMax = event.end["date"]

    events_filtered = retrieve_day_events(timeMin, timeMax, calendar)

    if events_filtered:
        return events_filtered[0]


def find_timed_event_matching_time(
    event: Event,
    calendar: caldav.Calendar,
) -> caldav.Event | None:
    if event.is_all_day:
        return None
    timeMin = event.start["dateTime"]
    timeMax = event.end["dateTime"]

    events_filtered = retrieve_timed_events(timeMin, timeMax, calendar)

    if events_filtered:
        return events_filtered[0]


def caldav_event_vevent(event: caldav.Event):
    return event.icalendar_component


def retrieve_day_events(
    timeMin: str,
    timeMax: str,
    calendar: caldav.Calendar,
) -> list[caldav.Event]:

    tz = timezone("Europe/Paris")
    time_min = datetime.datetime.fromisoformat(timeMin).astimezone(tz)
    time_max = datetime.datetime.fromisoformat(timeMax).astimezone(tz)

    events = []
    for event in calendar.events():
        vevent = caldav_event_vevent(event)
        if not vevent:
            continue
        dtstart: datetime.datetime = vevent.get("DTSTART").dt
        dtstart = datetime.datetime.combine(
            dtstart, datetime.datetime.min.time()
        ).astimezone(tz)
        dtend: datetime.datetime = vevent.get("DTEND").dt
        dtend = datetime.datetime.combine(
            dtend, datetime.datetime.min.time()
        ).astimezone(tz)
        delta = dtend - dtstart
        if delta >= datetime.timedelta(hours=24) and time_min <= dtstart <= time_max:
            events.append(event)
    return events


def retrieve_timed_events(
    timeMin: str,
    timeMax: str,
    calendar: caldav.Calendar,
) -> list[caldav.Event]:
    time_min = datetime.datetime.fromisoformat(timeMin)
    time_max = datetime.datetime.fromisoformat(timeMax)

    events = []
    for event in calendar.events():
        vevent = caldav_event_vevent(event)
        if not vevent:
            continue
        dtstart: datetime.datetime = vevent.get("DTSTART").dt
        # dtstart for day event is a date not a datetime
        if type(time_min) != type(dtstart):
            continue
        if time_min <= dtstart <= time_max:
            events.append(event)
    return events


def create_day_event(calendar: caldav.Calendar, event_details: Event) -> caldav.Event:

    # Convert string timestamps to date
    dtstart = datetime.date.fromisoformat(event_details.start["date"])
    dtend = datetime.date.fromisoformat(event_details.end["date"])

    cal_event = calendar.add_event(
        dtstart=dtstart,
        dtend=dtend,
        summary=event_details.summary,
        description=event_details.description,
        location=event_details.location,
        color=NEXTCLOUD_COLORS[event_details.colorId],
    )

    creation_event_msg = f"Event created: {dtstart} {event_details.summary}"
    print(color_text(creation_event_msg, "YELLOW"))
    logger.warning(creation_event_msg)
    return cal_event


def create_timed_event(calendar: caldav.Calendar, event_details: Event) -> caldav.Event:
    tz = timezone("Europe/Paris")

    # Convert string timestamps to datetime
    dtstart = datetime.datetime.fromisoformat(
        event_details.start["dateTime"]
    ).astimezone(tz)
    dtend = datetime.datetime.fromisoformat(event_details.end["dateTime"]).astimezone(
        tz
    )

    cal_event = calendar.add_event(
        dtstart=dtstart,
        dtend=dtend,
        summary=event_details.summary,
        description=event_details.description,
        location=event_details.location,
        color=NEXTCLOUD_COLORS[event_details.colorId],
    )

    print(cal_event.icalendar_instance)
    creation_event_msg = f"Event created: {dtstart} {event_details.summary}"
    print(color_text(creation_event_msg, "YELLOW"))
    logger.warning(creation_event_msg)
    return cal_event


def update_timed_event(
    new_event: Event,
    old_event: caldav.Event,
) -> None:
    vevent = caldav_event_vevent(old_event)
    if not vevent:
        return

    summary = vevent.get("SUMMARY", "%").to_ical().decode()
    description = vevent.get("DESCRIPTION", "")
    description = description.to_ical().decode() if description else description
    location = vevent.get("LOCATION", "")
    location = location.to_ical().decode() if location else location

    dtstart = vevent.get("DTSTART").dt
    dtend = vevent.get("DTEND").dt

    tz = timezone("Europe/Paris")

    # Convert string timestamps to datetime
    if new_event.is_all_day:
        newdtstart = datetime.date.fromisoformat(new_event.start["date"])
        newdtend = datetime.date.fromisoformat(new_event.end["date"])
    else:
        # fmt: off
        newdtstart = datetime.datetime.fromisoformat(new_event.start["dateTime"]).astimezone(tz)
        newdtend = datetime.datetime.fromisoformat(new_event.end["dateTime"]).astimezone(tz)
        # fmt: on

    if (
        dtstart == newdtstart
        and dtend == newdtend
        and description == new_event.description
        and summary == new_event.summary
        and location == new_event.location
    ):
        unchanged_event_msg = f"Event didn't change: {dtstart} {summary}"
        print(color_text(unchanged_event_msg, "PURPLE"))
        logger.warning(unchanged_event_msg)
    else:
        old_event.icalendar_component["dtstart"].dt = newdtstart
        old_event.icalendar_component["dtend"].dt = newdtend
        old_event.icalendar_component["summary"] = new_event.summary
        old_event.icalendar_component["description"] = new_event.description
        old_event.icalendar_component["location"] = new_event.location
        old_event.save(no_overwrite=False)
        unchanged_event_msg = f"Event updated: {newdtstart} {summary}"
        print(color_text(unchanged_event_msg, "CYAN"))
        logger.warning(unchanged_event_msg)
