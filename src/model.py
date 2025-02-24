from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date

import caldav
from pytz import timezone


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
    description_raw: str
    colorId: str
    htmlLink: str
    is_all_day: bool

    @classmethod
    def from_dict(cls, event_dict: dict) -> Event:
        """
        Creates an Event from a dict.
        Raise AssertionError if some values types aren't correct.
        """
        is_all_day = "dateTime" not in event_dict["start"]
        event = cls(
            id=event_dict.get("id", ""),
            start=event_dict["start"],
            end=event_dict["end"],
            location=event_dict.get("location", ""),
            summary=event_dict["summary"],
            description=event_dict.get("description", ""),
            description_raw=event_dict.get("description_raw", ""),
            colorId=event_dict.get("colorId", "11"),
            htmlLink=event_dict.get("htmlLink", ""),
            is_all_day=is_all_day,
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
        assert isinstance(event.description_raw, str)
        assert isinstance(event.colorId, str)

    def is_equal(self, event: Event) -> bool:
        """
        Compare two events.
        They are equal if they share the same :
            - start,
            - end,
            - location,
            - summary,
            - description,
            - colorId

        Comparison used in google calendar only.
        The description is html formated while "description_raw" isn't.
        Google Calendar supports html in its description while Nextcloud doesn't
        """
        return (
            self.start == event.start
            and self.end == event.end
            and self.location == event.location
            and self.summary == event.summary
            and self.description == event.description
            and self.colorId == event.colorId
        )

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

    def readable_start_date(self) -> str:
        """
        Transform a dict describing the start time event into a readable string.
        * all day event have a "date" key wich is already readable. We right pad it
            for alignement.
        * timed event have a "dateTime" which is isoformated, we format it like :
            "2022-12-31 23:59"
        """
        if self.is_all_day:
            return self.start["date"] + " " * 8
        else:
            return datetime.fromisoformat(self.start["dateTime"]).strftime(
                "%Y-%m-%d - %H:%M"
            )

    def __eq__(self, other: Event) -> bool:
        return self.summary == other.summary

    def nextcloud_dates(self) -> tuple[datetime | date, datetime | date]:
        tz = timezone("Europe/Paris")

        if self.is_all_day:
            newdtstart = date.fromisoformat(self.start["date"])
            newdtend = date.fromisoformat(self.end["date"])
        else:
            # fmt: off
            newdtstart = datetime.fromisoformat(self.start["dateTime"]).astimezone(tz)
            newdtend = datetime.fromisoformat(self.end["dateTime"]).astimezone(tz)
            # fmt: on
        return newdtstart, newdtend

    def is_equal_nextcloud(self, other: caldav.Event) -> bool:
        """
        Compares a Calpy Event to a caldav.Event.

        If they share every detail, they are equal.

        Compared details:
        - start
        - end
        - summary
        - description vs description_raw (not html formatted)
        - location

        @param other: (caldav.Event)
        @return: (bool)
        """
        vevent = other.icalendar_component
        if not vevent:
            return False

        otherstart = vevent.get("DTSTART").dt
        otherend = vevent.get("DTEND").dt
        summary = vevent.get("SUMMARY", "%")
        summary = summary.to_ical().decode() if summary else summary
        description = vevent.get("DESCRIPTION", "")
        description = description.to_ical().decode() if description else description
        location = vevent.get("LOCATION", "")
        location = location.to_ical().decode() if location else location

        selfstart, selfend = self.nextcloud_dates()
        return (
            otherstart == selfstart
            and otherend == selfend
            and summary == self.summary
            and description == self.description_raw
            and location == self.location
        )
