"""
author : qkzk

explore an md file (formated as the example path) and return a list of event

each event is a dic and has the keys :
            * 'start':datetime,
            * 'end':datetime,
            * 'location':str
            * 'summary':str ('%' if no summary were given)
            * 'description':str (possibly empty or multiline)
            * 'colorId':str ('1' to '11')

COLORS = {
    # rainbow order
    "11": "#dc2127",  # rouge
    "4":  "#ff887c",  # Rosé
    "6":  "#ffb878",  # orange clair
    "5":  "#fbd75b",  # Jaune un peu foncé
    "10": "#51b749",  # vert clair
    "2":  "#7ae7bf",  # jade
    "7":  "#46d6db",  # bleu clair
    "9":  "#5484ed",  # bleu foncé
    "1":  "#a4bdfc",  # Bleu pale
    "3":  "#dbadff",  # Violet clair
    "8":  "#e1e1e1",  # gris clair
}

"""

from typing import Optional, Union
import datetime

import markdown
import pytz

from model import Event

example_week_md_path = "/home/quentin/gdrive/dev/python/boulot_utils/cahier_texte_generator/calendrier/2019/periode_1/semaine_36.md"


TRADUCTION_MONTH = {
    "janvier": "January",
    "février": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December",
}

MONTHES_END_YEAR = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
]

STUDENT_CLASS_COLORS = {
    "2": ["ISN", "tale nsi"],
    "1": ["1ere NSI"],
    "9": ["ap", "orientation", "AP"],
    "8": ["2nd", "train"],
    "6": ["tmg2"],
    "11": ["l2s3", "l1s2", "l2s4", "croqmaths"],
    "7": ["imt", "CP2", "CP1"],
    "10": ["cdr", "CDR"],
    "3": ["réunion", "reunion", "conseil", "PP", "default"],
}

TIMEZONE = "Europe/Paris"

DEFAULT_COLOR = "11"

MD_LI_TOKENS = ("-", "*", "+")


def get_lines_from(path: str) -> list[str]:
    """
    open a file and return the list of lines as str

    @param path: (str) the path of the given file
    @return: (list of str) every line is a string
    """
    with open(path, mode="r", encoding="utf-8") as f:
        return f.readlines()


def parse_date(line: str) -> datetime.datetime:
    """
    Extract the date from a line :
    ## Lundi 02 septembre   -----> 2019-09-02 00:00:00
    ## Lundi 02 mai         -----> 2020-05-02 00:00:00

    @param line: (str) a line from the .md file
    @return: (datetime.datetime obj) a datetime at midnight (ie a date)
    """
    date_list = line[3:].strip().split(" ")
    day = date_list[1]
    month = TRADUCTION_MONTH[date_list[2]]
    year = get_current_year(month)
    date_str = f"{year}-{month}-{day}"
    date_day = datetime.datetime.strptime(date_str, "%Y-%B-%d")

    return date_day


def get_current_year(md_month: str) -> int:
    """
    Return the correct year.
    The year is either the current year or the next.
    It's the next only if we're setting events for
    after january 1st during the beggining of the current school year
    ie : today is 2019/09/31 and event is 2020/01/31

    @param md_month: (str)
    @return: (int)
    """
    now = datetime.datetime.now()
    current_year = now.year
    current_month = now.month
    if md_month in MONTHES_END_YEAR and current_month in range(8, 13):
        # is it before or after the end of civil year ?
        current_year += 1
    return current_year


def format_html(description: str) -> str:
    """
    format a string from markdown to html
    @param description: (str) mardkdown formated string
    @return: (str) equivalent string in html format
    """
    description_html = markdown.markdown(description)
    return description_html


def parse_hours(
    dt_key: datetime.datetime, hours: str
) -> tuple[dict[str, str], dict[str, str]]:
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
            'dateTime': '2019-08-09T15:00:00+02:00',
            'timeZone': 'Europe/Paris',
        }
    """
    hours = hours.strip("*").strip()
    hours_list = hours.split("-")

    start_str = hours_list[0]
    end_str = hours_list[1]

    start_hour, start_minute = get_hours_minute(start_str)
    end_hour, end_minute = get_hours_minute(end_str)

    year = dt_key.year
    month = dt_key.month
    day = dt_key.day

    start_dt = datetime.datetime(year, month, day, start_hour, start_minute)
    end_dt = datetime.datetime(year, month, day, end_hour, end_minute)

    start = {"dateTime": format_dt_for_event(start_dt), "timeZone": TIMEZONE}
    end = {"dateTime": format_dt_for_event(end_dt), "timeZone": TIMEZONE}

    return start, end


def get_hours_minute(time_str: str) -> tuple[int, int]:
    """
    Extract an hour a minute from a string
    we could use datetime.strptime but it's dirtier and quicker (to code)
    @param time_str: (str) french time format : 8h35
    @return: (tuple of int) (hour, minute) : (8, 35)
    """
    time_list = time_str.split("h")
    time_hour = int(time_list[0])
    time_minute = 0 if time_list[1] == "" else int(time_list[1])
    return time_hour, time_minute


def get_offset_at_given_date(time_of_event: datetime.datetime) -> int:
    """
    Get the offset (1 or 2 at a give date)

    During summer Europe/Paris is +2 hours offset from UTC
    During summer Europe/Paris is +1 hours offset from UTC

    @param time_of_event: (datetime)
    @return: (int)
    """
    cet = pytz.timezone("CET")
    offset_delta = cet.utcoffset(time_of_event)
    if offset_delta is not None:
        offset_hours = int(offset_delta.total_seconds() / 3600)
        return offset_hours
    return 0


def format_dt_for_event(time_of_event: datetime.datetime) -> str:
    """
    '2019-08-09T15:00:00+02:00'

    The date is correctly offseted (+1 or +2 according to offset)
    """

    offset = get_offset_at_given_date(time_of_event)
    time_format = f"%Y-%m-%dT%H:%M:00+0{offset}:00"
    return datetime.datetime.strftime(time_of_event, time_format)


def get_days_indexes(lines: list[str]) -> list[int]:
    """
    Returns the line number of line describing a day.

    @param lines: (list[str]) the lines of the .md file
    @return: (list[int]) list of line indexes
    """
    return [line_nr for line_nr, line in enumerate(lines) if line.startswith("## ")]


def split_day_lines(lines: list[str]) -> dict[datetime.datetime, list[str]]:
    """
    Returns a dict of date : lines

    @param lines: (list[str]) whole content of .md file
    @param days_index: (list[int]) line indexes of days
    @return: (dict[datetime, list[str]]) the pairs date, lines
    """
    days_index = get_days_indexes(lines)
    dict_day_lines = {}
    for i in range(len(days_index)):
        start = days_index[i]
        end = days_index[i + 1] if i + 1 < len(days_index) else len(lines)
        day_lines = lines[slice(start + 1, end)]
        dict_day_lines[parse_date(lines[start])] = day_lines
    return dict_day_lines


def parse_day_events(
    dict_day_lines: dict[datetime.datetime, list[str]],
) -> list[Event]:
    """
    Extract the events for a day.

    @param dict_day_lines: (dict[datetime.datetime, list[str]]) strings per day.
    @return: (list[event])
    """
    events = []
    for dt, lines in dict_day_lines.items():
        events.extend(read_day_events(dt, split_day_events(lines)))
    return events


def parse_location(summary_strings: list[str]) -> str:
    """
    Extract the location of the event.

    @param summary_strings: (list[str])
    @return: (str)
    """
    return summary_strings[1] if len(summary_strings) > 1 else ""


def parse_summary(summary_strings: list[str]) -> str:
    """
    Extract the summary for a list of strings.

    @param summary_strings: (list[str]) list of string for a summary.
        The first line should be blank
    @return: (str) joined summary, without the blank line.
    """
    if len(summary_strings) <= 2:
        return "%"
    return summary_strings[2]


def parse_color_id(summary: str) -> str:
    """
    Search for keywords in the description of the event.
    Return the color number (string) if something is found

    @param summary: (str) the description of the event
    @return: (str or None) the
    """
    summary = summary.lower()
    for nb, tags in STUDENT_CLASS_COLORS.items():
        for tag in tags:
            if tag.lower() in summary.lower():
                return nb
    return DEFAULT_COLOR


def parse_first_line(
    dt: datetime.datetime,
    summary_strings: list[str],
) -> dict[str, Union[str, dict[str, str]]]:
    """
    Parse the first line of a event string into a dict.
    @param dt:(datetime.datetime) event date
    @param summary_strings: (str) the first line :
        - 6h40-7h14 - gare - train
    @return: (dict[str, Union[str, dict[str, str]]])
    with keys:
    * start,
    * end,
    * location,
    * corlorId
    """

    start, end = parse_hours(dt, summary_strings[0])
    location = parse_location(summary_strings)
    summary = parse_summary(summary_strings)
    color_id = parse_color_id(summary)

    return {
        "start": start,
        "end": end,
        "location": location,
        "summary": summary,
        "colorId": color_id,
    }


def parse_description(lines: list[str]) -> str:
    """
    Extract a description from the list of strings, if any.
    @param lines: (list[str]) lines describing an event
    @return: (Optional[str]) the joined lines of the event.
    """
    return format_html("\n".join(line.strip() for line in lines[1:] if line.strip()))


def parse_event(
    dt: datetime.datetime,
    lines: list[str],
) -> Event:
    """
    Parse an event from its line and a date.
    @param dt:(datetime.datetime) the date of the event
    @param lines: (list[str]) lines of the event
    @return: (Event) Complete Event, ready to be pushed.
    """
    event_dict = parse_first_line(dt, lines[0].strip().split(" - "))
    description = parse_description(lines)
    if description is not None:
        event_dict["description"] = description

    return Event.from_dict(event_dict)


def read_day_events(
    dt: datetime.datetime,
    splitted_events: list[list[str]],
) -> list[Event]:
    """
    Returns a list of Event for that day.
    @param dt: (datetime.datetime) the day
    @param split_events: (list[list[str]) event for that day, per day event.
    @return: (list[Event]) the events of that day
    """
    return [parse_event(dt, lines) for lines in splitted_events if lines]


def split_day_events(lines: list[str]) -> list[list[str]]:
    """
    Split the list of lines per day into lines per event per day.
    @param lines: (list[str]) lines for a day
    @return: (list[list[str]]) list of string lines per event
    """
    pack = [[]]
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(MD_LI_TOKENS):
            pack.append([line[2:]])
        elif not line.startswith("\n"):
            pack[-1].append(line)
        index += 1
    return pack


def parse_events(
    path: str,
) -> list[Event]:
    """
    Extract all the events of a week, given by a md file
    see example_week_md_path file for a given format

    @param path: (str) path of the .md file
    @return : (list[Event]) all the events of a given week
    """
    return parse_day_events(split_day_lines(get_lines_from(path)))


if __name__ == "__main__":
    print(parse_color_id("2ND9"))
