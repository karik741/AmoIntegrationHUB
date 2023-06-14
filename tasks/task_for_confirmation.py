from datetime import datetime, timedelta

from amocrm.v2 import Task
from time_helpers import time_for_amo
from entity_helpers.contact_search import find_contact_by_docrm_data
from config import Config


def create_and_save_task(lesson, contact_id):
    lesson_time = time_for_amo(lesson['lessonStart'])
    contact = find_contact_by_docrm_data(contact_id[9:], '')
    task = Task()
    task.entity_id = contact.id
    task.entity_type = "contacts"
    task.task_type_id = Config.task_type_confirmation
    task.responsible_user = Config.user_admin_id
    task.complete_till = time_for_task(lesson_time)
    task.text = f'Записан на {"индивидуальный" if lesson["isIndividual"] else "групповой"} урок ' \
                f'{datetime.utcfromtimestamp(lesson_time).strftime("%d.%m.%Y %H:%M")}, ' \
                f'{lesson["subject"]}, педагог {lesson["teacher"]}. Подтвердить посещение.'
    task.save()


def time_for_task(lesson_time):
    day_before = datetime.utcfromtimestamp(lesson_time) - timedelta(days=1)
    return day_before.replace(hour=12, minute=0, second=0, microsecond=0)