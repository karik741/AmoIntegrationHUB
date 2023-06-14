from entity_helpers.contact_search import find_contact_by_lead, Contact
from entity_helpers.lead_custom_fields import Lead
from entity_helpers.enums import CustomerNotificationMedium
from config import Config
from asgiref.sync import async_to_sync
import aiohttp


def on_send_template_task(template_id: str, substitutions: list, lead_id: str):
    lead = Lead.objects.get(query=str(lead_id))
    contact = find_contact_by_lead(lead)
    async_to_sync(send_message_to_customer)(template_id, substitutions, contact)


async def send_message_to_customer(template_id: str, substitutions: list, contact: Contact):
    send_data = {
        'customerId': f'customer-{contact.doCRM_id}',
        'messageTemplateId': template_id,
        'medium': [CustomerNotificationMedium.WhatsApp],
        'onlyByFirstChannel': True,
        'manualReplacements': get_replacements(substitutions, contact),
    }
    print(get_replacements(substitutions, contact))
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                f"{Config.docrm_url}/api/NotificationApiExternal/SendTemplate", json=send_data)
            print(await response.text())
        except Exception as e:
            print(f"An error occurred: {e}")
            print(f"Response status: {response.status}")
            print(f"Response headers: {response.headers}")
            text = await response.text()
            print(f"Response body: {text}")


def get_replacements(substitutions: list, contact: Contact):
    if substitutions[0] == 'none':
        return []
    else:
        return [contact.name.split()[0] if substitution == 'name' else substitution for substitution in substitutions]
