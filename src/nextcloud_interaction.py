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

# BASE_URL = "http://qkzk.ddns.net:81/remote.php/dav/"
# USERNAME = "qkzk"
APP_PASSWORD_PATH = "tokens/quentin/nextcloud"

NEXTCLOUD_COLORS = {
    "11": "CRIMSON",
    "4": "LIGHTCORAL",
    "6": "SANDYBROWN",
    "5": "GOLD",
    "10": "LIMEGREEN",
    "2": "AQUAMARINE",
    "7": "MEDIUMTURQUOISE",
    "9": "ROYALBLUE",
    "1": "SKYBLUE",
    "3": "PLUM",
    "8": "GAINSBORO",
}


def create_or_update_week_events_nextcloud() -> None:
    logger.warning(STARTING_APPLICATION_MSG)
    arguments = read_arguments()
    print(arguments)
    # exit()
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
    else:
        # TODO: day events
        print("TODO")


# def create_or_update_day_event(
#     calendar: caldav.Calendar,
#     event_details: Event,
# ):
#     timeMin = one_day_earlier(event_details.start["date"])
#     timeMax = event_details.end["date"] + "T00:00:00Z"
#     existing_events = list(
#         retrieve_day_events_matching_date(calendar, timeMin, timeMax)
#     )
#     if event_details in existing_events:
#         update_event(
#             new_event=event_details,
#             old_event=existing_events[existing_events.index(event_details)],
#         )
#     else:
#         create_event(calendar, event_details=event_details)


def create_or_update_timed_event(
    calendar: caldav.Calendar,
    event_details: Event,
) -> None:
    existing_event = find_timed_event_matching_time(event_details, calendar)
    if existing_event is None:
        create_event(
            calendar,
            event_details,
        )
    else:
        update_event(
            new_event=event_details,
            old_event=existing_event,
        )


def find_timed_event_matching_time(
    event: Event,
    calendar: caldav.Calendar,
) -> caldav.Event | None:
    if event.is_all_day:
        return None
    timeMin = event.start["dateTime"]
    timeMax = event.end["dateTime"]

    events_filtered = retrieve_events(timeMin, timeMax, calendar)

    if events_filtered:
        return events_filtered[0]


def caldav_event_vevent(event: caldav.Event):
    return event.icalendar_component


def retrieve_events(
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
        if time_min <= dtstart <= time_max:
            events.append(event)
    return events


def create_event(calendar: caldav.Calendar, event_details: Event) -> caldav.Event:
    tz = timezone("Europe/Paris")

    # Convert string timestamps to datetime
    dtstart = datetime.datetime.fromisoformat(
        event_details.start.get("dateTime", event_details.start.get("date"))
    ).astimezone(tz)
    dtend = datetime.datetime.fromisoformat(
        event_details.end.get("dateTime", event_details.end.get("date"))
    ).astimezone(tz)

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


def update_event(
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

    is_all_day = (
        isinstance(dtstart, datetime.datetime)
        and dtstart.time() == datetime.datetime.min.time()
    )
    tz = timezone("Europe/Paris")

    # Convert string timestamps to datetime
    newdtstart = datetime.datetime.fromisoformat(
        new_event.start.get("dateTime", new_event.start.get("date"))
    ).astimezone(tz)
    newdtend = datetime.datetime.fromisoformat(
        new_event.end.get("dateTime", new_event.end.get("date"))
    ).astimezone(tz)
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
