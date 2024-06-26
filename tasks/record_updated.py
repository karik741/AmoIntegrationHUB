from datetime import datetime, timedelta
from typing import TypedDict, List
import typing

from amocrm.v2 import Task, User

import time
from config import Config
from entity_helpers.contact_search import find_contact_by_docrm_data, Contact
from entity_helpers.lead_custom_fields import Lead
from entity_helpers.enums import ProgramType, Actions, RecordStatus
from time_helpers import Instant, time_for_amo, unix_time


class QuestionsAnswers(TypedDict):
    question: str
    answer: str


class AmoRecordAction(TypedDict):
    employee: str | None
    action: Actions


class AmoRecord(TypedDict):
    lessonId: str
    numberInProgram: int
    auditory: str
    teacher: str | None
    lessonStart: Instant
    lessonEnd: Instant
    batchStart: Instant
    batchEnd: Instant
    programName: str
    durationInMinutes: int
    programLessonCount: int
    limitFrom: int
    limitTo: int
    isIndividual: bool
    visited: bool | None
    subscriptionId: str | None
    isPrimarySale: bool | None
    recordHistory: list[AmoRecordAction]
    questionsAnswers: List[QuestionsAnswers]


class RecordData(TypedDict):
    customerId: str
    branchId: str
    programType: ProgramType
    subject: str
    lessonUpdated: AmoRecord
    lastSimiliarLesson: AmoRecord | None
    remainedSubscriptionUnits: float
    isReviewUpdated: bool


def on_record_updated(record_data: RecordData):
    contact = find_contact_by_docrm_data(record_data['customerId'], 'non_existing_phone')
    lesson_time = time_for_amo(record_data['lessonUpdated']['lessonStart'])

    if record_data['isReviewUpdated']:
        send_review_process(record_data, contact, lesson_time)
    else:
        record_updated_process(record_data, contact, lesson_time)


def send_review_process(record_data: RecordData, contact: Contact, lesson_time):
    text_for_note = ''
    for review in record_data['lessonUpdated']['questionsAnswers']:
        text_for_note += f'Вопрос: {review["question"]}\n' \
                         f'Ответ: {review["answer"]}\n\n'
    contact.notes.objects.create(
        note_type='common',
        params={
            "text": f'Отчет педагога: {record_data["lessonUpdated"]["teacher"]}\n'
                    f'По уроку: {datetime.utcfromtimestamp(lesson_time).strftime("%d.%m.%Y %H:%M")} '
                    f'{record_data["subject"]}: {record_data["lessonUpdated"]["programName"]}\n\n'
                    f'{text_for_note}'
        }
    )


def record_updated_process(record_data: RecordData, contact: Contact, lesson_time):
    record_status_for_amo = record_status(record_data)
    leads = contact.primary_and_secondary_leads()

    if record_status_for_amo == RecordStatus.registered or record_status_for_amo == RecordStatus.restored:
        student_registered_on_lesson_process(record_data, contact, lesson_time, leads)

    if record_status_for_amo == RecordStatus.marked_regular:
        student_marked_regular_process(record_data, contact, lesson_time, leads)

    if (record_status_for_amo == RecordStatus.not_came_free_promo or
            record_status_for_amo == RecordStatus.came_free_promo):
        student_marked_free_promo_process(record_data, contact, lesson_time, leads, record_status_for_amo)

    if (record_status_for_amo == RecordStatus.not_came_paid_promo or
            record_status_for_amo == RecordStatus.came_paid_promo):
        student_marked_paid_promo_process(record_data, contact, lesson_time, leads, record_status_for_amo)

    if (record_status_for_amo == RecordStatus.cancelled_free_promo or
            record_status_for_amo == RecordStatus.cancelled_paid_promo or
            record_status_for_amo == RecordStatus.cancelled_regular):
        student_cancelled_process(record_data, contact, lesson_time, leads, record_status_for_amo)

    if record_status_for_amo == RecordStatus.came_event:
        student_came_event_process(lesson_time, leads, contact)


def student_registered_on_lesson_process(record_data: RecordData, contact: Contact, lesson_time, leads: List[Lead]):
    note_for_contact(contact, record_data, lesson_time)
    lead = choose_lead_for_record(leads, record_data)
    if lead is not None:
        is_secondary = record_data['programType'] == ProgramType.paid \
                       or record_data['lessonUpdated']['isPrimarySale'] is False
        lead.pipeline = Config.secondary_leads_pipeline_id if is_secondary else Config.primary_leads_pipeline_id
        lead.status = Config.lead_status_in_schedule_value_id \
            if is_secondary else Config.lead_status_recorded_to_promo_value_id
        lead.save()


def student_marked_regular_process(record_data: RecordData, contact: Contact, lesson_time, leads: List[Lead]):
    note_for_contact(contact, record_data, lesson_time)
    lead = choose_lead_by_subscription(leads, record_data)
    if record_data['remainedSubscriptionUnits'] > 0:
        if record_data['lastSimiliarLesson']['lessonId'] == record_data['lessonUpdated']['lessonId']:
            new_task = Task()
            new_task.entity_id = lead.id if lead is not None else contact.id
            new_task.entity_type = "leads" if lead is not None else "contacts"
            new_task.task_type_id = Config.task_type_register_new_value_id
            new_task.responsible_user = Config.user_admin_1_id
            new_task.complete_till = datetime.now()
            new_task.text = f'{"Посетил" if record_data["lessonUpdated"]["visited"] else "Пропустил"} ' \
                            f'{datetime.utcfromtimestamp(lesson_time).strftime("%d:%m:%Y %H:%M")} ' \
                            f'''{"индивидуальный" if record_data["lessonUpdated"]["isIndividual"]
                            else "групповой"} ''' \
                            f'{record_program_type(record_data)} по направлению: {record_data["subject"]}. ' \
                            f'Еще есть такие уроки в абонементах, но дальше не записан. Записать'
            new_task.save()
            if lead is not None:
                lead.status = Config.lead_status_needs_schedule_value_id
                lead.save()
    else:
        active_users = [typing.cast(User, user) for user in User.objects.all() if user.is_active]
        new_task = Task()
        new_task.entity_id = lead.id if lead is not None else contact.id
        new_task.entity_type = "leads" if lead is not None else "contacts"
        new_task.task_type_id = Config.task_type_renew_value_id
        new_task.responsible_user = active_user_id_or_default(Config.user_sales_person_id, active_users)
        new_task.complete_till = datetime.now()
        text_for_note = "Вторичных сделок несколько или вообще нет," \
                        " нужно выбрать подходящую или обратиться к руководителю."
        new_task.text = f'{"Посетил" if record_data["lessonUpdated"]["visited"] else "Пропустил"} ' \
                        f'{datetime.utcfromtimestamp(lesson_time).strftime("%d:%m:%Y %H:%M")} ' \
                        f'{"индивидуальный" if record_data["lessonUpdated"]["isIndividual"] else "групповой"} ' \
                        f'{record_program_type(record_data)} по направлению: {record_data["subject"]}. ' \
                        f'Именно таких уроков в абонементах больше нет. Скорее всего нужно продать продление. ' \
                        f'{"" if lead is not None else text_for_note}'
        new_task.save()
        if lead is not None:
            lead.status = Config.lead_status_zero_lessons_remained_value_id
            lead.save()


def student_marked_free_promo_process(record_data: RecordData, contact: Contact, lesson_time, leads: List[Lead],
                                      record_status_for_amo: RecordStatus):
    lead = choose_lead_for_free_promo(leads)
    create_task_after_promo(contact, lead, record_status_for_amo == RecordStatus.came_free_promo,
                            record_data, lesson_time)
    if lead is not None:
        lead.status = Config.lead_status_visited_promo_value_id \
            if record_status_for_amo == RecordStatus.came_free_promo else Config.lead_status_missed_promo_value_id
        lead.save()


def student_marked_paid_promo_process(record_data: RecordData, contact: Contact, lesson_time, leads: List[Lead],
                                      record_status_for_amo: RecordStatus):
    lead = choose_lead_for_paid_promo(leads, record_data)

    create_task_after_promo(contact, lead, record_status_for_amo == RecordStatus.came_paid_promo,
                            record_data, lesson_time)
    if lead is not None:
        if record_status_for_amo == RecordStatus.came_paid_promo:
            lead.pipeline = Config.primary_leads_pipeline_id
            lead.status = Config.lead_status_visited_promo_value_id
        else:
            lead.pipeline = Config.primary_leads_pipeline_id
            lead.status = Config.lead_status_missed_promo_value_id
        lead.save()


def student_cancelled_process(record_data: RecordData, contact: Contact, lesson_time, leads: List[Lead],
                              record_status_for_amo: RecordStatus):
    note_for_contact(contact, record_data, lesson_time)
    if (record_data['lastSimiliarLesson'] is None or (record_data['lastSimiliarLesson'] is not None and
                                                      unix_time(record_data['lastSimiliarLesson']['lessonStart']) <
                                                      int(time.time()))):
        lead = choose_lead_for_record(leads, record_data)
        new_task = Task()
        new_task.entity_id = lead.id if lead is not None else contact.id
        new_task.entity_type = "leads" if lead is not None else "contacts"

        if record_status_for_amo == RecordStatus.cancelled_paid_promo or \
                record_status_for_amo == RecordStatus.cancelled_free_promo:
            new_task.task_type_id = Config.task_type_cc_promo_reregister_value_id
            new_task.responsible_user = lead.responsible_user.id \
                if Config.settings_task_type_reregister_to_current_manager else Config.user_free_cc_tasks_holder_id

        else:
            new_task.task_type_id = Config.task_type_register_new_value_id
            new_task.responsible_user = Config.user_admin_1_id


        new_task.complete_till = datetime.now() + timedelta(seconds=7200)
        task_text = "еще есть такие уроки в абонементах, но "
        new_task.text = f'Отменил запись на ' \
                        f'{datetime.utcfromtimestamp(lesson_time).strftime("%d:%m:%Y %H:%M")} ' \
                        f'{"индивидуальный" if record_data["lessonUpdated"]["isIndividual"] else "групповой"} ' \
                        f'{record_program_type(record_data)} по направлению: {record_data["subject"]},  ' \
                        f'{task_text if record_status_for_amo == RecordStatus.cancelled_paid_promo else ""}' \
                        f'дальше не записан. Записать'
        new_task.save()
        if lead is not None:

            if record_status_for_amo == RecordStatus.cancelled_regular:
                lead.pipeline = Config.secondary_leads_pipeline_id
                lead.status = Config.lead_status_needs_schedule_value_id
            elif record_status_for_amo == RecordStatus.cancelled_free_promo:
                lead.pipeline = Config.primary_leads_pipeline_id
                lead.status = Config.lead_status_need_identified_value_id
            elif record_status_for_amo == RecordStatus.cancelled_paid_promo:
                lead.pipeline = Config.primary_leads_pipeline_id
                lead.status = Config.lead_status_payed_for_promo_value_id

            lead.save()


def student_came_event_process(lesson_time, leads: List[Lead], contact: Contact):
    lead = choose_lead_for_event(leads, contact)
    lead.status = Config.lead_status_came_event
    lead.save()
    lead.notes.objects.create(
        note_type='common',
        params={
            "text": f'Посетил концерт {datetime.utcfromtimestamp(lesson_time).strftime("%d.%m.%Y")} '
        }
    )
    lead.contacts.append(contact, False)


def create_task_after_promo(contact: Contact, lead: Lead, came: bool, record_data: RecordData, lesson_time: int):
    active_users = [typing.cast(User, user) for user in User.objects.all() if user.is_active]
    new_task = Task()
    new_task.entity_id = lead.id if lead is not None else contact.id
    new_task.entity_type = "leads" if lead is not None else "contacts"
    new_task.complete_till = datetime.now() + timedelta(seconds=7200)

    if came:
        new_task.task_type_id = Config.task_type_promo_retro_value_id
        new_task.responsible_user = lead.responsible_user.id if Config.settings_task_type_promo_retro_to_current_manager \
            else active_user_id_or_default(Config.user_sales_person_id, active_users)
        came_text = f'Нужно {"" if lead is not None else "найти сделку,"} ' \
               f'взять ОС по пробному и предложить подходящий продукт.'
    else:
        new_task.task_type_id = Config.task_type_cc_promo_reregister_value_id
        new_task.responsible_user = lead.responsible_user.id if Config.settings_task_type_promo_retro_to_current_manager \
            else Config.user_free_cc_tasks_holder_id
        came_text = "ПЕРЕЗАПИСАТЬ!"

    new_task.text = f'{"Посетил" if came else "Пропустил"} ' \
                    f'{datetime.utcfromtimestamp(lesson_time).strftime("%d:%m:%Y %H:%M")} ' \
                    f'{"индивидуальный" if record_data["lessonUpdated"]["isIndividual"] else "групповой"} ' \
                    f'{record_program_type(record_data)} по направлению: {record_data["subject"]}. ' \
                    f'{came_text}'
    new_task.save()


def record_status(record_data: RecordData):
    last_action = record_data['lessonUpdated']['recordHistory'][-1]['action']
    program_type = record_data['programType']
    visited = record_data['lessonUpdated']['visited'] is True
    if program_type == ProgramType.free_promo and last_action == Actions.visit_marked and not visited:
        return RecordStatus.not_came_free_promo
    if program_type == ProgramType.free_promo and last_action == Actions.visit_marked and visited:
        return RecordStatus.came_free_promo
    if program_type == ProgramType.paid_promo and last_action == Actions.visit_marked and not visited:
        return RecordStatus.not_came_paid_promo
    if program_type == ProgramType.paid_promo and last_action == Actions.visit_marked and visited:
        return RecordStatus.came_paid_promo
    if program_type == ProgramType.paid and last_action == Actions.cancelled:
        return RecordStatus.cancelled_regular
    if program_type == ProgramType.paid_promo and last_action == Actions.cancelled:
        return RecordStatus.cancelled_paid_promo
    if program_type == ProgramType.free_promo and last_action == Actions.cancelled:
        return RecordStatus.cancelled_free_promo
    if program_type == ProgramType.paid and last_action == Actions.visit_marked:
        return RecordStatus.marked_regular
    if program_type == ProgramType.event and last_action == Actions.visit_marked and visited:
        return RecordStatus.came_event
    if last_action == Actions.registered:
        return RecordStatus.registered
    if last_action == Actions.restored:
        return RecordStatus.restored
    return


def record_program_type(record_data: RecordData):
    match record_data['programType']:
        case ProgramType.paid:
            return 'платный урок'
        case ProgramType.free_promo:
            return 'бесплатный промоурок'
        case ProgramType.paid_promo:
            return 'платный промоурок'
        case ProgramType.event:
            return 'мероприятие'


def active_user_id_or_default(user_id, active_users: list[User]):
    try:
        return next((u.id for u in active_users if u.id == user_id), Config.user_free_cc_tasks_holder_id)
    except:
        return Config.user_free_cc_tasks_holder_id


def choose_lead_for_record(leads: list[Lead], record_data: RecordData):
    if len(leads) > 0:
        if record_data['programType'] == ProgramType.paid_promo:
            return choose_lead_for_paid_promo(leads, record_data)
        if record_data['programType'] == ProgramType.free_promo:
            return choose_lead_for_free_promo(leads)
        if record_data['programType'] == ProgramType.paid:
            return choose_lead_by_subscription(leads, record_data)
        return
    else:
        return


def choose_lead_by_subscription(leads: list[Lead], record_data: RecordData):
    for lead in leads:
        if lead.id_subscription_lessons == record_data['lessonUpdated']['subscriptionId']:
            return lead
    return


def choose_lead_for_free_promo(leads: list[Lead]):
    for lead in leads:
        if lead.pipeline.id == Config.primary_leads_pipeline_id \
                and lead.status == Config.lead_status_recorded_to_promo_value_id:
            return lead
    for lead in leads:
        if lead.pipeline.id == Config.primary_leads_pipeline_id:
            return lead
    return


def choose_lead_for_paid_promo(leads: list[Lead], record_data: RecordData):
    for lead in leads:
        if lead.id_subscription_paid_promo is not None:
            ids = lead.id_subscription_paid_promo.split(', ')
            if record_data['lessonUpdated']['subscriptionId'] in ids:
                return lead
    return


def choose_lead_for_event(leads: list[Lead], contact: Contact):
    for lead in leads:
        if lead.pipeline.id == Config.event_leads_pipeline_id:
            return lead
    print(f'Попытка прикрепить контакт {contact.id} к лиду - посмотри че там как')
    return Lead()


def note_for_contact(contact: Contact, record_data: RecordData, lesson_time):
    text_for_note = ''
    match record_data['lessonUpdated']['recordHistory'][-1]['action']:
        case Actions.visit_marked:
            text_for_note = f'{"Посетил" if record_data["lessonUpdated"]["visited"] else "Пропустил"}'
        case Actions.restored:
            text_for_note = 'Восстановлена запись на'
        case Actions.registered:
            text_for_note = 'Записан на'
        case Actions.cancelled:
            text_for_note = 'Отменена запись на'
    contact.notes.objects.create(
        note_type='common',
        params={
            "text": f'{datetime.utcfromtimestamp(lesson_time).strftime("%d.%m.%Y %H:%M")} '
                    f'{text_for_note} '
                    f'{"индивидуальный" if record_data["lessonUpdated"]["isIndividual"] else "групповой"} '
                    f'{record_program_type(record_data)} по направлению: {record_data["subject"]}'
        }
    )
