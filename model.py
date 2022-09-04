from dataclasses import dataclass
import datetime


@dataclass
class Event:
    start: datetime.datetime
    end: datetime.datetime
    location: str
    summary: str
    description: str
    colorId: str
