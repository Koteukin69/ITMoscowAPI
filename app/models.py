from typing import List, Optional

from pydantic import BaseModel


class Building(BaseModel):
    name: str
    key: str


class GroupItem(BaseModel):
    name: str
    building: str  # building key
    key: str       # URL-encoded group name


class GroupsFilterRequest(BaseModel):
    building: Optional[str] = None
    key: Optional[str] = None


class Lesson(BaseModel):
    number: int
    time: str
    subject: str
    teacher: str
    room: str


class Replacement(BaseModel):
    number: int
    subject: str
    teacher: str
    room: str


class Schedule(BaseModel):
    weekday: str
    lessons: List[Lesson]


class ScheduleDayRequest(BaseModel):
    group: str       # group name
    building: str    # building key
    weekday: int     # 0=Mon … 5=Sat
    replacements: bool = False
