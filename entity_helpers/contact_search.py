import re
import typing

from amocrm.v2 import Contact as ContactBase, Lead, tokens
from amocrm.v2.entity import custom_field

from config import Config


def find_contact_by_docrm_data(docrm_id: str, docrm_phone: str):
    contacts_by_id = find_contacts(docrm_id)
    contact_by_id_filtered = [x for x in contacts_by_id if x.doCRM_id == docrm_id]
    if len(contact_by_id_filtered) > 0:
        return contact_by_id_filtered[0]

    contact_by_phone_as_is = find_contact_by_phone(docrm_phone)
    if contact_by_phone_as_is:
        return contact_by_phone_as_is

    # Если мы не нашли контакт ни по ID, ни по номеру телефона;
    # Но телефон передан в российском международном формате;
    # Ищем по номеру телефона в российском внутреннем формате.
    if docrm_phone.startswith('+7'):
        docrm_phone_russian_internal = docrm_phone.replace('+7', '8', 1)
        contact_by_phone_russian_internal = find_contact_by_phone(docrm_phone_russian_internal)
        if contact_by_phone_russian_internal:
            return contact_by_phone_russian_internal

    # Если мы не нашли контакт ни по ID, ни по номеру телефона;
    # Но телефон передан в российском международном формате без +;
    # Ищем по номеру телефона в российском внутреннем формате.
    # TODO это идиотизм, DoCRM такое не передаёт
    if docrm_phone.startswith('7'):
        docrm_phone_russian_internal = docrm_phone.replace('7', '8', 1)
        contact_by_phone_russian_circumcised = find_contact_by_phone(docrm_phone_russian_internal)
        if contact_by_phone_russian_circumcised:
            return contact_by_phone_russian_circumcised

    # Ничего не нашли, сдаёмся
    return None


# Ищет в амо контакт по номеру телефона, дофильтровывает результаты поиска по очищенному номеру.
def find_contact_by_phone(phone: str):
    cleaned_phone = clean_phone(phone)
    contacts_by_phone = find_contacts(phone)

    for contact in contacts_by_phone:
        mobile_phone = contact.phone

        if mobile_phone and clean_phone(mobile_phone) == cleaned_phone:
            return contact

        work_phone = contact.work_phone

        if work_phone and clean_phone(work_phone) == cleaned_phone:
            return contact

    return None


# Запрашивает у амо контакты по строке поиска.
def find_contacts(query: str):
    return [typing.cast(Contact, contact) for contact in list(Contact.objects.filter(query=query))]


def find_contact_by_lead(lead: Lead):
    try:
        contact = [typing.cast(Contact, contact) for contact in lead.contacts][0]
        return contact
    except:
        return None


# Вырезает из строки всё, кроме цифр.
def clean_phone(phone: str):
    return re.sub(r'[^0-9]', '', phone)


lead_statuses_to_skip = Config.lead_statuses_exclude


class VisitedTrialValues:
    yes = custom_field.SelectValue(id=Config.client_visited_trial_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_visited_trial_no_value_id, value='Нет')


class HasPrepaidValues:
    yes = custom_field.SelectValue(id=Config.client_has_prepaid_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_has_prepaid_no_value_id, value='Нет')


class HasFullPaidValues:
    yes = custom_field.SelectValue(id=Config.client_has_full_paid_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_has_full_paid_no_value_id, value='Нет')


class HasActiveGroupDealValues:
    yes = custom_field.SelectValue(id=Config.client_has_active_group_deal_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_has_active_group_deal_no_value_id, value='Нет')


class HasActiveIndividualDealValues:
    yes = custom_field.SelectValue(id=Config.client_has_active_individual_deal_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_has_active_individual_deal_no_value_id, value='Нет')


class IsInScheduleValues:
    yes = custom_field.SelectValue(id=Config.client_is_in_schedule_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_is_in_schedule_no_value_id, value='Нет')


class IsInScheduleGroupValues:
    yes = custom_field.SelectValue(id=Config.client_is_in_group_schedule_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_is_in_group_schedule_no_value_id, value='Нет')


class IsInScheduleIndividualValues:
    yes = custom_field.SelectValue(id=Config.client_is_in_individual_schedule_yes_value_id, value='Да')
    no = custom_field.SelectValue(id=Config.client_is_in_individual_schedule_no_value_id, value='Нет')


class Contact(ContactBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.leads_loaded = []
        # noinspection PyProtectedMember
        if self.leads._data:
            self.leads_loaded = [typing.cast(Lead, x) for x in self.leads]

    doCRM_id = custom_field.TextCustomField("docrmUUID", field_id=Config.client_docrm_uuid_field_id)
    phone = custom_field.ContactPhoneField("Телефон", enum_code="MOB")
    work_phone = custom_field.ContactPhoneField("Телефон", enum_code="WORK")
    doCRM_url = custom_field.UrlCustomField("Ссылка на DOCRM")
    email = custom_field.ContactEmailField("", field_id=Config.client_email_field_id)
    visited_trial_lesson = \
        custom_field.SelectCustomField("", field_id=Config.client_visited_trial_lesson_field_id,
                                       enums=VisitedTrialValues)
    last_visited_trial_lesson_date = \
        custom_field.DateCustomField("", field_id=Config.client_last_visited_trial_lesson_date_field_id)
    last_visited_trial_lesson_direction = \
        custom_field.TextCustomField("", field_id=Config.client_last_visited_trial_lesson_direction_field_id)
    has_prepaid = custom_field.SelectCustomField("", field_id=Config.client_has_prepaid_field_id,
                                                 enums=HasPrepaidValues)
    last_prepaid_date = custom_field.DateCustomField("", field_id=Config.client_last_prepaid_date_field_id)
    last_prepaid_sum = custom_field.NumericCustomField("", field_id=Config.client_last_prepaid_sum_field_id)
    has_full_paid = custom_field.SelectCustomField("", field_id=Config.client_has_full_paid_field_id,
                                                   enums=HasFullPaidValues)
    full_paid_date = custom_field.DateCustomField("", field_id=Config.client_full_paid_date_field_id)
    last_deal_paid_sum = custom_field.NumericCustomField("", field_id=Config.client_last_deal_paid_sum_field_id)
    paid_group_count = custom_field.NumericCustomField("", field_id=Config.client_paid_group_count_field_id)
    paid_individual_count = custom_field.NumericCustomField("", field_id=Config.client_paid_individual_count_field_id)
    paid_sum_full = custom_field.NumericCustomField("", field_id=Config.client_paid_sum_full_field_id)
    has_active_group_deal = custom_field.SelectCustomField("", field_id=Config.client_has_active_group_deal_field_id,
                                                           enums=HasActiveGroupDealValues)
    has_active_individual_deal = \
        custom_field.SelectCustomField("", field_id=Config.client_has_active_individual_deal_field_id,
                                       enums=HasActiveIndividualDealValues)
    is_in_schedule = custom_field.SelectCustomField("", field_id=Config.client_is_in_schedule_field_id,
                                                    enums=IsInScheduleValues)
    is_in_schedule_group = custom_field.SelectCustomField(
        "Студент стоит в расписании по групповому абонементу",
        field_id=Config.client_is_in_group_schedule_field_id, enums=IsInScheduleGroupValues)
    is_in_schedule_individual = custom_field.SelectCustomField(
        "Студент стоит в расписании по индивидуальному абонементу",
        field_id=Config.client_is_in_individual_schedule_field_id, enums=IsInScheduleIndividualValues)
    last_group_lesson_visit_date = \
        custom_field.DateCustomField("", field_id=Config.client_last_group_lesson_visit_date_field_id)
    last_group_deal_end_date = \
        custom_field.DateCustomField("", field_id=Config.client_last_group_deal_end_date_field_id)
    remained_group_lesson_count = \
        custom_field.NumericCustomField("", field_id=Config.client_remained_group_lesson_count_field_id)
    last_record_date = custom_field.DateCustomField("", field_id=Config.client_last_record_date_field_id)
    last_receive_time = custom_field.DateTimeCustomField("", field_id=Config.client_last_receive_time_field_id)
    last_group_lesson_visit_direction = \
        custom_field.TextCustomField("", field_id=Config.client_last_group_lesson_visit_direction_field_id)
    last_individual_lesson_visit_date = \
        custom_field.DateCustomField("", field_id=Config.client_last_individual_lesson_visit_date_field_id)
    last_individual_lesson_visit_teacher = \
        custom_field.TextCustomField("", field_id=Config.client_last_individual_lesson_visit_teacher_field_id)
    remained_individual_lesson_count = \
        custom_field.NumericCustomField("", field_id=Config.client_remained_individual_lesson_count_field_id)
    last_cancelled_record_date = \
        custom_field.DateCustomField("", field_id=Config.client_last_cancelled_record_date_field_id)
    last_group_lesson_visit_teacher = \
        custom_field.TextCustomField("", field_id=Config.client_last_group_lesson_visit_teacher_field_id)
    last_visited_trial_lesson_teacher = \
        custom_field.TextCustomField("", field_id=Config.client_last_visited_trial_lesson_teacher_field_id)

    def primary_leads(self):
        return [x for x in self.leads_loaded
                if x.pipeline.id == Config.primary_leads_pipeline_id and x.status.id not in lead_statuses_to_skip]

    def secondary_leads(self):
        return [x for x in self.leads_loaded
                if x.pipeline.id == Config.secondary_leads_pipeline_id and x.status.id not in lead_statuses_to_skip]

    def primary_and_secondary_leads(self):
        return [x for x in self.leads_loaded if x.status.id not in lead_statuses_to_skip]
