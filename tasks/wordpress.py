from typing import TypedDict

from amocrm.v2 import Lead
from entity_helpers.contact_search import find_contact_by_phone, Contact
from config import Config
from entity_helpers.enums import WordPressForm


class WordpressData(TypedDict):
    form_id: int
    form_submit_data: dict


def on_wordpress_task(wordpress_data: WordpressData):
    available_forms = [
        WordPressForm.home,
        WordPressForm.sign_up_for_lesson,
        WordPressForm.blocked_home,
        WordPressForm.promo_lesson,
        WordPressForm.promo_lesson_bottom,
        WordPressForm.sign_up_for_lesson_bottom,
        WordPressForm.sign_up_for_promo_lesson,
        WordPressForm.sign_up_for_vocal_lesson,
        WordPressForm.sign_up_for_vocal_lesson_bottom
    ]

    if wordpress_data['form_id'] in available_forms and \
            find_contact_by_phone(wordpress_data['form_submit_data']['mask-896']) is None:
        contact = Contact()
        contact.phone = wordpress_data['form_submit_data']['mask-896']
        contact.name = wordpress_data['form_submit_data']['text-898']
        contact.save()

        new_lead = Lead()
        new_lead.name = f'{wordpress_data["form_submit_data"]["text-898"]} оставил заявку с сайта moscow.lz-school.ru'
        new_lead.responsible_user = Config.user_free_cc_tasks_holder_id
        new_lead.price = 0
        new_lead.pipeline = Config.primary_leads_pipeline_id
        new_lead.status = Config.lead_status_new_lead_value_id
        new_lead.save()

        contacts = new_lead.contacts
        links = contacts._links
        links.link(for_entity=contacts._instance, to_entity=contact, main=False, metadata={"is_main": True})

