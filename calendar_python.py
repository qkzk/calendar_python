'''
---
title: Calendar Python
author: qkkz
date: 2019/08/08
description:
'Lit un fichier .md formaté par cahier_texte_generator et ajoute les
événements dans google calendar'
---
'''


import logging
import os
import sys
import pytz
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pprint import pprint
import explore_md_file
from calendar_id import PYTHON_LYCEE_ID

# constants

# messages
WARNING_MSG = """
Create your Google Calendar Events from a .md File.

Warnings !

1. The Google Calendar Events will be updated or created
2. The .md file must be correctly formatted
3. There's no other warnings after this message.

"""
WRONG_PATH_MSG = """
Please provide a period number [1:5]
and a correct week number for that period
"""
EXPLORING_MSG = """
Starting to explore the given week... please wait...

"""
CONFIRMATION_MSG = """
DONE ADDING THE EVENTS TO GOOGLE CALENDAR !

"""
INPUT_WARNING_MSG = "Do you want to continue (y/N) : ? "
QUICK_EXIT_MSG = "That's ok, exiting"
STARTING_APPLICATION_MSG = 'Calendar Python started !'
LOGFILE = 'calendar_python.log'

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']


# Google Calendar settings
TZ = pytz.timezone("Europe/Paris")


# variables
text_description_example = '''<ul><li>voila voila</li><li>revoila</li></ul>'''
default_path_md = "/home/quentin/gdrive/dev/python/boulot_utils/cahier_texte_generator/calendrier/2019/periode_{}/semaine_{}.md"


# GOOGLE API FUNCTIONS


def get_cred():
    '''
    Returns the credentials for google calendar api

    @return service: (googleapiclient.discovery.Resource) le service passé
    '''
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def build_service():
    '''
    Return the google api client service ressource
    Start by building the credentials if needed

    @return: (googleapiclient.discovery.Resource)
    '''
    creds = get_cred()
    service = build('calendar', 'v3', credentials=creds)
    return service


def get_event_property(event, property, display=False):
    '''
    Renvoie une propriété d'un événement
    @param event: () un event
    @return : (any) la propriété de l'événement
    '''
    # event = get_event_details(eventID, service)
    property_value = None
    if property in event:
        property_value = event[property]
    if display:
        print(property, property_value)
    return property_value


def get_event(eventId, service):
    '''
    renvoie l'événement donné par eventID
    '''
    id = eventId
    event = service.events().get(calendarId=PYTHON_LYCEE_ID,
                                 eventId=id
                                 ).execute()
    return event


def find_next_event_by_date(given_time=None):
    '''
    Return the first evenement that finish after given_time.
    If no given_time is provided, the current time is used.

    @param given_time: (datetime.datetime obj) the time written as locally
    @return: (google api event object) the next event
        if no event is found, return None
    '''
    service = build_service()
    if given_time:
        requested_dt = pytz.timezone("Europe/Paris").localize(
            given_time,
            is_dst=None
        )
        str_dt = requested_dt
        dt_astimz_utc = str_dt.astimezone(pytz.utc)
        dt_string = dt_astimz_utc.strftime('%Y-%m-%dT%H:%M:%S.000000Z')

    if not given_time:
        str_dt = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    # attention va renvoyer le premier événement qui se termine avant timeMin
    events_result = service.events().list(calendarId=PYTHON_LYCEE_ID,
                                          timeMin=dt_string,
                                          maxResults=1,
                                          singleEvents=True,
                                          orderBy='startTime'
                                          ).execute()
    if len(events_result) > 0:
        event = events_result.get('items', [])[0]
        return event


def get_next_event_list(next_nb=10, display=False):
    '''
    Return the list of the next 10 events
    @param next_nb: (int) how many events do you want ?
    @return: (list) list of next 10 events starting now
    '''
    service = build_service()

    # Prints the start and name of the next 10 events on the user's calendar.
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    print(now)

    events_result = service.events().list(calendarId=PYTHON_LYCEE_ID,
                                          timeMin=now,
                                          maxResults=next_nb,
                                          singleEvents=True,
                                          orderBy='startTime'
                                          ).execute()
    events = events_result.get('items', [])

    if display:
        print('Getting the upcoming 10 events')
        if not events:
            print('No upcoming events found.')
        for event in events:
            details_list = {}
            start = event['start'].get('dateTime',
                                       event['start'].get('date'),
                                       )
            details_list['start'] = start
            details_list['end'] = event['end'].get(event['end'].get('date'))
            details_list['summary'] = event['summary']
            if 'description' in event:
                details_list['description'] = event['description']
            details_list['etag'] = event['etag']

            # print(start, end, description, event['summary'])
            pprint(details_list)

            print("\nevent complete :\n")
            pprint(event)
    return events


def get_calendar_list(display=False):
    '''
    List the calendars for given credentials
    '''
    service = build_service()

    calendar_results = service.calendarList().list().execute()
    calendars = calendar_results.get('items', [])
    if display:
        print("\nCalendar List : \n")
        if not calendars:
            print('No Calendars found.')
        for calendar_list_entry in calendars:
            pprint(calendar_list_entry)
    return calendars


def update_event(event_details,
                 eventId=None,
                 event=None,
                 service=None,
                 update_description=False):
    '''
    Update the details of an event.
    The event can be passed or only his id
    If no service is given, will create the service


    @param event_details: (dic) les attributs de l'événements à mettre à jour
    @param eventId: (str) l'id
    @param event: (google api event object) the event itself
    @param service: (google api ressource service object) the service object
    @param update_description : (bool) doit on cumuler la description ou
        la remplacer ?
    '''
    if not service:
        service = build_service()

    if not eventId and not event:
        raise ValueError("You must provide the event or its eventId")

    if not event:
        event = get_event(eventId, service)

    if update_description:
        old_desc = get_event_property(event, 'description', display=True)
        if old_desc:
            event_details['description'] = old_desc + event_details[
                'description']

    for attribute, value in event_details.items():
        event[attribute] = value

    updated_event = service.events().update(
        calendarId=PYTHON_LYCEE_ID, eventId=event['id'], body=event).execute()

    # Print the updated date.

    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=LOGFILE, level=logging.DEBUG)
    update_event_msg = "updated the event: {}".format(updated_event["htmlLink"])
    print(update_event_msg)
    logging.warning(update_event_msg)


def test_uploads_from_md(path, service=None):
    '''
    Create events from md file

    Create events even if they exists... :(

    desired behavior : only update if exists
    '''
    if service == None:
        service = build_service()
    events = explore_md_file.extract_events_from_file(path)
    for event_dic in events:
        # pprint(event)
        existing_event = event_already_have_id(event_dic, service)
        if not existing_event:
            create_event(event_details=event_dic, service=service)
        else:
            update_event(event_dic, event=existing_event, service=service)


def event_already_have_id(event, service=None):
    '''
    Look for an event by given dates in calendar.
    If one is found, return the event.
    Else, return None.

    @param event: (dic) event description, respecting precise format
    @return: (google api event object) description of the event if it already
        exists
    '''
    if not service:
        service = build_service()

    timeMin = event["start"]["dateTime"]
    timeMax = event["end"]["dateTime"]

    events_result = service.events().list(calendarId=PYTHON_LYCEE_ID,
                                          timeMin=timeMin,
                                          timeMax=timeMax,
                                          maxResults=1,
                                          singleEvents=True,
                                          orderBy='startTime'
                                          ).execute()
    events = events_result.get('items', [])

    if events:
        return events[0]
    return None


def create_event(event_details=None, service=None):
    '''
    Create a new event with given details
    @param event_details: (dic) description of the event
    @param service: (google api ressource service) the service
    @return: (None)
    '''

    if service == None:
        service = build_service()
    event = service.events().insert(
        calendarId=PYTHON_LYCEE_ID,
        body=event_details,
    ).execute()

    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=LOGFILE, level=logging.DEBUG)
    creation_event_msg = 'Event created: {}'.format(event.get('htmlLink'))
    print(creation_event_msg)
    logging.warning(creation_event_msg)


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
    eventId = get_event_property(next_event, 'id', display=True)

    event_details = {}
    event_details['location'] = '213'
    event_details['description'] = text_description_example

    # update_event(event_details, eventId=eventId,  update_description=True)
    update_event(event_details, event=next_event,  update_description=True)

    # test_uploads_from_md
    # print()
    path = explore_md_file.example_week_md_path
    test_uploads_from_md(path)


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
    # warnings
    print(WARNING_MSG)
    if len(sys.argv) < 2:
        raise ValueError(WRONG_PATH_MSG)
    period_number = int(sys.argv[1])
    week_number = int(sys.argv[2])

    path = default_path_md.format(period_number, week_number)

    print(path)
    input_warning = input(INPUT_WARNING_MSG)
    if input_warning != 'y':
        print(QUICK_EXIT_MSG)
        exit(-1)

    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=LOGFILE, level=logging.DEBUG)

    print(STARTING_APPLICATION_MSG)
    logging.warning(STARTING_APPLICATION_MSG)

    if not os.path.exists(path):
        print(path)
        logging.debug('File not found : {}'.format(path))
        raise FileNotFoundError(WRONG_PATH_MSG)

    print(EXPLORING_MSG)
    test_uploads_from_md(path)
    print(CONFIRMATION_MSG)


if __name__ == '__main__':
    # test_functions()
    create_or_update_week_events()
