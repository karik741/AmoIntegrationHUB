import typing
import requests
from typing import Iterable, Type, List, Dict

from amocrm.v2 import tokens, Pipeline, custom_field, Contact, Lead, User
from amocrm.v2.account import Account, AccountInteraction
from amocrm.v2.interaction import GenericInteraction
from amocrm.v2.manager import Manager
from amocrm.v2.model import Model

from config import Config


def create_all():
    access_token = tokens.default_token_manager.get_access_token()
    create_primary_pipeline()
    create_secondary_pipeline()
    create_event_pipeline()
    create_task_types()
    get_user_id()
    create_lead_custom_fields(access_token)
    create_contact_custom_fields(access_token)


def create_primary_pipeline():
    primary_pipeline = Pipeline()
    primary_pipeline.name = "Первичные продажи"
    primary_pipeline.sort = 10
    primary_pipeline.is_main = True
    primary_pipeline.is_unsorted_on = False
    primary_pipeline.statuses = [
        {"id": 142, "name": "ОПЛАТИЛ КУРС"},
        {"id": 143, "name": "[первичные]: ОТКАЗ"},
        {"name": "НОВАЯ ЗАЯВКА", "sort": 10},
        {"name": "НЕ ДОЗВОНИЛИСЬ (ПОПЫТКА СВЯЗАТЬСЯ СОВЕРШЕНА)", "sort": 20},
        {"name": "УСТАНОВЛЕН КОНТАКТ", "sort": 30},
        {"name": "ПОТРЕБНОСТЬ ВЫЯВЛЕНА", "sort": 40},
        {"name": "ЗАПИСАН НА ПРОБНОЕ", "sort": 50},
        {"name": "ПОДТВЕРДИЛ ПРОБНОЕ", "sort": 60},
        {"name": "НЕ ПРИШЕЛ НА ПРОБНОЕ", "sort": 70},
        {"name": "ПОСЕТИЛ ПРОБНОЕ", "sort": 80},
        {"name": "СОГЛАСЕН НА ПОКУПКУ", "sort": 90},
        {"name": "ВНЕС ПРЕДОПЛАТУ", "sort": 100}]

    primary_pipeline.save()
    primary_pipeline = Pipeline.objects.get(primary_pipeline.id)

    Config.primary_leads_pipeline_id = primary_pipeline.id
    Config.lead_status_new_lead_value_id = primary_pipeline.statuses[1].id
    Config.lead_status_not_contacted_value_id = primary_pipeline.statuses[2].id
    Config.lead_status_contacted_value_id = primary_pipeline.statuses[3].id
    Config.lead_status_need_identified_value_id = primary_pipeline.statuses[4].id
    Config.lead_status_recorded_to_promo_value_id = primary_pipeline.statuses[5].id
    Config.lead_status_missed_promo_value_id = primary_pipeline.statuses[7].id
    Config.lead_status_visited_promo_value_id = primary_pipeline.statuses[8].id
    Config.lead_status_prepayed_for_course_value_id = primary_pipeline.statuses[10].id
    Config.lead_status_primary_payed_for_course_value_id = 142
    Config.lead_status_primary_rejection = 143
    Config.lead_status_payed_for_promo_value_id = 0
    Config.lead_primary_loss_reason_not_payed = 0
    Config.lead_primary_loss_reason_in_rejection = 0
    Config.lead_primary_loss_reason_visit_promo_not_payed = 0


def create_secondary_pipeline():
    secondary_pipeline = Pipeline()
    secondary_pipeline.name = "Вторичные продажи"
    secondary_pipeline.sort = 20
    secondary_pipeline.is_main = False
    secondary_pipeline.is_unsorted_on = False
    secondary_pipeline.statuses = [
        {"id": 142, "name": "ОПЛАТИЛ КУРС"},
        {"id": 143, "name": "[вторичные]: ОТКАЗ"},
        {"name": "ПОЛУЧЕНА ПОЛНАЯ ОПЛАТА", "sort": 10},
        {"name": "СТОИТ ЗАДАЧА ПОСТАВИТЬ СТУДЕНТА В РАСПИСАНИЕ", "sort": 20},
        {"name": "СТУДЕНТ ПОСТАВЛЕН В РАСПИСАНИЕ", "sort": 30},
        {"name": "ОСТАЛОСЬ 0 УРОКОВ", "sort": 40},
        {"name": "ОТПРАВЛЕНА ССЫЛКА НА ОПЛАТУ НОВОГО АБОНЕМЕНТА", "sort": 50},
        {"name": "ВНЕС ПРЕДОПЛАТУ", "sort": 60}]

    secondary_pipeline.save()
    secondary_pipeline = Pipeline.objects.get(secondary_pipeline.id)

    Config.secondary_leads_pipeline_id = secondary_pipeline.id
    Config.lead_status_fullpayed_for_course_value_id = secondary_pipeline.statuses[1].id
    Config.lead_status_needs_schedule_value_id = secondary_pipeline.statuses[2].id
    Config.lead_status_in_schedule_value_id = secondary_pipeline.statuses[3].id
    Config.lead_status_zero_lessons_remained_value_id = secondary_pipeline.statuses[4].id
    Config.lead_status_secondary_prepayed_value_id = secondary_pipeline.statuses[6].id
    Config.lead_status_secondary_payed_value_id = 142
    Config.lead_status_secondary_rejection = 143


def create_event_pipeline():
    event_pipeline = Pipeline()
    event_pipeline.name = "Концерты"
    event_pipeline.sort = 30
    event_pipeline.is_main = False
    event_pipeline.is_unsorted_on = False
    event_pipeline.statuses = [
        {"id": 142, "name": "Посетил концерт"},
        {"name": "Куплен билет на концерт", "sort": 10},
    ]
    event_pipeline.save()

    event_pipeline = Pipeline.objects.get(event_pipeline.id)

    Config.event_leads_pipeline_id = event_pipeline.id
    Config.lead_status_payed_ticket = event_pipeline.statuses[1].id
    Config.lead_status_came_event = 142


def create_contact_custom_fields(access_token: str):
    fields = [
        {"name": "Ссылка на DOCRM", "type": "url", "sort": 1},
        {"name": "Текущий этап студента в GIS", "type": "text", "sort": 2},
        {"name": "Посещение пробного урока", "type": "select", "sort": 3, "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Дата последнего посещения пробного урока", "sort": 4, "type": "date"},
        {"name": "Направление последнего посещенного пробного", "sort": 5, "type": "text"},
        {"name": "Внес предоплату", "sort": 6, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Дата последнего внесения предоплаты", "sort": 7, "type": "date"},
        {"name": "Сумма последней предоплаты", "sort": 8, "type": "numeric"},
        {"name": "Внесена полная оплата/доплата", "sort": 9, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Дата внесения полной стоимости/доплаты", "sort": 10, "type": "date"},
        {"name": "Общая сумма оплаты последнего абонемента", "sort": 11, "type": "numeric"},
        {"name": "Количество полностью оплаченных групповых абонементов", "sort": 12, "type": "numeric"},
        {"name": "Количество полностью оплаченных индивидуальных абонементов", "sort": 13, "type": "numeric"},
        {"name": "Итого получено от студента за все время", "sort": 15, "type": "numeric"},
        {"name": "Есть хотя бы 1 действующий групповой абонемент", "sort": 16, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Есть хотя бы 1 действующий индивидуальной абонемент", "sort": 17, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Студент стоит в расписании по групповому абонементу (OLD)", "sort": 18, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Студент стоит в расписании по групповому абонементу", "sort": 19, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Студент стоит в расписании по индивидуальному абонементу", "sort": 20, "type": "select", "enums": [
            {"value": "Да", "sort": 1},
            {"value": "Нет", "sort": 2}]},
        {"name": "Дата последнего посещения урока по групповому абонементу", "sort": 21, "type": "date"},
        {"name": "Дата окончания последнего группового абонемента", "sort": 22, "type": "date"},
        {"name": "Всего количество оставшихся уроков по групповым абонементам", "sort": 23, "type": "numeric"},
        {"name": "Дата последней записи в карте студента в GIS", "sort": 24, "type": "date"},
        {"name": "Дата последней передачи данных GIS’ом", "sort": 25, "type": "date"},
        {"name": "Педагог последнего пробного урока", "sort": 26, "type": "text"},
        {"name": "Педагог последнего посещенного группового урока", "sort": 27, "type": "text"},
        {"name": "Дата последней отмены занятия", "sort": 28, "type": "date"},
        {"name": "Направление последнего посещенного группового урока", "sort": 29, "type": "text"},
        {"name": "Дата последнего посещенного индивидуального урока", "sort": 30, "type": "date"},
        {"name": "Педагог последнего посещенного индивидуального урока", "sort": 31, "type": "text"},
        {"name": "Всего количество оставшихся уроков по индивидуальным абонементам", "sort": 32, "type": "numeric"},
        {"name": "docrmUUID", "type": "text", "sort": 33, "is_api_only": True}
    ]
    create_fields("contacts", fields, access_token)
    fields = get_fields_for(Contact)
    for field in fields:
        match field.name:
            case "docrmUUID":
                Config.client_docrm_uuid_field_id = field.id
            case "Email":
                Config.client_email_field_id = field.id
            case "Посещение пробного урока":
                Config.client_visited_trial_lesson_field_id = field.id
                Config.client_visited_trial_yes_value_id = field.enums[0]["id"]
                Config.client_visited_trial_no_value_id = field.enums[1]["id"]
            case "Дата последнего посещения пробного урока":
                Config.client_last_visited_trial_lesson_date_field_id = field.id
            case "Направление последнего посещенного пробного":
                Config.client_last_visited_trial_lesson_direction_field_id = field.id
            case "Внес предоплату":
                Config.client_has_prepaid_field_id = field.id
                Config.client_has_prepaid_yes_value_id = field.enums[0]["id"]
                Config.client_has_prepaid_no_value_id = field.enums[1]["id"]
            case "Дата последнего внесения предоплаты":
                Config.client_last_prepaid_date_field_id = field.id
            case "Сумма последней предоплаты":
                Config.client_last_prepaid_sum_field_id = field.id
            case "Внесена полная оплата/доплата":
                Config.client_has_full_paid_field_id = field.id
                Config.client_has_full_paid_yes_value_id = field.enums[0]["id"]
                Config.client_has_full_paid_no_value_id = field.enums[1]["id"]
            case "Дата внесения полной стоимости/доплаты":
                Config.client_full_paid_date_field_id = field.id
            case "Общая сумма оплаты последнего абонемента":
                Config.client_last_deal_paid_sum_field_id = field.id
            case "Количество полностью оплаченных групповых абонементов":
                Config.client_paid_group_count_field_id = field.id
            case "Количество полностью оплаченных индивидуальных абонементов":
                Config.client_paid_individual_count_field_id = field.id
            case "Итого получено от студента за все время":
                Config.client_paid_sum_full_field_id = field.id
            case "Есть хотя бы 1 действующий групповой абонемент":
                Config.client_has_active_group_deal_field_id = field.id
                Config.client_has_active_group_deal_yes_value_id = field.enums[0]["id"]
                Config.client_has_active_group_deal_no_value_id = field.enums[1]["id"]
            case "Есть хотя бы 1 действующий индивидуальной абонемент":
                Config.client_has_active_individual_deal_field_id = field.id
                Config.client_has_active_individual_deal_yes_value_id = field.enums[0]["id"]
                Config.client_has_active_individual_deal_no_value_id = field.enums[1]["id"]
            case "Студент стоит в расписании по групповому абонементу (OLD)":
                Config.client_is_in_schedule_field_id = field.id
                Config.client_is_in_schedule_yes_value_id = field.enums[0]["id"]
                Config.client_is_in_schedule_no_value_id = field.enums[1]["id"]
            case "Студент стоит в расписании по групповому абонементу":
                Config.client_is_in_group_schedule_field_id = field.id
                Config.client_is_in_group_schedule_yes_value_id = field.enums[0]["id"]
                Config.client_is_in_group_schedule_no_value_id = field.enums[1]["id"]
            case "Студент стоит в расписании по индивидуальному абонементу":
                Config.client_is_in_individual_schedule_field_id = field.id
                Config.client_is_in_individual_schedule_yes_value_id = field.enums[0]["id"]
                Config.client_is_in_individual_schedule_no_value_id = field.enums[1]["id"]
            case "Дата последнего посещения урока по групповому абонементу":
                Config.client_last_group_lesson_visit_date_field_id = field.id
            case "Дата окончания последнего группового абонемента":
                Config.client_last_group_deal_end_date_field_id = field.id
            case "Всего количество оставшихся уроков по групповым абонементам":
                Config.client_remained_group_lesson_count_field_id = field.id
            case "Дата последней записи в карте студента в GIS":
                Config.client_last_record_date_field_id = field.id
            case "Дата последней передачи данных GIS’ом":
                Config.client_last_receive_time_field_id = field.id
            case "Направление последнего посещенного группового урока":
                Config.client_last_group_lesson_visit_direction_field_id = field.id
            case "Дата последнего посещенного индивидуального урока":
                Config.client_last_individual_lesson_visit_date_field_id = field.id
            case "Педагог последнего посещенного индивидуального урока":
                Config.client_last_individual_lesson_visit_teacher_field_id = field.id
            case "Всего количество оставшихся уроков по индивидуальным абонементам":
                Config.client_remained_individual_lesson_count_field_id = field.id
            case "Дата последней отмены занятия":
                Config.client_last_cancelled_record_date_field_id = field.id
            case "Педагог последнего посещенного группового урока":
                Config.client_last_group_lesson_visit_teacher_field_id = field.id
            case "Педагог последнего посещенного индивидуального урока":
                Config.client_last_visited_trial_lesson_teacher_field_id = field.id


def create_task_types():
    account = AccountInteraction().get(include=['task_types'])
    task_types = Account(account).task_types
    for task_type in task_types:
        match task_type["name"]:
            case "Обработка заявки":
                Config.task_type_cc_processing_site_value_id = task_type["id"]
            case "Запись на пробн":
                Config.task_type_cc_promo_register_value_id = task_type["id"]
            case "Перезапись пробн":
                Config.task_type_cc_promo_reregister_value_id = task_type["id"]
            case "Сбор ОС пробный":
                Config.task_type_promo_retro_value_id = task_type["id"]
            case "Доплата брони":
                Config.task_type_fullpay_value_id = task_type["id"]
            case "Продление":
                Config.task_type_renew_value_id = task_type["id"]
            case "Записать":
                Config.task_type_register_new_value_id = task_type["id"]
            case "Подтвердить урок":
                Config.task_type_confirmation = task_type["id"]


def get_user_id():
    users = [typing.cast(User, user) for user in User.objects.all()]
    Config.user_free_cc_tasks_holder_id = users[0].id
    Config.user_sales_person_id = users[0].id
    Config.user_admin_id = users[0].id
    Config.user_sales_leader_online_id = users[0].id
    Config.uses_sales_offl = users[0].id
    Config.user_technician_id = users[0].id


def create_lead_custom_fields(access_token: str):
    fields = [
        {"name": "ID абонемента для оплаты", "type": "text", "sort": 1},
        {"name": "ID абонемента для уроков", "type": "text", "sort": 2},
        {"name": "ID абонементов для оплаты платных промоуроков", "type": "text", "sort": 3},
    ]
    create_fields("leads", fields, access_token)
    fields = get_fields_for(Lead)
    Config.lead_statuses_exclude: [142, 143]
    for field in fields:
        match field.name:
            case "utm_content":
                Config.lead_utm_content_field_id = field.id
            case "utm_medium":
                Config.lead_utm_medium_field_id = field.id
            case "utm_campaign":
                Config.lead_utm_campaign_field_id = field.id
            case "utm_source":
                Config.lead_utm_source_field_id = field.id
            case "utm_term":
                Config.lead_utm_term_field_id = field.id
            case "utm_referrer":
                Config.lead_utm_referrer_field_id = field.id
            case "openstat_service":
                Config.lead_openstat_service_field_id = field.id
            case "openstat_campaign":
                Config.lead_openstat_campaign_field_id = field.id
            case "openstat_ad":
                Config.lead_openstat_ad_field_id = field.id
            case "openstat_source":
                Config.lead_openstat_source_field_id = field.id
            case "roistat":
                Config.lead_roistat_user_field_id = field.id
            case "ID абонемента для оплаты":
                Config.lead_id_subscription_payments_field_id = field.id
            case "ID абонемента для уроков":
                Config.lead_id_subscription_lessons_field_id = field.id
            case "ID абонементов для оплаты платных промоуроков":
                Config.lead_id_subscription_paid_promo_field_id = field.id

        Config.lead_roistat_field_id: 0


def get_fields_for(model: Type[Model]) -> Iterable[custom_field.CustomFieldModel]:
    return Manager(
        GenericInteraction(
            path=f"{model.objects._interaction.path}/custom_fields",
            field="custom_fields",
        ),
        model=custom_field.CustomFieldModel,
    ).all()


def create_fields(entity: str, fields: List[Dict], access_token: str):
    api_call_headers = {'Authorization': 'Bearer ' + access_token}
    requests.post(f'https://{Config.subdomain}.amocrm.ru/api/v4/{entity}/custom_fields',
                  json=fields, headers=api_call_headers, verify=True)
