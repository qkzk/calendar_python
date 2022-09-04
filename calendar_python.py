"""
---
title: Calendar Python
author: qkkz
date: 2019/08/08
description:
'Lit un fichier .md formaté par cahier_texte_generator et ajoute les
événements dans google calendar'
---
"""

from os import listdir
from os.path import isfile, join
from typing import Any, Optional, Union

import argparse
import logging
import os
import os.path
import pickle
import sys

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

import pytz

import explore_md_file
from arguments_parser import read_arguments
from calendar_id import PYTHON_LYCEE_ID

# constants
TEXT_COLORS = {
    "PURPLE": "\033[95m",
    "CYAN": "\033[96m",
    "DARKCYAN": "\033[36m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "END": "\033[0m",
}

# messages
WELCOME_MSG = "welcome to..."
BANNER = """
########  ##    ## ######## ##     ##  #######  ##    ##
##     ##  ##  ##     ##    ##     ## ##     ## ###   ##
##     ##   ####      ##    ##     ## ##     ## ####  ##
########     ##       ##    ######### ##     ## ## ## ##
##           ##       ##    ##     ## ##     ## ##  ####
##           ##       ##    ##     ## ##     ## ##   ###
##           ##       ##    ##     ##  #######  ##    ##


 ######     ###    ##       ######## ##    ## ########     ###    ########
##    ##   ## ##   ##       ##       ###   ## ##     ##   ## ##   ##     ##
##        ##   ##  ##       ##       ####  ## ##     ##  ##   ##  ##     ##
##       ##     ## ##       ######   ## ## ## ##     ## ##     ## ########
##       ######### ##       ##       ##  #### ##     ## ######### ##   ##
##    ## ##     ## ##       ##       ##   ### ##     ## ##     ## ##    ##
 ######  ##     ## ######## ######## ##    ## ########  ##     ## ##     ##
"""

WARNING_MSG = """
Create your Google Calendar Events from a .md File.

Warnings !

1. The Google Calendar Events will be updated or created
2. The .md file must be correctly formatted or the application will crash

"""
GET_PERIOD_MSG = "Please choose a period in [1-5] : "
GET_WEEK_MSG = "Please choose a week in {} : "
WRONG_PATH_MSG = """
Please provide a period number [1:5]
and a correct week number for that period
"""
INPUT_PRINT_MD_FILE = "Do you want to see the content of the file (y/N) ? "
EXPLORING_MSG = """
Starting to explore the given week... please wait...

"""

MD_CONTENT_MSG = "This is the content of the .md file :\n"
INPUT_WARNING_MSG = """LAST WARNING !

Do you want to continue ?
Press (y) to continue, (n) to exit or another key to look for another file : """
QUICK_EXIT_MSG = "That's ok, exiting"
STARTING_APPLICATION_MSG = "Calendar Python started !"
CONFIRMATION_MSG = """
DONE ADDING THE EVENTS TO GOOGLE CALENDAR !

"""

# logs etc.
LOGFILE = "calendar_python.log"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Google Calendar settings
TZ = pytz.timezone("Europe/Paris")

# variables
text_description_example = """<ul><li>voila voila</li><li>revoila</li></ul>"""
# Example path, for testing
# default_path_md = "/home/quentin/gdrive/dev/python/boulot_utils/cahier_texte_generator/calendrier/2019/periode_{}/semaine_{}.md"
# Real path

period_list = range(1, 6)
period_path = "/home/quentin/gdrive/cours/git_cours/cours/2022/periode_{}/"
default_path_md = period_path + "semaine_{}.md"

# GOOGLE API FUNCTIONS


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


def get_event_property(
    event: dict[str, dict[str, str]],
    property: str,
) -> Optional[Union[str, dict[str, str]]]:
    """
    Renvoie une propriété d'un événement
    @param event: () un event
    @return : (any) la propriété de l'événement
    """
    value = event.get(property)
    print(property, value)
    return value


def get_existing_event(
    service: Resource,
    eventId: str,
) -> Optional[dict[str, dict[str, str]]]:
    """
    returns an event from its eventID
    Returns None if nothing is found.

    @param service: (Resource) the google api ressource
    @eventId: (str) the given event id, a string containing an integer
    @returns: (Optional[dict[str, dict[str, str]]]) the event, if any.
    """
    event = service.events().get(calendarId=PYTHON_LYCEE_ID, eventId=eventId).execute()
    return event


# def find_next_event_by_date(given_time: Optional[datetime.datetime] = None):
#     """
#     Return the first evenement that finish after given_time.
#     If no given_time is provided, the current time is used.
#
#     @param given_time: (datetime.datetime obj) the time written as locally
#     @return: (google api event object) the next event
#         if no event is found, return None
#     """
#     service = build_service()
#     if given_time is None:
#         dt_string = (
#             datetime.datetime.utcnow().isoformat() + "Z"
#         )  # 'Z' indicates UTC time
#     else:
#         str_dt = pytz.timezone("Europe/Paris").localize(given_time, is_dst=None)
#         dt_astimz_utc = str_dt.astimezone(pytz.utc)
#         dt_string = dt_astimz_utc.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
#
#     # attention va renvoyer le premier événement qui se termine avant timeMin
#     events_result = (
#         service.events()
#         .list(
#             calendarId=PYTHON_LYCEE_ID,
#             timeMin=dt_string,
#             maxResults=1,
#             singleEvents=True,
#             orderBy="startTime",
#         )
#         .execute()
#     )
#     if len(events_result) > 0:
#         event = events_result.get("items", [])[0]
#         return event


# def get_next_event_list(next_nb=10, display=False):
#     """
#     Return the list of the next 10 events
#     @param next_nb: (int) how many events do you want ?
#     @return: (list) list of next 10 events starting now
#     """
#     service = build_service()
#
#     # Prints the start and name of the next 10 events on the user's calendar.
#     # Call the Calendar API
#     now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
#
#     print(now)
#
#     events_result = (
#         service.events()
#         .list(
#             calendarId=PYTHON_LYCEE_ID,
#             timeMin=now,
#             maxResults=next_nb,
#             singleEvents=True,
#             orderBy="startTime",
#         )
#         .execute()
#     )
#     events = events_result.get("items", [])
#
#     if display:
#         print("Getting the upcoming 10 events")
#         if not events:
#             print("No upcoming events found.")
#         for event in events:
#             details_list = {}
#             start = event["start"].get(
#                 "dateTime",
#                 event["start"].get("date"),
#             )
#             details_list["start"] = start
#             details_list["end"] = event["end"].get(event["end"].get("date"))
#             details_list["summary"] = event["summary"]
#             if "description" in event:
#                 details_list["description"] = event["description"]
#             details_list["etag"] = event["etag"]
#
#             # print(start, end, description, event['summary'])
#             # pprint(details_list)
#
#             print("\nevent complete :\n")
#             # pprint(event)
#     return events


# def get_calendar_list(display=False):
#     """
#     List the calendars for given credentials
#     """
#     service = build_service()
#
#     calendar_results = service.calendarList().list().execute()
#     calendars = calendar_results.get("items", [])
#     if display:
#         print("\nCalendar List : \n")
#         if not calendars:
#             print("No Calendars found.")
#         for calendar_list_entry in calendars:
#             pprint(calendar_list_entry)
#     return calendars


def update_event(
    service: Resource,
    event_details: dict,
    eventId: Optional[str] = None,
    existing_event: Optional[dict[str, dict[str, str]]] = None,
    update_description: bool = False,
) -> None:
    """
    Update the details of an event.
    The event can be passed or only his id
    If no service is given, will create the service


    @param event_details: (dict) les attributs de l'événements à mettre à jour
    @param eventId: (str) l'id
    @param existing_event: (google api event object) the event itself
    @param service: (google api ressource service object) the service object
    @param update_description : (bool) doit on cumuler la description ou
        la remplacer ?
    @returns: (None)
    """
    if eventId is None and existing_event is None:
        raise ValueError("You must provide the event or its eventId")

    if existing_event is None and eventId is not None:
        existing_event = get_existing_event(service, eventId)

    if existing_event is None:
        raise ValueError(
            f"event unknown - eventId: {eventId}, event_details: {event_details}"
        )

    if update_description:
        old_desc = get_event_property(existing_event, "description")
        if old_desc:
            event_details["description"] = old_desc + event_details["description"]

    for attribute, value in event_details.items():
        existing_event[attribute] = value

    updated_event = (
        service.events()
        .update(
            calendarId=PYTHON_LYCEE_ID,
            eventId=existing_event["id"],
            body=existing_event,
        )
        .execute()
    )

    # Print the updated date.

    logging.basicConfig(
        format="%(asctime)s %(message)s", filename=LOGFILE, level=logging.DEBUG
    )
    update_event_msg = "updated the event: {}".format(updated_event["htmlLink"])
    print(update_event_msg)
    logging.warning(update_event_msg)


def sync_event_from_md(
    service: Resource,
    path: str,
) -> None:
    """
    Create or update events from md file
    """
    event_list = explore_md_file.extract_events_from_file(path)
    for event_details in event_list:
        update_or_create_event(service, event_details)


def update_or_create_event(
    service: Resource,
    event_details: dict[str, dict[str, str]],
) -> None:
    """
    Sync a single event read from a .md file.
    seek if the event already exists,
    if there's already an event, it's updated.
    Else, a new one is created

    @param service: (Resource) the google api ressource
    @param event_details: (dict[str, dict[str, str]]) the description of an event
    @returns: (None)
    """
    existing_event = get_first_event_from_event_date(event_details, service)
    if existing_event is None:
        create_event(
            service=service,
            event_details=event_details,
        )
    else:
        update_event(
            service=service,
            event_details=event_details,
            existing_event=existing_event,
        )


def get_first_event_from_event_date(
    event: dict[str, dict[str, str]],
    service: Resource,
) -> Optional[dict[str, dict[str, str]]]:
    """
    Look for an event by given dates in calendar.
    If one is found, return the event.
    Else, return None.

    @param event: (dic) event description, respecting precise format
    @return: (google api event object) description of the event if it already
        exists
    """
    timeMin = event["start"]["dateTime"]
    timeMax = event["end"]["dateTime"]

    events_from_googleapi = (
        service.events()
        .list(
            calendarId=PYTHON_LYCEE_ID,
            timeMin=timeMin,
            timeMax=timeMax,
            maxResults=1,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_from_googleapi.get("items", [None])
    return events[0]


def create_event(
    service: Resource,
    event_details: dict[str, dict[str, str]],
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
            calendarId=PYTHON_LYCEE_ID,
            body=event_details,
        )
        .execute()
    )

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        filename=LOGFILE,
        level=logging.DEBUG,
    )
    creation_event_msg = f"Event created: {event.get('htmlLink')}"
    print(creation_event_msg)
    logging.warning(creation_event_msg)


def extract_number_from_path(week_md_filename: str) -> int:
    """
    Extract the number from a week .md filename

    "semaine_36.md"   ----> 36
    "semaine_1.md"    ----1 1

    @param week_md_filename: (str) the name of the md file
    @return: (int)
    """
    week_number = int(week_md_filename[:-3].split("_")[1])
    return week_number


def get_weeks_from_period(period_path: str) -> list[int]:
    """
    Get the week numbers from a given period path
    List all the week from path
    @param period_path: (str) the path to the period folder
    @return: (list of int) the list of the weeks in that period
    """
    week_dirs_list = [f for f in listdir(period_path) if isfile(join(period_path, f))]
    week_number_list = sorted(list(map(extract_number_from_path, week_dirs_list)))
    return week_number_list


def color_text(text: str, color: str = "BOLD") -> str:
    """
    Color a line for shell printing.
    The string is encapsulated and rest of line will have default format.

    @param text: (str) text to be printed
    @param color: (str) used color or "BOLD"
    @returns: (str) formated string closed by an END tag.
    """
    return TEXT_COLORS[color] + text + TEXT_COLORS["END"]


def display_md_content(path: str) -> None:
    """
    Print the content of the md file to the console.
    @param: (path) the path to the md file
    @return: (None)
    """
    with open(path, mode="r") as mdfile:
        print(MD_CONTENT_MSG)
        print(color_text(mdfile.read(), "BOLD"))


def ask_path_to_user(
    arguments: argparse.Namespace,
    reset_path=False,
) -> tuple[Union[str, Any], list[Union[int, Any]]]:
    """
    Create the path from the args and ask the user what he wants to do.
    @param reset_path: (bool) do we have to reset the path ?
    @return: (str) the path to the md file
    """
    global period_path
    print(color_text(WARNING_MSG, "DARKCYAN"))

    if reset_path or len(sys.argv) == 1:
        # no parameters were given by the user
        period_number = -1
        while period_number not in period_list:
            period_number = int(input(GET_PERIOD_MSG))
        period_path = period_path.format(period_number)
        week_dirs_list = get_weeks_from_period(period_path)
        week_number = -1
        # while week_number not in week_dirs_list:
        #     week_number = int(input(GET_WEEK_MSG.format(week_dirs_list)))
        while True:
            inputed_weeks = input(GET_WEEK_MSG.format(week_dirs_list))
            if " " in inputed_weeks:
                mode = "multi_weeks"
                week_list = [int(number) for number in inputed_weeks.split(" ")]
                break

            else:
                week_number = int(inputed_weeks)
            if week_number in week_dirs_list:
                mode = "solo_week"
                week_list = [week_number]
                break

    elif len(sys.argv) < 2:
        # wrong number of arguments
        raise ValueError(WRONG_PATH_MSG)
    else:
        # the user has provided at least a parameter
        mode = "args_provided"
        period_number = arguments.period_number
        week_list = convert_week_numbers(arguments.week_numbers)
    print(color_text(mode, "DARKCYAN"))
    if len(week_list) == 0:
        raise ValueError("week_list empty")
    if not isinstance(week_list[0], int):
        raise ValueError("weeks must be integer")

    return period_number, week_list


def convert_numbers_to_path(
    period_number: str, week_list: list[int], arguments: argparse.Namespace
) -> list[str]:
    # we now have a complete path
    path_list = []
    for week_number in week_list:
        path = default_path_md.format(period_number, week_number)
        print(color_text(path + "\n", "YELLOW"))
        path_list.append(path)

    # does the user wants to see the events that will be created ?

    if arguments.interactive or arguments.view_content:
        input_print_md = input(INPUT_PRINT_MD_FILE)
        if input_print_md == "y":
            for path in path_list:
                display_md_content(path)
    return path_list


def convert_week_numbers(week_numbers: list[str]) -> list[int]:
    """
    Casts the week numbers into a list of integers
    ["1", "2", "3"] -> [1, 2, 3]
    @param week_numbers: (str) a string containing the week numbers
    @return: (list[int]) the list of casted strings into integers
    """
    return list(map(int, week_numbers))


def warn_and_get_path(arguments: argparse.Namespace) -> list[str]:
    """
    Warn the user about what's he's going to do and return the path provided
    by the user.
    If no path is provided in the args, keep asking the user for a new one.

    @return: (str) the path to the md file
    """
    print(color_text(WELCOME_MSG, "DARKCYAN"))
    print(color_text(color_text(BANNER, "DARKCYAN"), "BOLD"))
    path_list = []
    reset_path = False
    input_warning = ""

    # 1st case : wrong arguments from argparse
    if (
        arguments.interactive
        or arguments.period_number is None
        or arguments.week_numbers == []
    ):

        print("Interactive mode")
        path_list = interactive_mode(path_list, reset_path, input_warning, arguments)
    else:
        path_list = convert_numbers_to_path(
            arguments.period_number, arguments.week_numbers, arguments
        )
        if not arguments.yes:
            path_list = interactive_mode(
                path_list, reset_path, input_warning, arguments
            )
    return path_list


def interactive_mode(
    path_list: list[str],
    reset_path: bool,
    input_warning: str,
    arguments: argparse.Namespace,
) -> list[str]:
    while user_provides_invalid_input(path_list, input_warning):
        period_number, week_list = ask_path_to_user(arguments, reset_path=reset_path)
        path_list = convert_numbers_to_path(period_number, week_list, arguments)
        # does the user wants to continue ? (that's the last warning)
        input_warning = input(color_text(color_text(INPUT_WARNING_MSG, "RED"), "BOLD"))
        reset_path = True
        if input_warning in ["n", "N"]:
            print(QUICK_EXIT_MSG)
            exit(2)
    print_paths(path_list)
    return path_list


def print_paths(path_list: list[str]) -> None:
    """
    Prints every path in pathlist
    @param path_list: (list[str]) a list of valid paths
    @returns: (None)
    """
    for path in path_list:
        print(color_text(path, "YELLOW"))


def user_provides_invalid_input(
    path_list: list[str],
    input_warning: str,
) -> bool:
    """
    True if the provided input is invalid
    inputs are invalid if they can't be converted into a list of valid files
    or if the user didn't provide a "y".

    @param path_list: (list[str]) a list of valid week numbers
    @param input_warning: (str) "y" or another inputed string.
    """
    return not path_list or input_warning != "y"


# def test_functions():
#     """
#     Used to test some functions
#     """
#     # display event list
#     next_event = get_next_event_list(next_nb=10, display=True)
#
#     # calendar list id
#     calendars = get_calendar_list(display=True)
#
#     # Find the next event after a date
#     dt = datetime.datetime(2019, 8, 9, 14, 0)
#     print("\n next event")
#     next_event = find_next_event_by_date(dt)
#     pprint(next_event)
#
#     # update the next_event
#     eventId = get_event_property(next_event, "id", display=True)
#
#     event_details = {}
#     event_details["location"] = "213"
#     event_details["description"] = text_description_example
#
#     # update_event(event_details, eventId=eventId,  update_description=True)
#     update_event(event_details, event=next_event, update_description=True)
#
#     # test_uploads_from_md
#     # print()
#     path = explore_md_file.example_week_md_path
#     sync_event_from_md(path)


def create_or_update_week_events() -> None:
    """
    The main function.

    Warn the user and, if he's ok, creates or update the events.
    Display some confirmation messages.

    The arguments (section number and week number) are read from the console
    section number must be between 1 and 5
    week number must be a correct week for that section

    If a file is found at correct path, it's explored.
    This is the danger zone, there's no warning but formatting
    must be correct.

    The application will crash if it can't read the content of the file
    or if the dates aren't correct.

    the logs are written to a LOGFILE

    @return: None

    """
    arguments = read_arguments()
    print(arguments)
    # get the path from the user, provided as args or not.
    path_list = warn_and_get_path(arguments)
    # if isn't exited yet, we continue.

    logging.basicConfig(
        format="%(asctime)s %(message)s", filename=LOGFILE, level=logging.DEBUG
    )

    print(color_text(STARTING_APPLICATION_MSG, "DARKCYAN"))
    logging.warning(STARTING_APPLICATION_MSG)

    for path in path_list:
        if not os.path.exists(path):
            logging.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        service: Resource = build_service()
        sync_event_from_md(service, path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


if __name__ == "__main__":
    # test_functions()
    create_or_update_week_events()
