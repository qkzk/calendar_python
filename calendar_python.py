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
from os.path import isfile, join, exists
from typing import Any, Union

import argparse
import sys

from googleapiclient.discovery import Resource

from arguments_parser import read_arguments
from config import CURRENT_YEAR, GIT_COURS_REPO_PATH
from colors import color_text
from google_interaction import build_service, sync_event_from_md
from logger import logger

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

PERIOD_LIST = range(1, 6)
PERIOD_PATH = f"{GIT_COURS_REPO_PATH}{CURRENT_YEAR}/" + "periode_{}/"
DEFAULT_PATH_MD = PERIOD_PATH + "semaine_{}.md"


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
    arguments: argparse.Namespace,
    reset_path=False,
) -> tuple[Union[str, Any], list[Union[int, Any]]]:
    """
    Create the path from the args and ask the user what he wants to do.
    @param reset_path: (bool) do we have to reset the path ?
    @return: tuple[Union(str, Any), list[Union[int, Any]]] a pair with period number (1-5) and corresponding weeks
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
    """
    Convert the period number and week list into a valid path.
    If the user provided args with correspoding period and weeks, we read it from there.

    @param period_number: (str) Castable into int 1, ..., 5
    @param week_list: (list[int]) can be empty
    @param arguments: (argparse.Namespace) provided args
    @return: (list[str]) the corresponding path
    """
    # we now have a complete path
    path_list = []
    for week_number in week_list:
        path = DEFAULT_PATH_MD.format(period_number, week_number)
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
    Warn the user about what's he's going to do and return the paths provided
    by the user.
    If no path is provided in the args, keep asking the user for a new one.

    @param: (argparse.Namespace) provided args
    @return: (list[str]) the path to the md file
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
    """
    Used when no path could be read from arguments.

    @param path_list: list[str] provided path list. Could be empty.
    @param reset_path: (bool) should we reset this path ?
    @param arguments: (argparse.Namespace) provided args
    @return: (list[str]) the paths
    """
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
        if not exists(path):
            logger.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        service: Resource = build_service()
        sync_event_from_md(service, path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


if __name__ == "__main__":
    create_or_update_week_events()
