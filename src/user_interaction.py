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
INPUT_PRINT_MD_FILE = "Do you want to see the content of the file (y/N) ? "

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


def get_md_path_from_args_or_user(
    root_path: str,
    arguments: argparse.Namespace,
    reset_path=False,
) -> tuple[Union[str, Any], list[Union[int, Any]]]:
    """
    Create the path from the args and ask the user what he wants to do.

    @param root_path: (str) formatable path where periods are stored.
    @param reset_path: (bool) do we have to reset the path ?
    @return: tuple[Union(str, Any), list[Union[int, Any]]] a pair with period number (1-5) and corresponding weeks
    """
    print(color_text(WARNING_MSG, "DARKCYAN"))

    if reset_path or len(sys.argv) == 1:
        # no parameters were given by the user
        mode = "Interactive"
        period_number = ask_user_period()
        period_path = build_period_path(root_path).format(period_number)
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


def convert_week_numbers(week_numbers: list[str]) -> list[int]:
    """
    Casts the week numbers into a list of integers
    ["1", "2", "3"] -> [1, 2, 3]
    @param week_numbers: (str) a string containing the week numbers
    @return: (list[int]) the list of casted strings into integers
    """
    print("convert_week_numbers - week_numbers", week_numbers)
    return list(map(int, week_numbers))


def warn_and_get_path(calpy_states: CalpyStates):
    """
    Warn the user about what's he's going to do and return the paths provided
    by the user.
    If no path is provided in the args, keep asking the user for a new one.

    @param: (argparse.Namespace) provided args
    @return: (list[str]) the path to the md file
    """
    print(color_text(WELCOME_MSG, "DARKCYAN"))
    print(color_text(color_text(BANNER, "DARKCYAN"), "BOLD"))
    print(calpy_states)

    while not calpy_states.confirmation:
        if calpy_states.agenda is None:
            calpy_states.agenda = ask_agenda()
        print("after agenda", calpy_states)

        if calpy_states.period is None:
            calpy_states.period = ask_user_period()
        print("after period", calpy_states)

        if calpy_states.weeks is None:
            calpy_states.weeks = ask_user_week(calpy_states.period_path)

        if calpy_states.display is None:
            calpy_states.display = ask_for_display()

        print("calpy_states.display", calpy_states.display)
        if calpy_states.display:
            for path in calpy_states.path_list:
                display_md_content(path)

        if calpy_states.confirmation is None:
            calpy_states.confirmation = ask_for_confirmation()
            if not calpy_states.confirmation:
                calpy_states.reset()


def ask_agenda() -> Agenda:
    agenda_names = [agenda.longname for agenda in agendas]
    input_agenda = ""
    while input_agenda not in agenda_names:
        input_agenda = input(f"Quel agenda choisir parmi {agenda_names} ? ")
    return pick_agenda(agendas, input_agenda)


def ask_for_display() -> bool:
    return input("Afficher le contenu ? [y/n] ") in ["y", "Y"]


def ask_for_confirmation() -> bool:
    return input("Voulez vous synchroniser ? [y/n] ") in ["y", "Y"]


def interactive_mode(
    root_path: str,
    path_list: list[str],
    reset_path: bool,
    input_warning: str,
    arguments: argparse.Namespace,
) -> list[str]:
    """
    Used when no path could be read from arguments.

    @param root_path: (str) the root folder containing the subfolder for this agenda
    @param path_list: (list[str]) provided path list. Could be empty.
    @param reset_path: (bool) should we reset this path ?
    @param arguments: (argparse.Namespace) provided args
    @return: (list[str]) the paths
    """
    while user_provides_invalid_input(path_list, input_warning):
        period_number, week_list = get_md_path_from_args_or_user(
            root_path, arguments, reset_path=reset_path
        )
        period_path = build_period_path(root_path)
        default_path_md = build_default_path_md(period_path)
        path_list = convert_numbers_to_path(
            default_path_md,
            week_list,
        )
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
    @returns: (bool) True if the path couldn't be figured or the user typed no.
    """
    return not path_list or input_warning != "y"
