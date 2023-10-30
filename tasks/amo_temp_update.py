from amocrm.v2 import tokens

from entity_helpers.lead_custom_fields import Lead
from tags_helpers import create_tags
from entity_helpers.contact_search import find_contact_by_phone
from config import Config


def on_push_amo_leads(number, pipeline_id, status_id, loss_reason_id, deal_name, tag):
    print(f'номер {number}, pipeline_id {pipeline_id}, status_id {status_id}, loss_reason_id {loss_reason_id}, '
          f'deal_name {deal_name}, tag {tag}')
    access_token = tokens.default_token_manager.get_access_token()
    contact = find_contact_by_phone(number)
    print(contact)
    lead = Lead()
    lead.name = deal_name
    lead.pipeline = int(pipeline_id)
    lead.status = int(status_id)
    lead.loss_reason_id = int(loss_reason_id)
    lead.save()
    print(lead.name)
    lead_tags = [tag]
    create_tags(lead, lead_tags, access_token)
    lead.contacts.append(contact, False)


