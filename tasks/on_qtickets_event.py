from typing import TypedDict, List, Optional
from datetime import datetime, timedelta

from amocrm.v2 import tokens

from entity_helpers.lead_custom_fields import Lead
from entity_helpers.contact_search import find_contact_by_phone, Contact, HasActiveGroupDealValues, \
    HasActiveIndividualDealValues
from config import Config
from tags_helpers import create_tags


class Event(TypedDict):
    name: str


class Show(TypedDict):
    event: Event
    start_date: str
    finish_date: str


class Basket(TypedDict):
    id: int
    seat_name: str
    quantity: int
    price: int
    checked_at: Optional[str]
    show: Show
    client_email: str
    client_phone: str
    client_surname: str
    client_middlename: Optional[str]
    client_name: str


class QticketsWebhookResponse(TypedDict):
    payed: bool
    price: int
    baskets: List[Basket]


class Customer(TypedDict):
    hash: str
    leadSource: Optional[str]
    id: str
    amoId: Optional[str]
    name: str
    email: str
    phone: str
    url: str
    leadSubject: Optional[str]


class QticketsInfo(TypedDict):
    customer: Customer
    qticketsWebhookResponse: QticketsWebhookResponse


def on_qtickets_event(event: List[QticketsInfo]):
    access_token = tokens.default_token_manager.get_access_token()
    concert_date = get_concert_date(event)
    concert_name = get_event_name(event)

    for basket in event[0]['qticketsWebhookResponse']['baskets']:
        if basket['checked_at'] is None:
            phone = basket['client_phone']
            contact = find_contact_by_phone(phone)

            if not contact:
                return

            lead = choose_lead_for_event(contact)
            lead.price = basket['price']
            lead.pipeline = Config.event_leads_pipeline_id
            lead.status = Config.lead_status_payed_ticket
            lead.name = f'{basket["client_name"]} концерт: {concert_name} - {concert_date}'
            lead.save()
            lead_tags = [f'Концерт: {concert_name} - {concert_date}']
            create_tags(lead, lead_tags, access_token)
            lead.contacts.append(contact, False)


def choose_lead_for_event(contact: Contact):
    leads = contact.leads_loaded
    if len(leads) == 1:
        if datetime.now() - contact.leads_loaded[0].created_at < timedelta(minutes=5):
            return contact.leads_loaded[0]
        return Lead()
    else:
        return Lead()


def get_concert_date(event: List[QticketsInfo]) -> str:
    for e in event:
        for basket in e['qticketsWebhookResponse']['baskets']:
            start_date_str = basket['show']['start_date']
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            return start_date.strftime("%d.%m.%Y %H:%M")
    return ""


def get_event_name(event: List[QticketsInfo]) -> str:
    for e in event:
        for basket in e['qticketsWebhookResponse']['baskets']:
            concert_name = basket['show']['event']['name']
            return concert_name
    return ""



