from datetime import datetime, timedelta
from typing import TypedDict

from amocrm.v2 import Task

from config import Config
from entity_helpers.contact_search import find_contact_by_docrm_data


class TaskData(TypedDict):
    taskCode: int
    gisId: str


def on_task_create(task_data: TaskData):
    contact = find_contact_by_docrm_data(task_data["gisId"], 'non_existing_phone')
    leads = contact.primary_leads()
    if task_data['taskCode'] == 1:
        entity_type = "contacts"
        entity_id = contact.id
        if len(leads) == 1:
            lead = leads[0]
            lead.status = Config.lead_status_missed_promo_value_id
            lead.pipeline = Config.primary_leads_pipeline_id
            lead.save()
            entity_type = "leads"
            entity_id = lead.id

        new_task = Task()
        new_task.entity_id = entity_id
        new_task.entity_type = entity_type
        new_task.task_type_id = Config.task_type_cc_promo_reregister_value_id
        new_task.responsible_user = Config.user_free_cc_tasks_holder_id
        new_task.complete_till = datetime.now() + timedelta(seconds=60)
        new_task.text = f'{datetime.now().strftime("%d.%m.%Y")} не пришел на пробный. Перезаписать.'
        new_task.save()
    if task_data["taskCode"] == 2:
        entity_type = "contacts"
        entity_id = contact.id
        if len(leads) == 1:
            lead = leads[0]
            lead.status = Config.lead_status_visited_promo_value_id
            lead.pipeline = Config.primary_leads_pipeline_id
            lead.responsible_user = Config.uses_sales_offl
            lead.save()
            entity_type = "leads"
            entity_id = lead.id

        new_task = Task()
        new_task.entity_id = entity_id
        new_task.entity_type = entity_type
        new_task.task_type_id = Config.task_type_promo_retro_value_id
        new_task.responsible_user = Config.uses_sales_offl
        new_task.complete_till = datetime.now() + timedelta(seconds=7200)
        new_task.text = f'{datetime.now().strftime("%d.%m.%Y")} был на пробном уроке, взять ОС, продать подходящий ' \
                        f'продукт. '
        new_task.save()

