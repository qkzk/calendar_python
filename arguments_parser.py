"""
title: reads and parse command line arguments
"""

import argparse


def read_arguments():
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

    arguments = parser.parse_args()

    return arguments


def test():
    arguments = read_arguments()
    print(arguments)


if __name__ == "__main__":
    test()
