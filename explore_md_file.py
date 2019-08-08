'''
author : qkzk

explore an md file (formated as the example path) and return a list of event

each event is a dic and has the keys :
            * 'start':datetime,
            * 'end':datetime,
            * 'location':str
            * 'summary':str ('%' if no summary were given)
            * 'description':str (possibly empty or multiline)
            * 'colorId':str ('1' to '11')

'''

import datetime
from pprint import pprint

example_week_md_path = "/home/quentin/gdrive/dev/python/boulot_utils/cahier_texte_generator/calendrier/2019/periode_1/semaine_36.md"

traduction = {
    # on pourrait utiliser des locales et traduire automatiquement...
    "Lundi":     "Monday",
    "Mardi":     "Tuesday",
    "Mercredi":  "Wednesday",
    "Jeudi":     "Thursday",
    "Vendredi":  "Friday",
    "Samedi":    "Saturday",
    "Dimanche":  "Sunday",
    "janvier":   "January",
    "février":   "February",
    "mars":      "March",
    "avril":     "April",
    "mai":       "May",
    "juin":      "June",
    "juillet":   "July",
    "août":      "August",
    "septembre": "September",
    "octobre":   "October",
    "novembre":  "November",
    "décembre":  "December",
}


colors = {
    # rainbow order
    "11": "#dc2127",  # rouge
    "4": "#ff887c",   # Rosé
    "6": "#ffb878",   # orange clair
    "5": "#fbd75b",   # Jaune un peu foncé
    "10": "#51b749",  # vert clair
    "2": "#7ae7bf",   # jade
    "1": "#a4bdfc",   # Bleu pale
    "7": "#46d6db",   # bleu clair
    "9": "#5484ed",   # bleu foncé
    "3": "#dbadff",   # Violet clair
    "8": "#e1e1e1",   # gris clair
}

student_class_colors = {
    "isn": "5",
    "2nde 3": "7",
    "truc": "3",
    "%": "8"
}


def explore_md_file(path):
    '''
    open a file and return the list of lines as str

    @param path: (str) the path of the given file
    @return: (list of str) every line is a string
    '''
    with open(path, mode='r') as f:
        file_lines = f.readlines()
        # print(file_lines)
    return file_lines


def get_date_from_line(line):
    '''
    Extract the date from a line :
    ## Lundi 02 septembre   -----> 2019-09-02 00:00:00

    @param line: (str) a line from the .md file
    @return: (datetime.datetime obj) a date
    '''
    # new date
    date_str = line[3:]
    date_list = date_str.strip().split(' ')
    # print(date_list)
    day_of_the_week = traduction[date_list[0]]
    day_nb = date_list[1]
    month = traduction[date_list[2]]
    date_str_strp = '-'.join([month, day_nb])
    date_str_strp = '2019-' + date_str_strp
    date_day = datetime.datetime.strptime(date_str_strp, '%Y-%B-%d')

    return date_day


def get_events_from_str(events_dic_str_from_lines):
    '''
    loop through the lines and extrac the events
    return them as a dict of datetime: list of events

    @param events_dic_str_from_lines : (str) formated like :

    * 8h-8h55 - s213 - 2nde 3
    * corriger exo machin chose
    * rendre devoir
    rendre travail truc
    @return: (dic) the events of that date datetime: list of events
        each event has the keys :
            * 'start':datetime,
            * 'end':datetime,
            * 'location':str
            * 'summary':str ('%' if no summary were given)
            * 'description':str (possibly empty or multiline)
            * 'colorId':str ('1' to '11')
    '''
    event_per_date = {}
    for dt_key, string_list in events_dic_str_from_lines.items():
        # print(dt_key, string_list)
        event_list = []
        for string_event in string_list:
            first_line = string_event[0]
            # * 8h55-9h50 - s215
            first_string_list = first_line.strip().split(' - ')
            # print(first_string_list)

            hours = first_string_list[0]
            start, end = get_hours(dt_key, hours)
            if len(first_string_list) > 1:
                location = first_string_list[1]
            event = {
                # "hours": get_hours(dt_key, hours),
                "start": start,
                "end": end,
                "location": location,
            }
            if len(first_string_list) > 2:
                student_class = first_string_list[2]
                event["summary"] = student_class
            else:
                event["summary"] = '%'
            if event["summary"] in student_class_colors:
                event["colorId"] = student_class_colors[event["summary"]]
            if len(first_line) > 1:
                description = '\n'.join(string_event[1:])
                event["description"] = description.strip()
            event_list.append(event)
        event_per_date[dt_key] = event_list
        # break
    return event_per_date


def get_hours(dt_key, hours):
    """
    Extract the start and end datetime of a given string

    @param dt_key: datetime.datetime(2019, 9, 6, 0, 0)
    @param hours: (str) '* 8h55-9h50'
    @return: (tuple) (start, end)
        example :
        'end': datetime.datetime(2019, 9, 2, 10, 55),
        'start': datetime.datetime(2019, 9, 2, 10, 0),


        start = {
            'dateTime': '2019-08-09T14:00:00+02:00',
            'timeZone': 'Europe/Paris',
            }
        end = {
        'dateTime': '2019-08-09T15:00:00+02:00'}
        'timeZone': 'Europe/Paris',
        }
    """
    hours = hours[2:]
    hours_list = hours.split('-')

    start_str = hours_list[0]
    end_str = hours_list[1]

    start_list = start_str.split('h')
    end_list = end_str.split('h')

    start_hour = int(start_list[0])
    start_minute = 0 if start_list[1] == '' else int(start_list[1])

    end_hour = int(end_list[0])
    end_minute = 0 if end_list[1] == '' else int(end_list[1])

    year = dt_key.year
    month = dt_key.month
    day = dt_key.day

    start = datetime.datetime(year, month, day, start_hour, start_minute)
    end = datetime.datetime(year, month, day, end_hour, end_minute)

    start = {'dateTime': format_dt_for_event(start), 'timeZone': 'Europe/Paris'}
    end = {'dateTime': format_dt_for_event(end), 'timeZone': 'Europe/Paris'}

    return start, end


def format_dt_for_event(time_of_event):
    '''
    '2019-08-09T15:00:00+02:00'
    '''
    time_format = "%Y-%m-%dT%H:%M:00+02:00"
    return datetime.datetime.strftime(time_of_event, time_format)


def get_event_from_lines(file_lines):
    '''
    Extract the events from lines of a file

    Return them as a dic of list of dic (to be flattened)
    see other functions for more detailled description of the events

    @param file_lines: (list of str) the lines of the md file
    @return : (dic)
    '''
    events_dic_str_from_lines = {}

    nb_file_lines = len(file_lines)

    for line_nb in range(nb_file_lines):
        line = file_lines[line_nb]

        if line.startswith('##'):
            # it's a new day...
            events_list_from_day = []
            date_day = get_date_from_line(line)
            # next line is blank
            line_nb += 2
            if line_nb >= nb_file_lines:
                break
            line = file_lines[line_nb]
            while line.startswith('*'):

                events_list_from_day.append([line.strip()])
                line_nb += 1
                line = file_lines[line_nb]
                while line.startswith('  ') or line in ['\n', '\r\n']:
                    events_list_from_day[-1].append(line.strip())
                    line_nb += 1
                    line = file_lines[line_nb]
            events_dic_str_from_lines[date_day] = events_list_from_day

        line_nb += 1
    return events_dic_str_from_lines


def extract_events_from_file(path=None):
    '''
    Extract all the events of a week, given by a md file
    see example_week_md_path file for a given format

    @param path: (str) path of the .md file
    @return : (list) all the events of a given week
    each event has the keys :
            * 'start':datetime,
            * 'end':datetime,
            * 'location':str
            * 'summary':str ('%' if no summary were given)
            * 'description':str (possibly empty or multiline)
            * 'colorId':str ('1' to '11')

    '''
    if not path:
        # example mode
        path = example_week_md_path
    file_lines = explore_md_file(example_week_md_path)
    # pprint(file_lines)
    events_dic_str_from_lines = get_event_from_lines(file_lines)
    # pprint(events_dic_str_from_lines)
    events_from_str = get_events_from_str(events_dic_str_from_lines)
    # pprint(events_from_str)
    nested_events = list(events_from_str.values())
    flat_events = [item for sublist in nested_events for item in sublist]
    return flat_events


if __name__ == '__main__':
    events = extract_events_from_file()
    pprint(events)
