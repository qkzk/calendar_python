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
from os.path import exists

from googleapiclient.discovery import Resource

from src.config import agendas, default_agenda, Agenda

from .arguments_parser import read_arguments
from .colors import color_text
from .google_interaction import build_service, sync_event_from_md
from .logger import logger
from .user_interaction import warn_and_get_path, WRONG_PATH_MSG

STARTING_APPLICATION_MSG = "Calendar Python started !"
EXPLORING_MSG = """
Starting to explore the given week... please wait...

"""
CONFIRMATION_MSG = """
DONE ADDING THE EVENTS TO GOOGLE CALENDAR !

"""

SELECTED_AGENDA_MSG = """
YOU PICKED THE AGENDA : {}
"""


def pick_agenda(agenda_name_from_args: str) -> Agenda:
    """
    Returns the selected agenda from command line arguments.

    @param agenda_name_from_args: (str) the parsed name from command line arguments.
        It may be a short or longname.
    """
    for agenda in agendas:
        if (
            agenda.longname == agenda_name_from_args
            or agenda.shortname == agenda_name_from_args
        ):
            return agenda
    return default_agenda


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
    print(color_text(STARTING_APPLICATION_MSG, "DARKCYAN"))
    logger.warning(STARTING_APPLICATION_MSG)

    arguments = read_arguments()

    # select the correct agenda and print it
    agenda = pick_agenda(arguments.agenda)
    print(color_text(SELECTED_AGENDA_MSG.format(agenda.longname), "YELLOW"))

    # get the path from the user, provided as args or not.
    path_list = warn_and_get_path(arguments, agenda)
    # if isn't exited yet, we continue.

    service: Resource = build_service(agenda)

    for path in path_list:
        if not exists(path):
            logger.debug("File not found : {}".format(path))
            raise FileNotFoundError(
                f"""File not found : {path}
{WRONG_PATH_MSG}"""
            )

        print(EXPLORING_MSG)
        sync_event_from_md(agenda, service, path)
        print(color_text(CONFIRMATION_MSG, "DARKCYAN"))


if __name__ == "__main__":
    create_or_update_week_events()
