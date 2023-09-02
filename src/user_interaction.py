from os import listdir
from os.path import isfile, join
from typing import Any, Union

import argparse
import sys

from .config import agendas, Agenda
from .states import CalpyStates, pick_agenda
from .config import CURRENT_YEAR, Agenda
from .colors import color_text

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
2. The .md file must be correctly formated or the application will crash

"""
GET_PERIOD_MSG = "Please choose a period in [1-5] : "
GET_WEEK_MSG = "Please choose a week in {} : "

MD_CONTENT_MSG = "This is the content of the .md file :\n"
INPUT_WARNING_MSG = """LAST WARNING !

Do you want to continue ?
Press (y) to continue, (n) to exit or another key to look for another file : """
QUICK_EXIT_MSG = "That's ok, exiting"

WRONG_PATH_MSG = """
Please provide a period number [1:5]
and a correct week number for that period
"""

# logs etc.
LOGFILE = "calendar_python.log"

PERIOD_LIST = range(1, 6)


def build_period_path(agenda_path: str) -> str:
    """
    Returns the formatable root path where 'periode' are stored.

    @param agenda_path: (str) where are files stored.
    @return: (str) formatable period path.
    """
    return f"{agenda_path}{CURRENT_YEAR}/" + "periode_{}/"


def build_default_path_md(period_path: str) -> str:
    """
    Returns the formatable week path.

    @param period_path: (str) formated root path where 'periode'
        are stored
    @return: (str) formatable week path where every week is
        stored
    """
    return period_path + "semaine_{}.md"


def extract_number_from_path(week_md_filename: str) -> int:
    """
    Extract the number from a week .md filename

    "semaine_36.md"   ----> 36
    "semaine_1.md"    ----> 1

    @param week_md_filename: (str) the name of the md file
    @return: (int)
    """
    return int(week_md_filename[:-3].split("_")[1])


def get_weeks_from_period(period_path: str) -> list[int]:
    """
    Get the week numbers from a given period path
    List all the week from path
    @param period_path: (str) the path to the period folder
    @return: (list of int) the list of the weeks in that period
    """
    week_dirs_list = (f for f in listdir(period_path) if isfile(join(period_path, f)))
    return sorted(list(map(extract_number_from_path, week_dirs_list)))


def display_md_content(path: str) -> None:
    """
    Print the content of the md file to the console.
    @param: (path) the path to the md file
    @return: (None)
    """
    with open(path, mode="r") as mdfile:
        print(MD_CONTENT_MSG)
        print(color_text(mdfile.read(), "BOLD"))


def ask_period() -> int:
    """
    Asks the user for a valid period number.
    Loops until the user gave a valid period number.
    @returns: (int) a period number from PERIOD_LIST
    """
    while True:
        period_str = input(color_text(GET_PERIOD_MSG, "CYAN"))
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
        inputed_weeks = input(color_text(GET_WEEK_MSG.format(valid_weeks), "CYAN"))
        try:
            week_list = list(map(int, inputed_weeks.split(" ")))
        except ValueError:
            continue
        if all(map(lambda week: week in valid_weeks, week_list)):
            return week_list


def update_state_from_inputs(calpy_states: CalpyStates):
    """
    Warn the user about what's he's going to do and return the paths provided
    by the user.
    If no path is provided in the args, keep asking the user for a new one.

    @param: (argparse.Namespace) provided args
    @return: (list[str]) the path to the md file
    """
    print(color_text(WELCOME_MSG, "DARKCYAN"))
    print(color_text(color_text(BANNER, "DARKCYAN"), "BOLD"))

    while not calpy_states.confirmation:
        if calpy_states.agenda is None:
            calpy_states.agenda = ask_agenda()

        print(color_text(f"Chosen agenda {calpy_states.agenda.longname}", "YELLOW"))

        if calpy_states.period is None:
            calpy_states.period = ask_period()

        print(color_text(f"Chosen period {calpy_states.period}", "YELLOW"))

        if calpy_states.weeks is None:
            calpy_states.weeks = ask_user_week(calpy_states.period_path)
        print(color_text(f"Chosen weeks {calpy_states.weeks}", "YELLOW"))
        print_paths(calpy_states.path_list)

        if calpy_states.display is None:
            calpy_states.display = ask_for_display()
        print(color_text(f"Display content ? {calpy_states.display}", "YELLOW"))

        if calpy_states.display:
            for path in calpy_states.path_list:
                display_md_content(path)

        if calpy_states.confirmation is None:
            confirmation = ask_for_confirmation()
            print(color_text(f"Sync ? {confirmation}", "YELLOW"))
            calpy_states.confirmation = confirmation

        if not calpy_states.confirmation:
            calpy_states.reset()


def ask_agenda() -> Agenda:
    agenda_names = [agenda.longname for agenda in agendas]
    input_agenda = ""
    while input_agenda not in agenda_names:
        input_agenda = input(
            color_text(f"Quel agenda choisir parmi {agenda_names} ? ", "CYAN")
        )
    return pick_agenda(agendas, input_agenda)


def ask_for_display() -> bool:
    return input(color_text("Afficher le contenu ? [y/n] ", "CYAN")) in ["y", "Y"]


def ask_for_confirmation() -> bool:
    return input(color_text("Voulez vous synchroniser ? [y/n] ", "CYAN")) in ["y", "Y"]


def print_paths(path_list: list[str]) -> None:
    """
    Prints every path in pathlist
    @param path_list: (list[str]) a list of valid paths
    @returns: (None)
    """
    for path in path_list:
        print(color_text(path, "YELLOW"))
