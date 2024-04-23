"""
Example of valid format

Valid format:

filename : $AGENDAPATH/periode_1/semaine_44.md
filecontent:

# Semaine 44 - du lundi 30 octobre au dimanche 05 novembre

- location - content. Next is date of end - Vendredi 3 Novembre

## lundi 30 octobre

- 10h-11h - home - gardening

## mardi 31 octobre

- 7h-8h - city - doctor
...
"""

import argparse


def read_arguments() -> argparse.Namespace:
    """
    Returns a parser of arguments.

    -i, --interactive: interactive mode. The user types the period and week numbers.
        The user can also review the content.
    -v, -- view_content: display the markdown content
    -y, --yes: Don't ask confirmation
    -h, --help: Print a valid example of content
    -a, --agenda: a valid and configured agenda
    [period_number]: (int) between 1 and 5
    [week_numbers]: ([int]) corresponding week numbers. Must belong to that period
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Synchronise your markdown calendars with Google Calendar.""",
        epilog=__doc__,
        usage="calpy -a q 1 35 36 -y",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i", "--interactive", help="interactive mode", action="store_true"
    )
    weeks = group.add_argument_group()

    weeks.add_argument(
        "period_number",
        help="A period number, between 1 and 5",
        type=int,
        nargs="?",
    )

    weeks.add_argument(
        "week_numbers",
        help="A list of week numbers from that period",
        nargs="*",
        type=int,
    )

    parser.add_argument(
        "-v",
        "--view_content",
        default=True,
        help="display the content of .md file",
        action="store_false",
    )

    parser.add_argument(
        "-y",
        "--yes",
        default=False,
        help="Don't ask confirmation",
        action="store_true",
    )

    parser.add_argument(
        "-a",
        "--agenda",
        default="quentin",
        help="A valid and configured agenda name -- default to 'quentin'",
        type=str,
    )

    arguments = parser.parse_args()

    return arguments


def test():
    arguments = read_arguments()
    print(arguments)


if __name__ == "__main__":
    test()
