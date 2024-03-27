from datetime import datetime, timedelta
from asgiref.sync import async_to_sync

from amocrm.v2 import Task, tokens

from time_helpers import time_for_amo
from entity_helpers.contact_search import find_contact_by_docrm_data, find_contacts, clean_phone, Contact, \
                                          CustomLinksInteraction
from tags_helpers import create_tags

from config import Config
from tasks.amo_contact_create import update_or_create_contact


def custom_unlink(contact, lead):
    custom_interaction = CustomLinksInteraction()
    return custom_interaction.unlink(for_entity=lead, to_entity=contact)


def merge_contacts(contacts: list[Contact]):
    final_contact = contacts[0]
    token = tokens.default_token_manager.get_access_token()
    print(f'Несколько контактов, складываем всё в контакт {final_contact.id}')
    for contact in contacts[1:]:
        contact.phone = "+79999999999"
        contact.work_phone = "+79999999999"
        create_tags(contact, ["дубль контакта, нужно удалить"], token)
        contact.save()
        leads = contact.leads_loaded
        print(f'Дубль {contact.id} -> {final_contact.id}')
        for lead in leads:
            print(f'переносим lead {lead.id}')
            lead.contacts.append(final_contact, False)
            custom_unlink(contact, lead)

    async_to_sync(update_or_create_contact)(final_contact)


    return final_contact


def create_and_save_task(lesson, customer_phone):
    lesson_time = time_for_amo(lesson['lessonStart'])
    contacts = find_contacts(customer_phone)
    print(f'Найдено контактов {len(contacts)}')
    if len(contacts) > 1:
        contact = merge_contacts(contacts)
    else:
        contact = contacts[0]
    task = Task()
    task.entity_id = contact.id
    print(f'Ставим задачу на {contact.id}')
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
