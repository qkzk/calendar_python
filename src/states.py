from __future__ import annotations
import argparse

from dataclasses import dataclass
from typing import Union

from src.colors import color_text


from .config import Agenda, default_agenda, CURRENT_YEAR


def pick_agenda(agendas: list[Agenda], agenda_name_from_args: str) -> Agenda:
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


@dataclass
class State:
    name: str
    initial: bool = False
    final: bool = False

    def __hash__(self) -> int:
        return sum(map(ord, self.name))

    def __repr__(self) -> str:
        return self.name


class StateMachineError(Exception):
    pass


class StateMachine:
    def __init__(self, transitions: dict[State, dict[str, State]]):
        self.__current: State
        self.__transitions = transitions
        self.set_initial_state()

    def set_initial_state(self) -> None:
        initial_states = [state for state in self.__transitions if state.initial]
        if len(initial_states) == 0:
            raise StateMachineError("There should be at least one initial state.")
        if len(initial_states) > 1:
            raise StateMachineError(
                "Too much initial states. There should be only one."
            )
        self.__current = initial_states[0]

    def next(self, param: str) -> None:
        print(f"Event: {param} - current state: {self.current}", end="")
        if self.__current.final:
            print()
            return
        if param in self.__transitions[self.__current]:
            self.__current = self.__transitions[self.__current][param]
            print(f" - next state: {self.current}")
        else:
            print()

    @property
    def current(self) -> State:
        return self.__current

    @current.setter
    def current(self, next) -> None:
        self.__current = next

    def __repr__(self) -> str:
        return f"StateMachine with current state : {self.__current}"


class CalpyStates:
    def __init__(self):
        self.__ask_agenda = State("ask agenda", initial=True)
        self.__ask_period = State("ask period")
        self.__ask_week = State("ask week")
        self.__ask_display = State("ask display")
        self.__ask_confirmation = State("ask confirmation")
        self.__ready = State("ready", final=True)

        self.__attributes: dict = {}

        self.__transitions = StateMachine(
            {
                self.__ask_agenda: {
                    "agenda": self.__ask_period,
                    "reset": self.__ask_agenda,
                },
                self.__ask_period: {
                    "period": self.__ask_week,
                    "reset": self.__ask_agenda,
                },
                self.__ask_week: {
                    "week": self.__ask_display,
                    "reset": self.__ask_agenda,
                },
                self.__ask_display: {
                    "display": self.__ask_confirmation,
                    "reset": self.__ask_agenda,
                },
                self.__ask_confirmation: {
                    "confirmation": self.__ready,
                    "reset": self.__ask_agenda,
                },
            }
        )
        self.__agenda: Union[Agenda, None] = None
        self.__period: Union[int, None] = None
        self.__weeks: Union[list[int], None] = None
        self.__display: Union[bool, None] = None
        self.__confirmation: Union[bool, None] = None

    @classmethod
    def from_arguments_and_config(
        cls, arguments: argparse.Namespace, agendas: list[Agenda]
    ) -> CalpyStates:
        state = cls()
        if arguments.interactive:
            return state
        if arguments.agenda:
            state.agenda = pick_agenda(agendas, arguments.agenda)
        if arguments.period_number:
            state.period = arguments.period_number
        if arguments.week_numbers:
            state.weeks = arguments.week_numbers
            print("weeks", state.weeks)
        if arguments.view_content:
            state.display = True
        if arguments.yes:
            state.confirmation = True
        return state

    def __repr__(self) -> str:
        return repr(self.__transitions)

    @property
    def state(self) -> State:
        return self.__transitions.current

    @property
    def agenda(self):
        return self.__agenda

    @agenda.setter
    def agenda(self, agenda: Agenda):
        if self.__transitions.current == self.__ask_agenda:
            self.__agenda = agenda
            self.__transitions.next("agenda")

    @property
    def period(self):
        return self.__period

    @period.setter
    def period(self, period_number: int):
        if self.__transitions.current == self.__ask_period:
            self.__attributes["period_path"] = self.__build_period_path(period_number)
            self.__period = period_number
            self.__transitions.next("period")

    def __build_period_path(self, period_number: int) -> str:
        return f"{self.__agenda.git_repo_path}{CURRENT_YEAR}/periode_{period_number}/"

    @property
    def period_path(self) -> str:
        return self.__attributes["period_path"]

    @property
    def weeks(self):
        return self.__weeks

    @weeks.setter
    def weeks(self, weeks: list[int]):
        if self.__transitions.current == self.__ask_week:
            self.__attributes["path_list"] = self.__convert_numbers_to_path(weeks)
            self.__weeks = weeks
            self.__transitions.next("week")

    def __convert_numbers_to_path(
        self,
        week_list: list[int],
    ) -> list[str]:
        """
        Convert the period number and week list into a valid path.
        If the user provided args with correspoding period and weeks, we read it from there.

        @param default_path_md: (str) Path with 2 formatable arguments.
        @param period_number: (str) Castable into int 1, ..., 5
        @param week_list: (list[int]) can be empty
        @param arguments: (argparse.Namespace) provided args
        @return: (list[str]) the corresponding path
        """
        # we now have a complete path
        path_list = []
        print(week_list)
        for week_number in week_list:
            path = self.__attributes["period_path"] + f"semaine_{week_number}.md"
            print(color_text(path + "\n", "YELLOW"))
            path_list.append(path)

        return path_list

    @property
    def path_list(self) -> list[str]:
        return self.__attributes["path_list"]

    @property
    def display(self):
        return self.__display

    @display.setter
    def display(self, should_display: bool):
        if self.__transitions.current == self.__ask_display:
            self.__display = should_display
            self.__transitions.next("display")

    def should_display(self) -> bool:
        return self.__display is True

    @property
    def confirmation(self):
        return self.__confirmation

    @confirmation.setter
    def confirmation(self, conf: bool):
        if not conf:
            self.__transitions.next("reset")
        if self.__transitions.current == self.__ask_confirmation:
            self.__confirmation = conf
            self.__transitions.next("confirmation")

    def reset(self) -> None:
        self.__agenda = None
        self.__period = None
        self.__weeks = None
        self.__display = None
        self.__confirmation = None

        self.__attributes = {}
        self.__transitions.next("reset")


def test_greenlight():
    g = State("green", initial=True)
    y = State("yellow")
    r = State("red", final=True)
    transitions = StateMachine(
        {
            g: {"go": y},
            y: {"go": r},
            r: {"go": g},
        },
    )
    print(transitions.current)
    transitions.next("go")
    print(transitions.current)
    transitions.next("go")
    print(transitions.current)
    transitions.next("go")
    print(transitions.current)
    transitions.next("go")


def test_calpy():
    ask_period = State("ask period", initial=True)
    ask_week = State("ask week")
    ask_display = State("ask display")
    ask_confirmation = State("ask confirmation")
    ready = State("ready", final=True)

    calpy_state_machine = StateMachine(
        {
            ask_period: {"period": ask_week},
            ask_week: {"week": ask_display},
            ask_display: {"display": ask_confirmation},
            ask_confirmation: {
                "reset": ask_period,
                "confirmation": ready,
            },
        }
    )
    calpy_state_machine.next("period")
    calpy_state_machine.next("week")
    calpy_state_machine.next("display")
    calpy_state_machine.next("reset")
    calpy_state_machine.next("period")
    calpy_state_machine.next("week")
    calpy_state_machine.next("display")
    calpy_state_machine.next("confirmation")


def test_calpy_state_machine():
    agenda = Agenda("quentin", "q", "1", "path", "1", True)
    calpy = CalpyStates()
    print(calpy.state)
    calpy.agenda = agenda
    print(calpy.state)
    calpy.period = 1
    print(calpy.state)
    calpy.weeks = [35, 36]
    print(calpy.state)
    calpy.display = False
    print(calpy.state)
    calpy.confirmation = False
    print(calpy.state)
    calpy.agenda = agenda
    print(calpy.state)
    calpy.period = 1
    print(calpy.state)
    calpy.weeks = [35, 36]
    print(calpy.state)
    calpy.display = False
    print(calpy.state)
    calpy.confirmation = True
    print(calpy.state)


if __name__ == "__main__":
    # test_greenlight()
    # test_calpy()
    test_calpy_state_machine()
