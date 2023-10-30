import typing

import aiohttp

from config import Config
from entity_helpers.contact_search import Contact


async def on_amo_contact_task(id: int):
    contact = typing.cast(Contact, Contact.objects.get(id))
    await update_or_create_contact(contact)


async def update_or_create_contact(contact: Contact):
    if contact.phone in Config.allowed_phones or not Config.whitelist_enabled():
        send_data = {
            'phone': contact.phone or contact.work_phone,
            'name': contact.name if contact.name else 'Без имени',
            'alias': 'central',
            'email': contact.email,
            'facebookPageId': None,
            'subjectName': '',
            'leadDescriptor': None,
            'googleClientId': None,
            'roistatId': None,
            'amoId': contact.id

        }
        async with aiohttp.ClientSession() as session:
            await session.post(
                    f"{Config.docrm_url}/api/customerapi/createcustomerfromamo", json={'cmd': send_data})
