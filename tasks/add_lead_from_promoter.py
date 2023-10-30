from typing import TypedDict
import re

from amocrm.v2 import tokens

from entity_helpers.contact_search import Contact
from entity_helpers.lead_custom_fields import Lead
from tags_helpers import create_tags
from config import Config
from entity_helpers.contact_search import find_contacts


class PromoterLead(TypedDict):
    name: str
    phone_number: str
    promoter: str
    location: str
    supervisor: str
    direction: str
    trial_type: str


def on_add_lead_from_promoter(promoter_lead_data: PromoterLead):
    access_token = tokens.default_token_manager.get_access_token()
    contact = process_contact_for_lead_from_promoter(promoter_lead_data, access_token)

    lead = Lead()
    lead.name = f'Лид от промоутера {promoter_lead_data["name"]} {promoter_lead_data["direction"]} ' \
                f'оффлайн группы промоутер: {promoter_lead_data["promoter"]} супервайзер: ' \
                f'{promoter_lead_data["supervisor"]}'

    lead.promoter = promoter_lead_data['promoter']
    lead.promoter_location = promoter_lead_data['location']
    lead.supervisor = promoter_lead_data['supervisor']
    lead.direction = promoter_lead_data['direction']
    lead.pipeline = Config.primary_leads_pipeline_id
    lead.status = Config.lead_status_new_lead_value_id
    lead.roistat_user = "оффлайн_промоутеры"
    lead.save()

    lead_tags = [f'лид от промоутера']


    create_tags(lead, lead_tags, access_token)


    lead.contacts.append(contact, False)


def process_contact_for_lead_from_promoter(promoter_lead_data: PromoterLead, access_token: str):
    clean_phone = re.sub(r'\D', '', promoter_lead_data['phone_number'])
    contacts = find_contacts(clean_phone)
    if contacts:
        for contact in contacts:
            print(contact.name)
            print(contact.doCRM_id)
            if contact.doCRM_id is not None:
                return contact

        return contacts[0]

    contact = Contact()
    contact.name = promoter_lead_data['name']
    contact.phone = promoter_lead_data['phone_number']
    contact.save()
    contact_tags = [f'лид от промоутера']
    create_tags(contact, contact_tags, access_token)

    return contact
