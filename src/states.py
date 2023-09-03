from __future__ import annotations
import argparse

from dataclasses import dataclass
from typing import Union

from .colors import color_text
from .config import Agenda, CURRENT_YEAR, pick_agenda


@dataclass
class State:
    """
    Represents a state from a Finite State Machine.
    It has a name (str), can be initial (bool) or final (bool)
    """

    name: str
    initial: bool = False
    final: bool = False

    def __hash__(self) -> int:
        """Allows state to be dict keys."""
        return sum(map(ord, self.name))

    def __repr__(self) -> str:
        return self.name


class StateMachineError(Exception):
    """Raised when a transition between states is impossible."""

    pass


class StateMachine:
    """
    A Finite State Machine.
    It has a a current state (State) and transitions between states.
    One of those states should be "initial".
    """

    def __init__(self, transitions: dict[State, dict[str, State]]):
        self.__current: State
        self.__transitions = transitions
        self.__set_initial_state()

    def __set_initial_state(self) -> None:
        """
        Set the initial state of the machine.
        StateMachineError is raised if 0 or more than 1 states are "initial".
        """
        initial_states = [state for state in self.__transitions if state.initial]
        if len(initial_states) == 0:
            raise StateMachineError("There should be at least one initial state.")
        if len(initial_states) > 1:
            raise StateMachineError(
                "Too much initial states. There should be only one."
            )
        self.__current = initial_states[0]

    def next(self, event: str) -> None:
        """Change state from an action"""
        if self.__current.final:
            return
        if event in self.__transitions[self.__current]:
            self.__current = self.__transitions[self.__current][event]
        else:
            raise StateMachineError(
                f"Transition from {self.__current} with event {event} impossible."
            )

    @property
    def current(self) -> State:
        """
        The current state of the machine.
        @return: (State)
        """
        return self.__current

    def __repr__(self) -> str:
        return f"StateMachine with current state : {self.__current}"


class CalpyStates:
    """
    States of the application.
    It uses a StateMachine and a few parameters.
    """

    def __init__(self):
        # State of a finite state machine
        self.__ask_agenda = State("ask agenda", initial=True)
        self.__ask_period = State("ask period")
        self.__ask_week = State("ask week")
        self.__ask_display = State("ask display")
        self.__ask_confirmation = State("ask confirmation")
        self.__ready = State("ready", final=True)

        # Transitions
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
        # parameters for given states.
        self.__agenda: Union[Agenda, None] = None
        self.__period: Union[int, None] = None
        self.__period_path: Union[str, None] = None
        self.__weeks: Union[list[int], None] = None
        self.__path_list: Union[list[str], None] = None
        self.__display: Union[bool, None] = None
        self.__confirmation: Union[bool, None] = None

    @classmethod
    def from_arguments_and_config(
        cls, arguments: argparse.Namespace, agendas: list[Agenda]
    ) -> CalpyStates:
        """
        Creates an instance of CalpyStates from command line arguments.
        It may not be in an initial state.
        If the interactive argument is set to True, no other argument are read.

        @param arguments: (argparse.Namespace) given arguments as defined in `src.argument_parser`
        @param agendas: (list[Agenda]) a list of configured agendas as definied in `src.config`
        @return: (CalpyStates) a new state.
        """
        calpy_state = cls()
        if arguments.interactive:
            return calpy_state
        if arguments.agenda:
            calpy_state.agenda = pick_agenda(agendas, arguments.agenda)
        if arguments.period_number:
            calpy_state.period = arguments.period_number
        if arguments.week_numbers:
            calpy_state.weeks = arguments.week_numbers
        if arguments.view_content:
            calpy_state.display = True
        if arguments.yes:
            calpy_state.confirmation = True
        return calpy_state

    def __repr__(self) -> str:
        return repr(self.__transitions)

    @property
    def state(self) -> State:
        """
        Returns the current state.
        @return: (State)
        """
        return self.__transitions.current

    @property
    def agenda(self) -> Union[Agenda, None]:
        """
        Returns the set agenda.
        If no agenda is set, it will raise a `TypeError`
        """
        return self.__agenda

    @agenda.setter
    def agenda(self, agenda: Agenda) -> None:
        """
        Set the new agenda and move to the next state.
        Nothing is done if the state isn't "ask_agenda".
        The agenda should be a valid one.

        @param agenda: (Agenda) the new agenda.
        """
        if self.__transitions.current == self.__ask_agenda:
            self.__agenda = agenda
            self.__transitions.next("agenda")

    @property
    def period(self) -> Union[int, None]:
        """
        Returns the set period.

        @return: (int) the set period. It should be a valid one from config.
        """
        return self.__period

    @period.setter
    def period(self, period_number: int):
        """
        Set the new period and move to the next state.
        Nothing is done if the state isn't "ask_period".

        @param period_number: (int) the new period.
        """
        if self.__transitions.current == self.__ask_period:
            self.__period_path = self.__build_period_path(period_number)
            self.__period = period_number
            self.__transitions.next("period")

    def __build_period_path(self, period_number: int) -> str:
        """
        Creates the period path from the period number.

        @param period_number: (int)
        @retun: (str) a complete path to the period folder.
        """
        return f"{self.agenda.git_repo_path}{CURRENT_YEAR}/periode_{period_number}/"

    @property
    def period_path(self) -> str:
        """
        Returns the period path.
        Raise a TypeError if it isn't defined.

        @return: (str)
        """
        if self.__period_path is None:
            raise TypeError("period path isn't defined")
        return self.__period_path

    @property
    def weeks(self) -> Union[list[int], None]:
        """
        Returns the weeks.
        Raise a TypeError if it isn't defined.

        @return: (list[int])
        """
        return self.__weeks

    @weeks.setter
    def weeks(self, weeks: list[int]):
        """
        Set the new weeks.
        Nothing is done if the state isn't "ask_week".

        @param weeks: list[int]
        """
        if self.__transitions.current == self.__ask_week:
            self.__path_list = self.__convert_numbers_to_path(weeks)
            self.__weeks = weeks
            self.__transitions.next("week")

    def __convert_numbers_to_path(
        self,
        week_list: list[int],
    ) -> list[str]:
        """
        Convert the period number and week list into a valid path.
        If the user provided args with correspoding period and weeks, we read it from there.

        @param week_list: (list[int]) can be empty
        @return: (list[str]) the corresponding path
        """
        # we now have a complete path
        path_list = []
        for week_number in week_list:
            path = self.period_path + f"semaine_{week_number}.md"
            print(color_text(path + "\n", "YELLOW"))
            path_list.append(path)

        return path_list

    @property
    def path_list(self) -> list[str]:
        """
        Returns the path list.
        Raise a `TypeError` if the path_list isn't defined.

        @return: list[str]
        """
        if self.__path_list is None:
            raise TypeError("Path list isn't defined")
        return self.__path_list

    @property
    def display(self) -> Union[bool, None]:
        """
        Return the display attribute.
        Raise a `TypeError` if it isn't defined.

        @return: (bool)
        """
        return self.__display

    @display.setter
    def display(self, should_display: bool):
        """
        Set the new display attribute.
        Nothing is done if the state isn't `ask display`.

        @param should_display: (bool) should we display the .md content?
        """
        if self.__transitions.current == self.__ask_display:
            self.__display = should_display
            self.__transitions.next("display")

    @property
    def confirmation(self) -> Union[bool, None]:
        """
        Should we sync the .md content ?
        Raise a `TypeError` if the confirmation isn't defined.

        @return: (bool)
        """
        return self.__confirmation

    @confirmation.setter
    def confirmation(self, conf: bool):
        """
        Set the new confirmation attribute.
        Nothing is done if the state isn't `ask confirmation`.

        @param should_display: (bool) should we sync the .md content?
        """
        if not conf:
            self.__transitions.next("reset")
        if self.__transitions.current == self.__ask_confirmation:
            self.__confirmation = conf
            self.__transitions.next("confirmation")

    def reset(self) -> None:
        """
        Reset the CalpyStates machine.

        Every attribute is reset to None and the State is set to ask_agenda.
        """
        self.__agenda = None
        self.__period = None
        self.__period_path = None
        self.__weeks = None
        self.__path_list = None
        self.__display = None
        self.__confirmation = None

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
