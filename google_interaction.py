from __future__ import annotations

from pprint import pprint
from typing import Any, Optional, Union

import datetime
import pickle
import os.path

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from explore_md_file import parse_events
from config import CALENDAR_ID
from colors import color_text
from logger import logger
from model import Event


# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_credentials() -> Union[Credentials, Any]:
    """
    Returns the credentials for google calendar api

    @return service: (googleapiclient.discovery.Resource) le service passé
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds


def build_service() -> Resource:
    """
    Return the google api client service ressource
    Start by building the credentials if needed

    @return: (googleapiclient.discovery.Resource)
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service


def update_event(
    service: Resource,
    new_event: Event,
    old_event: Event,
) -> None:
    """
    Update the details of an event.
    The event can be passed or only his id
    If no service is given, will create the service


    @param event_details: (dict) les attributs de l'événements à mettre à jour
    @param new_event: (Event) the new event to push
    @param old_event: (Event) the old event to update
    @returns: (None)
    """
    old_event.update(new_event)

    updated_data = (
        service.events()
        .update(
            calendarId=CALENDAR_ID,
            eventId=old_event.id,
            body=old_event.__dict__,
        )
        .execute()
    )
    update_event_msg = "updated the event: {}".format(updated_data["htmlLink"])
    print(color_text(update_event_msg, "CYAN"))
    logger.warning(update_event_msg)


def sync_event_from_md(
    service: Resource,
    path: str,
) -> None:
    """
    Create or update events from md file

    @param service: (Resource) the google api ressource
    @param path: (str) path to the md file
    @returns: (None)
    @SE: insert or update events for a given week
    """
    event_list = parse_events(path)
    pprint(event_list)
    for event_details in event_list:
        update_or_create_event(service, event_details)


def update_or_create_event(
    service: Resource,
    event_details: Event,
) -> None:
    """
    Sync a single event read from a .md file.
    seek if the event already exists,
    if there's already an event, it's updated.
    Else, a new one is created

    @param service: (Resource) the google api ressource
    @param event_details: (Event) the description of an event
    @returns: (None)
    """
    if not event_details.is_all_day:
        existing_event = get_matching_existing_event(event_details, service)
        if existing_event is None:
            create_event(
                service=service,
                event_details=event_details,
            )
        else:
            update_event(
                service=service,
                new_event=event_details,
                old_event=existing_event,
            )
    else:
        timeMin = (
            datetime.datetime.strptime(event_details.start["date"], "%Y-%m-%d")
            - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%dT00:00:00Z")
        timeMax = (
            datetime.datetime.strptime(event_details.end["date"], "%Y-%m-%d")
        ).strftime("%Y-%m-%dT00:00:00Z")
        existing_events = list(get_day_events_matching_date(timeMin, timeMax, service))
        if event_details in existing_events:
            update_event(
                service=service,
                new_event=event_details,
                old_event=existing_events[existing_events.index(event_details)],
            )
        else:
            create_event(service=service, event_details=event_details)


def retrieve_events(timeMin: str, timeMax: str, service: Resource) -> map[Event]:
    return map(
        Event.from_dict,
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=timeMin,
            timeMax=timeMax,
            maxResults=200,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", []),
    )


def get_matching_existing_event(
    event: Event,
    service: Resource,
) -> Optional[Event]:
    """
    Look for an event by given dates in calendar.
    If one is found, return the event.
    Else, return None.

    @param event: (dic) event description, respecting precise format
    @return: (google api event object) description of the event if it already
        exists
    """
    if event.is_all_day:
        return None
    timeMin = event.start["dateTime"]
    timeMax = event.end["dateTime"]

    events_filtered = list(
        filter(
            lambda event: not "date" in event.start,
            retrieve_events(timeMin, timeMax, service),
        )
    )
    if events_filtered and not events_filtered[0].is_all_day:
        return events_filtered[0]


def get_day_events_matching_date(
    timeMin: str,
    timeMax: str,
    service: Resource,
) -> filter[Event]:
    """
    Returns a list of day events with same start and end time.
    @param timeMin: (str) like 2022-12-31T00:00:00Z
    @param timeMax: (str) like 2022-12-31T00:00:00Z
    @param service: (Resource) the google api ressource
    @returns: (filter[Event]) a collection of filtered day events where the date matches.
    """
    return filter(
        lambda event: "date" in event.start,
        retrieve_events(timeMin, timeMax, service),
    )


def create_event(
    service: Resource,
    event_details: Event,
) -> None:
    """
    Create a new event with given details
    @param event_details: (dict) description of the event
    @param service: (google api ressource service) the service
    @return: (None)
    """

    event = (
        service.events()
        .insert(
            calendarId=CALENDAR_ID,
            body=event_details.__dict__,
        )
        .execute()
    )

    creation_event_msg = f"Event created: {event.get('htmlLink')}"
    print(color_text(creation_event_msg, "YELLOW"))
    logger.warning(creation_event_msg)
