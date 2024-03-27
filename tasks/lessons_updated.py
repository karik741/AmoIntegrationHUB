from typing import TypedDict, List

from time_helpers import Instant
from entity_helpers.enums import ProgramType
from config import Config
from worker import create_and_save_task_task

class CustomerData(TypedDict):
    customerId: str
    phoneNumber: str


class Lessons(TypedDict):
    programType: int
    subject: str
    lessonId: str
    auditory: str
    teacher: str
    lessonStart: Instant
    lessonEnd: Instant
    programName: str
    durationInMinutes: int
    isIndividual: bool
    customers: List[CustomerData]


class LessonsData(TypedDict):
    lessons: List[Lessons]


def on_lessons_updated(lessons_data: LessonsData):
    if Config.use_confirmation_tasks:
        for lesson in lessons_data['lessons']:
            if lesson['programType'] == ProgramType.paid:
                for customer_data in lesson['customers']:
                    create_and_save_task_task.delay(lesson, customer_data['phoneNumber'])

