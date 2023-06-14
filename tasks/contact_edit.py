from typing import TypedDict

from amocrm.v2 import Lead
from config import Config
from entity_helpers.contact_search import find_contact_by_docrm_data, Contact, VisitedTrialValues, HasPrepaidValues, \
    HasFullPaidValues, IsInScheduleGroupValues, IsInScheduleIndividualValues, HasActiveIndividualDealValues, \
    HasActiveGroupDealValues
from time_helpers import Instant


class ContactData(TypedDict):
    leadSource: str | None
    id: str
    amoId: str | None
    name: str | None
    email: str | None
    phone: str
    url: str
    leadSubject: str | None
    crmSegment: str | None
    visitedTrialLesson: bool | None
    lastVisitTrialLessonDate: Instant | None
    lastVisitTrialLessonDirection: str | None
    lastVisitTrialLessonTeacherId: str | None
    lastVisitTrialLessonTeacher: str | None
    hasPrepaid: bool
    lastPrepaidDate: Instant | None
    lastPrepaidSum: float | None
    hasFullPaid: bool
    fullPaidDate: Instant | None
    lastDealPaidSum: float | None
    paidGroupDealCount: int | None
    paidIndividualDealCount: int | None
    paidSumFull: float | None
    hasActiveGroupDeal: bool | None
    hasActiveIndividualDeal: bool | None
    isInScheduleGroup: bool | None
    isInScheduleIndividual: bool | None
    lastGroupDealEndDate: Instant | None
    remainedGroupLessonsCount: int | None
    remainedIndividualLessonsCount: int | None
    lastGroupLessonVisitDate: Instant | None
    lastGroupLessonVisitDirection: str | None
    lastGroupLessonVisitTeacher: str | None
    lastIndividualLessonVisitDate: Instant | None
    lastIndividualVisitTeacher: str | None
    lastCancelledRecordDate: Instant | None
    lastRecordInCardDate: Instant | None
    lastReceiveTime: Instant | None
    segmentId: str | None


def on_contact_edit(contact_data: ContactData):
    contact = None
    if contact_data["amoId"]:
        contact = Contact.objects.get(contact_data["amoId"])

    if not contact:
        contact = find_contact_by_docrm_data(contact_data["id"], contact_data["phone"])

    need_to_create_lead = False
    if not contact:
        if not Config.whitelist_enabled():
            contact = Contact()
            need_to_create_lead = True
        else:
            return

    if contact_data['phone']:
        contact.phone = contact_data['phone']

    if contact.phone not in Config.allowed_phones and Config.whitelist_enabled():
        return

    if contact_data['name']:
        contact.name = contact_data['name']

    if contact_data['id']:
        contact.doCRM_id = contact_data['id']

    if contact_data['email']:
        contact.email = contact_data['email']

    if contact_data['url']:
        contact.doCRM_url = contact_data['url']

    if contact_data['lastVisitTrialLessonDate']:
        contact.last_visited_trial_lesson_date = contact_data['lastVisitTrialLessonDate']['__instant']

    if contact_data['lastVisitTrialLessonDirection']:
        contact.last_visited_trial_lesson_direction = contact_data['lastVisitTrialLessonDirection']

    if contact_data['lastVisitTrialLessonTeacher'] is not None:
        contact.last_visited_trial_lesson_teacher = contact_data['lastVisitTrialLessonTeacher']

    if contact_data['fullPaidDate']:
        contact.full_paid_date = contact_data['fullPaidDate']['__instant']

    if contact_data['lastDealPaidSum']:
        contact.last_deal_paid_sum = contact_data['lastDealPaidSum']

    if contact_data['paidGroupDealCount']:
        contact.paid_group_count = contact_data['paidGroupDealCount']

    if contact_data['paidSumFull']:
        contact.paid_sum_full = contact_data['paidSumFull']

    if contact_data['paidIndividualDealCount']:
        contact.paid_individual_count = contact_data['paidIndividualDealCount']

    if contact_data['lastGroupDealEndDate']:
        contact.last_group_deal_end_date = contact_data['lastGroupDealEndDate']['__instant']

    if contact_data['remainedGroupLessonsCount']:
        contact.remained_group_lesson_count = contact_data['remainedGroupLessonsCount']

    if contact_data['remainedIndividualLessonsCount']:
        contact.remained_individual_lesson_count = contact_data['remainedIndividualLessonsCount']

    if contact_data['lastGroupLessonVisitDate']:
        contact.last_group_lesson_visit_date = contact_data['lastGroupLessonVisitDate']['__instant']

    if contact_data['lastGroupLessonVisitDirection']:
        contact.last_group_lesson_visit_direction = contact_data['lastGroupLessonVisitDirection']

    if contact_data['lastGroupLessonVisitTeacher'] is not None:
        contact.last_group_lesson_visit_teacher = contact_data['lastGroupLessonVisitTeacher']

    if contact_data['lastCancelledRecordDate']:
        contact.last_cancelled_record_date = contact_data['lastCancelledRecordDate']['__instant']

    if contact_data['lastRecordInCardDate']:
        contact.last_record_date = contact_data['lastRecordInCardDate']['__instant']

    if contact_data['lastReceiveTime'] is not None:
        contact.last_receive_time = contact_data['lastReceiveTime']['__instant']

    if contact_data['visitedTrialLesson'] is not None:
        contact.visited_trial_lesson = VisitedTrialValues.yes \
            if contact_data['visitedTrialLesson'] else VisitedTrialValues.no

    if contact_data['hasPrepaid'] is not None:
        contact.has_prepaid = HasPrepaidValues.yes \
            if contact_data['hasPrepaid'] else HasPrepaidValues.no
    #
    if contact_data['hasFullPaid'] is not None:
        contact.has_full_paid = HasFullPaidValues.yes \
            if contact_data['hasFullPaid'] else HasFullPaidValues.no

    if contact_data['hasActiveGroupDeal'] is not None:
        contact.has_active_group_deal = HasActiveGroupDealValues.yes \
            if contact_data['hasActiveGroupDeal'] else HasActiveGroupDealValues.no

    if contact_data['hasActiveIndividualDeal'] is not None:
        contact.has_active_individual_deal = HasActiveIndividualDealValues.yes \
            if contact_data['hasActiveIndividualDeal'] else HasActiveIndividualDealValues.no

    if contact_data['isInScheduleGroup'] is not None:
        contact.is_in_schedule_group = IsInScheduleGroupValues.yes \
            if contact_data['isInScheduleGroup'] else IsInScheduleGroupValues.no

    if contact_data['isInScheduleIndividual'] is not None:
        contact.is_in_schedule_individual = IsInScheduleIndividualValues.yes \
            if contact_data['isInScheduleIndividual'] else IsInScheduleIndividualValues.no

    contact.save()

    if need_to_create_lead:
        new_lead = Lead()
        new_lead.name = contact_data["name"] if contact_data["name"] else "Сделка"
        new_lead.responsible_user = Config.user_free_cc_tasks_holder_id
        new_lead.price = 0
        if contact_data['crmSegment'] is not None:
            match  contact_data['crmSegment']:
                case 'A':
                    new_lead.pipeline = Config.secondary_leads_pipeline_id
                    new_lead.status = Config.lead_status_in_schedule_value_id
                case 'B':
                    new_lead.pipeline = Config.secondary_leads_pipeline_id
                    new_lead.status = Config.lead_status_fullpayed_for_course_value_id
                case 'C':
                    new_lead.pipeline = Config.secondary_leads_pipeline_id
                    new_lead.status = Config.lead_status_zero_lessons_remained_value_id
                case 'D':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_recorded_to_promo_value_id
                case 'E':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_missed_promo_value_id
                case 'F':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_visited_promo_value_id
                case 'G':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_prepayed_for_course_value_id
                case 'H':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_primary_rejection
                    new_lead.loss_reason_id = Config.lead_primary_loss_reason_not_payed
                case 'I':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_primary_rejection
                    new_lead.loss_reason_id = Config.lead_primary_loss_reason_visit_promo_not_payed
                case 'J':
                    new_lead.pipeline = Config.primary_leads_pipeline_id
                    new_lead.status = Config.lead_status_primary_rejection
                    new_lead.loss_reason_id = Config.lead_primary_loss_reason_in_rejection

            new_lead.pipeline = Config.primary_leads_pipeline_id
            new_lead.status = Config.lead_status_new_lead_value_id
        new_lead.save()
        # TODO Дальше будет очень некрасивый хак, надо сделать PR в библиотеку и исправить его
        contacts = new_lead.contacts
        links = contacts._links
        links.link(for_entity=contacts._instance, to_entity=contact, main=False, metadata={"is_main": True})
