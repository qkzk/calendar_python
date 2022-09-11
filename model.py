from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Event:
    """
    Holds usefull infos about google calendar Events
    each event has the attributes :
    * 'start':datetime,
    * 'end':datetime,
    * 'location':str
    * 'summary':str ('%' if no summary were given)
    * 'description':str (possibly empty or multiline)
    * 'colorId':str ('1' to '11')

    """

    id: str
    start: dict[str, str]
    end: dict[str, str]
    location: str
    summary: str
    description: str
    colorId: str
    htmlLink: str

    @classmethod
    def from_dict(cls, event_dict: dict) -> Event:
        """
        Creates an Event from a dict.
        Raise AssertionError if some values types aren't correct.
        """
        event = cls(
            id=event_dict.get("id", ""),
            start=event_dict["start"],
            end=event_dict["end"],
            location=event_dict.get("location", ""),
            summary=event_dict["summary"],
            description=event_dict.get("description", ""),
            colorId=event_dict.get("colorId", "11"),
            htmlLink=event_dict.get("htmlLink", ""),
        )
        cls.raise_if_invalid(event)
        return event

    @staticmethod
    def raise_if_invalid(event: Event):
        """Raise assertion error if some values don't have correct type"""
        assert isinstance(event.start, dict)
        assert isinstance(event.end, dict)
        assert isinstance(event.location, str)
        assert isinstance(event.summary, str)
        assert isinstance(event.description, str)
        assert isinstance(event.colorId, str)

    def update(self, event: Event) -> None:
        """
        Update values from new event.
        Keeps the id and htmlLink untouched.
        """
        self.start = event.start
        self.end = event.end
        self.location = event.location
        self.summary = event.summary
        self.description = event.description
        self.colorId = event.colorId
