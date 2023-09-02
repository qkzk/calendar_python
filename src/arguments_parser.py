"""
title: parser of command line arguments
"""

import argparse


def read_arguments() -> argparse.Namespace:
    """
    Returns a parser of arguments.

    -i, --interactive: interactive mode. The user types the period and week numbers.
        The user can also review the content.
    -v, -- view_content: display the markdown content
    -y, --yes: Don't ask confirmation
    [period_number]: (int) between 1 and 5
    [week_numbers]: ([int]) corresponding week numbers. Must belong to that period
    """
    parser = argparse.ArgumentParser(
        description="""Synchronise your markdown calendars with Google Calendar."""
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
        action="store_false",
    )

    parser.add_argument(
        "-y",
        "--yes",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-a",
        "--agenda",
        default="quentin",
        type=str,
    )

    arguments = parser.parse_args()
    print(arguments)

    return arguments


def test():
    arguments = read_arguments()
    print(arguments)


if __name__ == "__main__":
    test()
