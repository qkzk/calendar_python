"""
    ask_period = State(initial=True)
    ask_week = State()
    ask_display = State()
    ask_confirmation = State()
    ready = State(final=True, exit=True)

    sync = (
        ask_period.to(ask_week)
        | ask_week.to(ask_display)
        | ask_display.to(ask_confirmation)
        | ask_confirmation.to(ready)
        | ask_confirmation.to(ask_period)
    )

    def before_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"
"""
from dataclasses import dataclass
from typing import Any, Union


@dataclass
class State:
    name: str
    initial: bool = False
    final: bool = False
    attributes: Union[None, dict[str, Any]] = None

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


class CalpyStates:
    def __init__(self):
        self.__ask_agenda = State("ask agenda", initial=True)
        self.__ask_period = State("ask period")
        self.__ask_week = State("ask week")
        self.__ask_display = State("ask display")
        self.__ask_confirmation = State("ask confirmation")
        self.__ready = State("ready", final=True)

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
        self.__agenda: Union[str, None] = None
        self.__period: Union[int, None] = None
        self.__weeks: Union[list[int], None] = None
        self.__display: bool = False
        self.__confirmation: bool = False

    @property
    def state(self) -> State:
        return self.__transitions.current

    @property
    def agenda(self):
        return self.__agenda

    @agenda.setter
    def agenda(self, agenda: str):
        if self.__transitions.current == self.__ask_agenda:
            self.__agenda = agenda
            self.__transitions.next("agenda")

    @property
    def period(self):
        return self.__period

    @period.setter
    def period(self, per: int):
        if self.__transitions.current == self.__ask_period:
            self.__period = per
            self.__transitions.next("period")

    @property
    def weeks(self):
        return self.__weeks

    @weeks.setter
    def weeks(self, wk: list[int]):
        if self.__transitions.current == self.__ask_week:
            self.__weeks = wk
            self.__transitions.next("week")

    @property
    def display(self):
        return self.__display

    @display.setter
    def display(self, dp: bool):
        if self.__transitions.current == self.__ask_display:
            self.__display = dp
            self.__transitions.next("display")

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
    calpy = CalpyStates()
    print(calpy.state)
    calpy.agenda = "quentin"
    print(calpy.state)
    calpy.period = 1
    print(calpy.state)
    calpy.weeks = [35, 36]
    print(calpy.state)
    calpy.display = False
    print(calpy.state)
    calpy.confirmation = False
    print(calpy.state)
    calpy.agenda = "quentin"
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
