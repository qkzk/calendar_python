"""
title: config
author: qkzk
date: 2022/09/17

configuration file

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
from __future__ import annotations
from dataclasses import dataclass

import yaml

# What is the calendar id ?
CALENDAR_ID = "ja53enipie6bc0b7sdldvlf528@group.calendar.google.com"  # qu3nt1n
# CALENDAR_ID = 'u79g8ba5vo6d8qnt20vebrqp8k@group.calendar.google.com' # leclemenceau

# What is the current year ?
# school year, for 2022-2023 use 2022
CURRENT_YEAR = 2022

# Where are the .md files stored ?
GIT_COURS_REPO_PATH = "/home/quentin/gdrive/cours/git_cours/cours/"

# What is your timezone ?
TIMEZONE = "Europe/Paris"

# What colors do you want to use for specific content ?
# See documentation above
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

# What default color do you want ?
DEFAULT_COLOR = "11"


@dataclass
class Agenda:
    shortname: str
    longname: str
    calendar_id: str
    git_repo_path: str
    default_color: str
    default: bool = False

    @classmethod
    def from_yaml(cls, yaml_content: dict) -> Agenda:
        return cls(
            shortname=yaml_content["shortname"],
            longname=yaml_content["longname"],
            calendar_id=yaml_content["calendar_id"],
            git_repo_path=yaml_content["git_repo_path"],
            default_color=yaml_content["default_color"],
            default=yaml_content["default"],
        )


def read_config_file(config_path: str) -> list[Agenda]:
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_content = yaml.safe_load(config_file)
        print(config_content)
        return [Agenda.from_yaml(value) for value in config_content["agendas"].values()]


agendas = read_config_file("./config.yml")
DEFAULT_AGENDA = [agenda for agenda in agendas if agenda.default][0]
