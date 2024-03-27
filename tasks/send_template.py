from asgiref.sync import async_to_sync
import aiohttp
from typing import TypedDict, List

from entity_helpers.contact_search import find_contact_by_lead, Contact
from entity_helpers.lead_custom_fields import Lead
from config import Config
from tasks.amo_contact_create import update_or_create_contact


class Template(TypedDict):
    id: str
    substitutions: dict


def on_send_template_task(templates: List[Template], lead_id: str):
    lead = Lead.objects.get(object_id=lead_id)
    contact = find_contact_by_lead(lead)
    if contact:
        for template in templates:
            substitutions = [value for substitution, value in template['substitutions'].items()]
            async_to_sync(send_message_to_customer)(template['id'], substitutions, contact)
    else:
        print(f'Не найден контакт лида {lead.id} при попытке отправить шаблон')

async def send_message_to_customer(template_id: str, substitutions: list, contact: Contact, phone=None):
    if contact:
        await update_or_create_contact(contact)
    send_data = {
        'phone': phone or contact.phone or contact.work_phone,
        'messageTemplateId': template_id,
        'onlyByFirstChannel': False,
        'manualReplacements': get_replacements(substitutions, contact),
    }
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                f"{Config.docrm_url}/api/NotificationApiExternal/SendTemplate", json=send_data)
            response_data = await response.json()
            if not response_data.get('isSuccess'):
                print(response_data)
                print(send_data)

        except Exception as e:
            print(f"Error: {e}")
            print(send_data)



def get_replacements(substitutions: list, contact: Contact):
    if not substitutions:
        return []
    else:
        return [contact.name.split()[0] if substitution == 'name' else substitution for substitution in substitutions]




