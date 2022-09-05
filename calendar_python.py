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
import logging.handlers
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
from model import Event

CURRENT_YEAR = 2022

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

GIT_COURS_REPO_PATH = "/home/quentin/gdrive/cours/git_cours/cours/"

PERIOD_LIST = range(1, 6)
PERIOD_PATH = f"{GIT_COURS_REPO_PATH}{CURRENT_YEAR}/" + "periode_{}/"
default_path_md = PERIOD_PATH + "semaine_{}.md"

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
            calendarId=PYTHON_LYCEE_ID,
            eventId=old_event.id,
            body=old_event.__dict__,
        )
        .execute()
    )
    update_event_msg = "updated the event: {}".format(updated_data["htmlLink"])
    print(update_event_msg)
    logger.warning(update_event_msg)


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
            new_event=event_details,
            old_event=existing_event,
        )


def get_first_event_from_event_date(
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
    timeMin = event.start["dateTime"]
    timeMax = event.end["dateTime"]

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
    first_event = events_from_googleapi.get("items", [None])[0]
    if first_event is not None:
        return Event.from_dict(first_event)


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
            calendarId=PYTHON_LYCEE_ID,
            body=event_details.__dict__,
        )
        .execute()
    )

    creation_event_msg = f"Event created: {event.get('htmlLink')}"
    print(creation_event_msg)
    logger.warning(creation_event_msg)


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


def get_md_path_from_args_or_user(
    arguments: argparse.Namespace,
    reset_path=False,
) -> tuple[Union[str, Any], list[Union[int, Any]]]:
    """
    Create the path from the args and ask the user what he wants to do.
    @param reset_path: (bool) do we have to reset the path ?
    @return: (str) the path to the md file
    """
    print(color_text(WARNING_MSG, "DARKCYAN"))

    if reset_path or len(sys.argv) == 1:
        # no parameters were given by the user
        mode = "Interactive"
        period_number = ask_user_period()
        period_path = PERIOD_PATH.format(period_number)
        week_list = ask_user_week(period_path)

    elif len(sys.argv) < 2:
        # wrong number of arguments
        raise ValueError(WRONG_PATH_MSG)
    else:
        # the user has provided at least a parameter
        mode = "CLI arguments"
        period_number = arguments.period_number
        week_list = convert_week_numbers(arguments.week_numbers)
    print(color_text(f"mode: {mode}", "DARKCYAN"))
    if not week_list:
        raise ValueError("week_list empty")

    return period_number, week_list


def ask_user_period() -> int:
    """
    Asks the user for a valid period number.
    Loops until the user gave a valid period number.
    @returns: (int) a period number from PERIOD_LIST
    """
    while True:
        period_str = input(GET_PERIOD_MSG)
        try:
            period_number = int(period_str)
        except ValueError:
            continue
        if period_number in PERIOD_LIST:
            return period_number


def ask_user_week(period_path: str) -> list[int]:
    """
    Returns a list of valid weeks for a given path.
    Loops untill the user provides a valid week list
    Typed weeks must be separated by spaces

    @param period_path: (str) the path for the given period.
    @returns: (list[int]) the list of weeks typed by the user
    """
    valid_weeks = get_weeks_from_period(period_path)
    while True:
        inputed_weeks = input(GET_WEEK_MSG.format(valid_weeks))
        try:
            week_list = list(map(int, inputed_weeks.split(" ")))
        except ValueError:
            continue
        if all(map(lambda week: week in valid_weeks, week_list)):
            return week_list


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
        period_number, week_list = get_md_path_from_args_or_user(
            arguments, reset_path=reset_path
        )
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

    print(color_text(STARTING_APPLICATION_MSG, "DARKCYAN"))
    logger.warning(STARTING_APPLICATION_MSG)

    for path in path_list:
        if not os.path.exists(path):
            logger.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        service: Resource = build_service()
        sync_event_from_md(service, path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


def create_logger() -> logging.Logger:
    """Creates a rotating file_handler logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOGFILE,
        maxBytes=5 * 1025 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(file_handler)
    return logger


if __name__ == "__main__":
    logger = create_logger()
    create_or_update_week_events()
