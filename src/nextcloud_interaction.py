import datetime
from os.path import exists

import caldav
from pytz import timezone

from .arguments_parser import read_arguments
from .calendar_python import CONFIRMATION_MSG_NEXTCLOUD, EXPLORING_MSG
from .colors import color_text
from .config import Agenda, agendas
from .explore_md_file import parse_events
from .logger import logger
from .model import Event as CalpyEvent
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
    """
    Reads command-line arguments, retrieves calendar data, and synchronizes events for the upcoming week.
    """
    arguments = read_arguments()
    if arguments.no_nextcloud:
        print("disabled nextcloud syncing")
        return

    calpy_states = CalpyStates.from_arguments_and_config(arguments, agendas)
    if not isinstance(calpy_states.agenda, Agenda):
        print("Agenda should be set")
        return
    update_state_from_inputs(calpy_states)
    calendar = connect_nextcloud()
    if calendar is None:
        print("Couldn't fetch calendar from Nextcloud")
        return
    sync_events(calpy_states.agenda, calendar, calpy_states.path_list)


def sync_events(
    agenda: Agenda, calendar: caldav.Calendar, path_list: list[str]
) -> None:
    """
    Synchronizes events from Markdown files to the Nextcloud calendar.

    @param agenda: (Agenda) holds configured agenda information
    @param calendar: (caldav.Calendar) the Nextcloud calendar instance
    @param path_list: (list[str]) list of paths to event Markdown files
    """
    for path in path_list:
        if not exists(path):
            logger.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        sync_event_from_md(agenda, calendar, path)
        print(color_text(CONFIRMATION_MSG_NEXTCLOUD, "DARKCYAN"))


def read_nextcloud_setup() -> list[str]:
    """
    Reads the Nextcloud credentials and calendar setup from the configuration file.

    @returns: (list[str]) a list containing Nextcloud URL, username, app password, and calendar name.
    """
    with open(APP_PASSWORD_PATH) as f:
        return [line.strip() for line in f.readlines()[:4]]


def create_nextcloud_client(
    url: str, username: str, app_password: str
) -> caldav.DAVClient:
    """
    Creates and returns a CalDAV client for Nextcloud.

    @param url: (str) the Nextcloud CalDAV URL
    @param username: (str) the Nextcloud username
    @param app_password: (str) the app-specific password for authentication
    @returns: (caldav.DAVClient) a configured CalDAV client instance
    """
    return caldav.DAVClient(url=url, username=username, password=app_password)


def get_calendars(client: caldav.DAVClient) -> list[caldav.Calendar]:
    """
    Retrieves the list of available calendars from the Nextcloud account.

    @param client: (caldav.DAVClient) the Nextcloud CalDAV client
    @returns: (list[caldav.Calendar]) list of available calendars
    """
    principal = client.principal()
    calendars = principal.calendars()
    return calendars


def find_calendar(
    calendars: list[caldav.Calendar], name: str
) -> caldav.Calendar | None:
    """
    Finds a calendar by its name in the list of retrieved calendars.

    @param calendars: (list[caldav.Calendar]) list of available calendars
    @param name: (str) the name of the desired calendar
    @returns: (caldav.Calendar | None) the matching calendar or None if not found
    """
    for calendar in calendars:
        if calendar.name == name:
            return calendar


def connect_nextcloud() -> caldav.Calendar | None:
    """
    Establishes a connection to the Nextcloud CalDAV server and retrieves the specified calendar.

    @returns: (caldav.Calendar | None) the connected calendar instance or None if connection fails
    """
    url, username, app_password, calendar_name = read_nextcloud_setup()
    client = create_nextcloud_client(
        url=url, username=username, app_password=app_password
    )
    calendars = get_calendars(client)
    return find_calendar(calendars, calendar_name)


def sync_event_from_md(
    agenda: Agenda,
    calendar: caldav.Calendar,
    path: str,
) -> None:
    """
    Create or update events from md file

    @param agenda: (Agenda)
    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @param path: (str) path to the md file
    @returns: (None)
    @SE: insert or update events for a given week
    """
    md_event_list = parse_events(agenda, path)
    nextcloud_events = calendar.events()
    for event_details in md_event_list:
        update_or_create_event(event_details, nextcloud_events, calendar)


def update_or_create_event(
    event_details: CalpyEvent,
    nextcloud_events: list[caldav.Event],
    calendar: caldav.Calendar,
) -> None:
    """
    Sync a single event read from a .md file.
    seek if the event already exists,
    if there's already an event, it's updated.
    Else, a new one is created

    @param event_details: (Event) the description of an event
    @param nextcloud_events: (list[caldav.Event]) the existing events retrieved from the server
    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @returns: (None)
    """
    if not event_details.is_all_day:
        create_or_update_timed_event(event_details, nextcloud_events, calendar)
    else:
        create_or_update_day_event(event_details, nextcloud_events, calendar)


def create_or_update_day_event(
    event_details: CalpyEvent,
    nextcloud_events: list[caldav.Event],
    calendar: caldav.Calendar,
) -> None:
    """
    Sync a single DAY event read from a .md file.
    seek if the event already exists,
    if there's already an event, it's updated.
    Else, a new one is created

    @param event_details: (Event) the description of an event
    @param nextcloud_events: (list[caldav.Event]) the existing events retrieved from the server
    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @returns: (None)
    """
    existing_event = find_day_event_matching_date(event_details, nextcloud_events)
    if existing_event is None:
        create_day_event(calendar, event_details=event_details)
    else:
        update_event(new_event=event_details, old_event=existing_event)


def create_or_update_timed_event(
    event_details: CalpyEvent,
    nextcloud_events: list[caldav.Event],
    calendar: caldav.Calendar,
) -> None:
    """
    Sync a single TIMED event read from a .md file.
    seek if the event already exists,
    if there's already an event, it's updated.
    Else, a new one is created

    @param event_details: (Event) the description of an event
    @param nextcloud_events: (list[caldav.Event]) the existing events retrieved from the server
    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @returns: (None)
    """
    existing_event = find_timed_event_matching_time(event_details, nextcloud_events)
    if existing_event is None:
        create_timed_event(calendar, event_details)
    else:
        update_event(
            new_event=event_details,
            old_event=existing_event,
        )


def find_day_event_matching_date(
    event: CalpyEvent, nextcloud_events: list[caldav.Event]
) -> caldav.Event | None:
    """
    Look for a day event by given dates in nextcloud.
    If one is found, returns the event.
    Else, return None.

    @param event_details: (Event) the description of an event
    @param nextcloud_events: (list[caldav.Event]) the existing events retrieved from the server
    @return: (Optional[Event]) Already existing event with overlaping time.
    """
    if not event.is_all_day:
        return None
    timeMin = event.start["date"]
    timeMax = event.end["date"]
    events_filtered = filter_day_events_matching_times(
        timeMin, timeMax, nextcloud_events
    )
    if events_filtered:
        return events_filtered[0]


def find_timed_event_matching_time(
    event: CalpyEvent, nextcloud_events: list[caldav.Event]
) -> caldav.Event | None:
    """
    Look for a timed event by given date and times in nextcloud.
    If one is found, returns the event.
    Else, return None.

    @param event_details: (Event) the description of an event
    @param nextcloud_events: (list[caldav.Event]) the existing events retrieved from the server
    @return: (Optional[Event]) Already existing event with overlaping time.
    """
    if event.is_all_day:
        return None
    timeMin = event.start["dateTime"]
    timeMax = event.end["dateTime"]
    events_filtered = filter_timed_events_matching_datetimes(
        timeMin, timeMax, nextcloud_events
    )
    if events_filtered:
        return events_filtered[0]


def caldav_event_vevent(event: caldav.Event):
    """
    Returns the VEVENT component of the caldav event.
    caldav documentation isn't clear but we're only fetching events
    so we can be sure the VEVENT component is there.

    @param event: (caldav.Event) the event
    @return: (caldav.Object) the VEVENT component
    """
    return event.icalendar_component


def filter_day_events_matching_times(
    timeMin: str, timeMax: str, nextcloud_events: list[caldav.Event]
) -> list[caldav.Event]:
    """
    Returns a list of caldav.Event which :
    - are day events,
    - starts between timeMin and timeMax

    @param timeMin: (str) an fromisoformat date.
    @param timeMax: (str) an fromisoformat date.
    @param nextcloud_events: (list[caldav.Event]) the retrieved events
    @return: (list[caldav.Event]) the matching events.
    """
    tz = timezone("Europe/Paris")
    time_min = datetime.datetime.fromisoformat(timeMin).astimezone(tz)
    time_max = datetime.datetime.fromisoformat(timeMax).astimezone(tz)

    found_events = []
    for event in nextcloud_events:
        vevent = caldav_event_vevent(event)
        if not vevent:
            continue
        # fmt: off
        dtstart: datetime.datetime = vevent.get("DTSTART").dt
        dtstart = datetime.datetime.combine(dtstart, datetime.datetime.min.time()).astimezone(tz)
        dtend: datetime.datetime = vevent.get("DTEND").dt
        dtend = datetime.datetime.combine(dtend, datetime.datetime.min.time()).astimezone(tz)
        # fmt: on
        delta = dtend - dtstart
        # we muse ensure not to compare date and datetime
        if delta >= datetime.timedelta(hours=24) and time_min <= dtstart <= time_max:
            found_events.append(event)
    return found_events


def filter_timed_events_matching_datetimes(
    timeMin: str, timeMax: str, nextcloud_events: list[caldav.Event]
) -> list[caldav.Event]:
    """
    Returns a list of caldav.Event which :
    - are timed events,
    - starts between timeMin and timeMax

    @param timeMin: (str) an fromisoformat datetime.
    @param timeMax: (str) an fromisoformat datetime.
    @param nextcloud_events: (list[caldav.Event]) the retrieved events
    @return: (list[caldav.Event]) the matching events.
    """
    time_min = datetime.datetime.fromisoformat(timeMin)
    time_max = datetime.datetime.fromisoformat(timeMax)

    found_events = []
    for event in nextcloud_events:
        vevent = caldav_event_vevent(event)
        if not vevent:
            continue
        dtstart: datetime.datetime = vevent.get("DTSTART").dt
        # dtstart for timed event is a datetime not a date
        if type(time_min) == type(dtstart) and time_min <= dtstart <= time_max:
            found_events.append(event)
    return found_events


def create_day_event(
    calendar: caldav.Calendar, event_details: CalpyEvent
) -> caldav.Event:
    """
    Create a new day event with given details

    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @param event_details: (dict) description of the event
    @return: (None)
    """
    dtstart = datetime.date.fromisoformat(event_details.start["date"])
    dtend = datetime.date.fromisoformat(event_details.end["date"])

    cal_event = create_any_event(calendar, event_details, dtstart, dtend)

    creation_event_msg = f"DAY Event created: {event_details.readable_start_date()} {event_details.summary}"
    print(color_text(creation_event_msg, "YELLOW", "BOLD"))
    logger.warning(creation_event_msg)
    return cal_event


def create_timed_event(
    calendar: caldav.Calendar, event_details: CalpyEvent
) -> caldav.Event:
    """
    Create a new timed event with given details

    @param calendar: (caldav.Calendar) the matching calendar on nextcloud server
    @param event_details: (dict) description of the event
    @return: (None)
    """
    tz = timezone("Europe/Paris")

    # fmt: off
    dtstart = datetime.datetime.fromisoformat(event_details.start["dateTime"]).astimezone(tz)
    dtend = datetime.datetime.fromisoformat(event_details.end["dateTime"]).astimezone(tz)
    # fmt: on

    cal_event = create_any_event(calendar, event_details, dtstart, dtend)

    print(cal_event.icalendar_instance)
    creation_event_msg = (
        f"Event created: {event_details.readable_start_date()} {event_details.summary}"
    )
    print(color_text(creation_event_msg, "YELLOW"))
    logger.warning(creation_event_msg)
    return cal_event


def create_any_event(
    calendar: caldav.Calendar,
    event_details: CalpyEvent,
    dtstart: datetime.datetime | datetime.date,
    dtend: datetime.datetime | datetime.date,
) -> caldav.Event:
    """
    Helper function to create any kind of event.
    Since both DAY event and TIMED event share the same API,
    we can refactor a little.
    @param calendar: (caldav.Calendar) the calendar where the event is saved
    @param event_details: (CalpyEvent) the event itself. It's start and end date won't be used here
    @param dtstart: (datetime.datetime | datetime.date) depending on event kind
    @param dtend: (datetime.datetime | datetime.date) depending on event kind
    """
    return calendar.add_event(
        dtstart=dtstart,
        dtend=dtend,
        summary=event_details.summary,
        description=event_details.description_raw,
        location=event_details.location,
        color=NEXTCLOUD_COLORS[event_details.colorId],
    )


def update_event(
    new_event: CalpyEvent,
    old_event: caldav.Event,
) -> None:
    """
    Update the details of an event with the new ones.
    If the event is unchanged, nothing is done.

    Compared details : description, summary, location, start and end.

    @param new_event: (CalpyEvent) the new event to push
    @param old_event: (caldav.Event) the old event to update
    @returns: (None)
    """
    if new_event.is_equal_nextcloud(old_event):
        unchanged_event_msg = f"Event didn't change: {new_event.readable_start_date()} {new_event.summary}"
        # Nothing is done, we just print a message.
        if new_event.is_all_day:
            unchanged_event_msg = "DAY " + unchanged_event_msg
            print(color_text(unchanged_event_msg, "PURPLE", "BOLD"))
        else:
            print(color_text(unchanged_event_msg, "PURPLE"))
        logger.warning(unchanged_event_msg)
    else:
        update_old_components(old_event, new_event)
        old_event.save(no_overwrite=False)

        unchanged_event_msg = (
            f"Event updated: {new_event.readable_start_date()} {new_event.summary}"
        )
        if new_event.is_all_day:
            unchanged_event_msg = "DAY " + unchanged_event_msg
            print(color_text(unchanged_event_msg, "CYAN", "BOLD"))
        else:
            print(color_text(unchanged_event_msg, "CYAN"))
        logger.warning(unchanged_event_msg)


def update_old_components(old_event: caldav.Event, new_event: CalpyEvent):
    """
    Update every component of the Caldav event with new ones.

    WATCHOUT: it doesn't _save_ the event ! It's the responsability of the caller

    @param old_event: (caldav.Event)
    @param new_event: (CalpyEvent)
    """
    newdtstart, newdtend = new_event.nextcloud_dates()
    old_event.icalendar_component["dtstart"].dt = newdtstart
    old_event.icalendar_component["dtend"].dt = newdtend
    old_event.icalendar_component["summary"] = new_event.summary
    old_event.icalendar_component["description"] = new_event.description_raw
    old_event.icalendar_component["location"] = new_event.location
