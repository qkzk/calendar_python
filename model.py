from __future__ import annotations
from dataclasses import dataclass
from typing import Union


@dataclass
class Event:
    start: dict[str, str]
    end: dict[str, str]
    location: str
    summary: str
    description: str
    colorId: str

    @classmethod
    def from_dict(cls, event_dict: dict) -> Event:
        event = cls(
            start=event_dict["start"],
            end=event_dict["end"],
            location=event_dict["location"],
            summary=event_dict["summary"],
            description=event_dict["description"],
            colorId=event_dict["colorId"],
        )
        cls.raise_if_invalid(event)
        return event

    @staticmethod
    def raise_if_invalid(event: Event):
        assert isinstance(event.start, dict)
        assert isinstance(event.end, dict)
        assert isinstance(event.location, str)
        assert isinstance(event.summary, str)
        assert isinstance(event.description, str)
        assert isinstance(event.colorId, str)

    def into_dict(self) -> dict[str, Union[str, dict[str, str]]]:
        return {
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "summary": self.summary,
            "description": self.description,
            "colorId": self.colorId,
        }
