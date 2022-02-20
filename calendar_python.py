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


import argparse
import datetime
import logging
import os
import os.path
import pickle
import sys
from os import listdir
from os.path import isfile, join
from pprint import pprint

import pytz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import explore_md_file
from calendar_id import PYTHON_LYCEE_ID
from arguments_parser import read_arguments

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
period_path = "/home/quentin/gdrive/cours/git_cours/cours/2021/periode_{}/"
default_path_md = period_path + "semaine_{}.md"

# GOOGLE API FUNCTIONS


def get_cred():
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


def build_service():
    """
    Return the google api client service ressource
    Start by building the credentials if needed

    @return: (googleapiclient.discovery.Resource)
    """
    creds = get_cred()
    service = build("calendar", "v3", credentials=creds)
    return service


def get_event_property(event, property, display=False):
    """
    Renvoie une propriété d'un événement
    @param event: () un event
    @return : (any) la propriété de l'événement
    """
    # event = get_event_details(eventID, service)
    property_value = None
    if property in event:
        property_value = event[property]
    if display:
        print(property, property_value)
    return property_value


def get_event(eventId, service):
    """
    renvoie l'événement donné par eventID
    """
    id = eventId
    event = service.events().get(calendarId=PYTHON_LYCEE_ID, eventId=id).execute()
    return event


def find_next_event_by_date(given_time=None):
    """
    Return the first evenement that finish after given_time.
    If no given_time is provided, the current time is used.

    @param given_time: (datetime.datetime obj) the time written as locally
    @return: (google api event object) the next event
        if no event is found, return None
    """
    service = build_service()
    if given_time:
        requested_dt = pytz.timezone("Europe/Paris").localize(given_time, is_dst=None)
        str_dt = requested_dt
        dt_astimz_utc = str_dt.astimezone(pytz.utc)
        dt_string = dt_astimz_utc.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

    if not given_time:
        str_dt = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

    # attention va renvoyer le premier événement qui se termine avant timeMin
    events_result = (
        service.events()
        .list(
            calendarId=PYTHON_LYCEE_ID,
            timeMin=dt_string,
            maxResults=1,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    if len(events_result) > 0:
        event = events_result.get("items", [])[0]
        return event


def get_next_event_list(next_nb=10, display=False):
    """
    Return the list of the next 10 events
    @param next_nb: (int) how many events do you want ?
    @return: (list) list of next 10 events starting now
    """
    service = build_service()

    # Prints the start and name of the next 10 events on the user's calendar.
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

    print(now)

    events_result = (
        service.events()
        .list(
            calendarId=PYTHON_LYCEE_ID,
            timeMin=now,
            maxResults=next_nb,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if display:
        print("Getting the upcoming 10 events")
        if not events:
            print("No upcoming events found.")
        for event in events:
            details_list = {}
            start = event["start"].get(
                "dateTime",
                event["start"].get("date"),
            )
            details_list["start"] = start
            details_list["end"] = event["end"].get(event["end"].get("date"))
            details_list["summary"] = event["summary"]
            if "description" in event:
                details_list["description"] = event["description"]
            details_list["etag"] = event["etag"]

            # print(start, end, description, event['summary'])
            pprint(details_list)

            print("\nevent complete :\n")
            pprint(event)
    return events


def get_calendar_list(display=False):
    """
    List the calendars for given credentials
    """
    service = build_service()

    calendar_results = service.calendarList().list().execute()
    calendars = calendar_results.get("items", [])
    if display:
        print("\nCalendar List : \n")
        if not calendars:
            print("No Calendars found.")
        for calendar_list_entry in calendars:
            pprint(calendar_list_entry)
    return calendars


def update_event(
    event_details, eventId=None, event=None, service=None, update_description=False
):
    """
    Update the details of an event.
    The event can be passed or only his id
    If no service is given, will create the service


    @param event_details: (dic) les attributs de l'événements à mettre à jour
    @param eventId: (str) l'id
    @param event: (google api event object) the event itself
    @param service: (google api ressource service object) the service object
    @param update_description : (bool) doit on cumuler la description ou
        la remplacer ?
    """
    if not service:
        service = build_service()

    if not eventId and not event:
        raise ValueError("You must provide the event or its eventId")

    if not event:
        event = get_event(eventId, service)

    if update_description:
        old_desc = get_event_property(event, "description", display=True)
        if old_desc:
            event_details["description"] = old_desc + event_details["description"]

    for attribute, value in event_details.items():
        event[attribute] = value

    updated_event = (
        service.events()
        .update(calendarId=PYTHON_LYCEE_ID, eventId=event["id"], body=event)
        .execute()
    )

    # Print the updated date.

    logging.basicConfig(
        format="%(asctime)s %(message)s", filename=LOGFILE, level=logging.DEBUG
    )
    update_event_msg = "updated the event: {}".format(updated_event["htmlLink"])
    print(update_event_msg)
    logging.warning(update_event_msg)


def sync_event_from_md(path, service=None):
    """
    Create or update events from md file
    """
    if service == None:
        service = build_service()
    events = explore_md_file.extract_events_from_file(path)
    # input("press ctrl + C to abort ")
    for event_dic in events:
        # pprint(event)
        existing_event = event_already_have_id(event_dic, service)
        if not existing_event:
            create_event(event_details=event_dic, service=service)
        else:
            update_event(event_dic, event=existing_event, service=service)


def event_already_have_id(event, service=None):
    """
    Look for an event by given dates in calendar.
    If one is found, return the event.
    Else, return None.

    @param event: (dic) event description, respecting precise format
    @return: (google api event object) description of the event if it already
        exists
    """
    if not service:
        service = build_service()

    timeMin = event["start"]["dateTime"]
    timeMax = event["end"]["dateTime"]

    events_result = (
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
    events = events_result.get("items", [])

    if events:
        return events[0]
    return None


def create_event(event_details=None, service=None):
    """
    Create a new event with given details
    @param event_details: (dic) description of the event
    @param service: (google api ressource service) the service
    @return: (None)
    """

    if service == None:
        service = build_service()
    event = (
        service.events()
        .insert(
            calendarId=PYTHON_LYCEE_ID,
            body=event_details,
        )
        .execute()
    )

    logging.basicConfig(
        format="%(asctime)s %(message)s", filename=LOGFILE, level=logging.DEBUG
    )
    creation_event_msg = "Event created: {}".format(event.get("htmlLink"))
    print(creation_event_msg)
    logging.warning(creation_event_msg)


def extract_number_from_path(week_md_filename):
    """
    Extract the number from a week .md filename

    "semaine_36.md"   ----> 36
    "semaine_1.md"    ----1 1

    @param week_md_filename: (str) the name of the md file
    @return: (int)
    """
    week_number = int(week_md_filename[:-3].split("_")[1])
    return week_number


def get_weeks_from_period(period_path):
    """
    Get the week numbers from a given period path
    List all the week from path
    @param period_path: (str) the path to the period folder
    @return: (list of int) the list of the weeks in that period
    """
    week_dirs_list = [f for f in listdir(period_path) if isfile(join(period_path, f))]

    week_number_list = sorted(list(map(extract_number_from_path, week_dirs_list)))
    return week_number_list


def color_text(text, color="BOLD"):
    return TEXT_COLORS[color] + text + TEXT_COLORS["END"]


def display_md_content(path):
    """
    Print the content of the md file to the console.
    @param: (path) the path to the md file
    @return: (None)
    """
    with open(path, mode="r") as mdfile:
        print(MD_CONTENT_MSG)
        print(color_text(mdfile.read(), "BOLD"))


def ask_path_to_user(arguments: argparse.Namespace, reset_path=False):
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

    return period_number, week_list


def convert_numbers_to_path(
    period_number: int, week_list: list[int], arguments: argparse.Namespace
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


def convert_week_numbers(week_numbers: list) -> list:
    """
    split the week numbers into a list of integers
    ["1", "2", "3"] -> [1, 2, 3]
    @param week_numbers: (str) a string containing the week numbers
    @return: (list of int) those numbers as int in a list
    """
    return list(map(int, week_numbers))


def warn_and_get_path(arguments: argparse.Namespace):
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
):
    while path_list == "" or input_warning != "y":
        period_number, week_list = ask_path_to_user(arguments, reset_path=reset_path)
        path_list = convert_numbers_to_path(period_number, week_list, arguments)
        # does the user wants to continue ? (that's the last warning)
        input_warning = input(color_text(color_text(INPUT_WARNING_MSG, "RED"), "BOLD"))
        reset_path = True
        if input_warning in ["n", "N"]:
            print(QUICK_EXIT_MSG)
            exit(-1)
    print(color_text("We have a path !", "YELLOW"))
    for path in path_list:
        print(color_text(path, "YELLOW"))

    return path_list


def test_functions():
    """
    Used to test some functions
    """
    # display event list
    next_event = get_next_event_list(next_nb=10, display=True)

    # calendar list id
    calendars = get_calendar_list(display=True)

    # Find the next event after a date
    dt = datetime.datetime(2019, 8, 9, 14, 0)
    print("\n next event")
    next_event = find_next_event_by_date(dt)
    pprint(next_event)

    # update the next_event
    eventId = get_event_property(next_event, "id", display=True)

    event_details = {}
    event_details["location"] = "213"
    event_details["description"] = text_description_example

    # update_event(event_details, eventId=eventId,  update_description=True)
    update_event(event_details, event=next_event, update_description=True)

    # test_uploads_from_md
    # print()
    path = explore_md_file.example_week_md_path
    sync_event_from_md(path)


def create_or_update_week_events():
    """
    The main function.

    Warn the user and, if he's ok, creates or update the events.
    Display some confirmation messages.

    The arguments (section number and week number) are read from the console
    section number must be between 1 and 5
    week number must be a correct week for that section

    If a file is found at correct path, it's explored.
    This is the dangerous zone, there's no warning but formatting
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
            print(path)
            logging.debug("File not found : {}".format(path))
            raise FileNotFoundError(WRONG_PATH_MSG)

        print(EXPLORING_MSG)
        sync_event_from_md(path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


if __name__ == "__main__":
    # test_functions()
    create_or_update_week_events()
