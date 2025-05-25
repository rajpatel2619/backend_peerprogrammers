import enum
from enum import Enum
from datetime import date, time
from pydantic import BaseModel, Field



class CourseMode(enum.Enum):
    live = "Live"
    offline = "Offline"
    recorded = "Recorded"
    hybrid = "Hybrid"

class CourseModeEnum(str, Enum):
    live = "Live"
    offline = "Offline"
    recorded = "Recorded"
    hybrid = "Hybrid"

class CourseCreate(BaseModel):
    title: str
    description: str 
    mode: CourseModeEnum
    creator_ids: list[int]  # Accept multiple creators

class CourseDetailsUpdate(BaseModel):
    syllabus_summary: str
    syllabus_path: str
    venue: str
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    duration_in_hours: int
    title: str
    description: str
