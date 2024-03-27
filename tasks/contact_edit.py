from typing import TypedDict
from asgiref.sync import async_to_sync

from amocrm.v2.exceptions import NotFound

from entity_helpers.lead_custom_fields import Lead
from config import Config
from entity_helpers.contact_search import find_contact_by_docrm_data, Contact, HasPaidActiveNotUsedSubscription, \
    HasPaidActiveSubscriptionWithRemainingUnits, \
    HasPaidArchiveSubscriptionWithRemainingUnits, HasPaidPromoVisitedLesson, HasFreePromoVisitedLesson, find_contacts
from tasks.amo_contact_create import update_or_create_contact
from time_helpers import Instant, time_for_amo


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
    lastVisitTrialLessonDate: Instant | None
    lastVisitTrialLessonDirection: str | None
    lastVisitTrialLessonTeacherId: str | None
    lastVisitTrialLessonTeacher: str | None
    lastPrepaidDate: Instant | None
    lastPrepaidSum: float | None
    hasActiveGroupDeal: bool | None
    remainedGroupLessonsCount: int | None
    remainedIndividualLessonsCount: int | None
    lastGroupLessonVisitDate: Instant | None
    lastGroupLessonVisitDirection: str | None
    lastGroupLessonVisitTeacher: str | None
    lastIndividualLessonVisitDate: Instant | None
    lastIndividualVisitTeacher: str | None
    lastCancelledRecordDate: Instant | None
    lastReceiveTime: Instant | None
    segmentId: str | None

    lastPaidLessonDate: Instant | None
    lastPaidFutureLessonDate: Instant | None
    lastPaidVisitedLessonVisitDate: Instant | None
    lastPaidVisitedLessonSubjectName: str | None
    lastPaidVisitedLessonTeacherName: str | None
    countPaidFullPaidSubscriptions: int | None
    lastPaidFullPaidSubscriptionLastPaymentDate: Instant | None
    lastPaidFullPaidSubscriptionLastPaymentSum: float | None
    lastPaidFullPaidSubscriptionSubjectNames: list
    countPaidPartiallyPaidSubscriptions: int
    lastPaidPartiallyPaidSubscriptionLastPaymentDate: Instant | None
    countPaidActiveSubscriptions: int
    hasPaidActiveNotUsedSubscription: bool
    hasPaidActiveSubscriptionWithRemainingUnits: bool
    hasPaidArchiveSubscriptionWithRemainingUnits: bool
    hasPaidPromoVisitedLesson: bool
    lastPaidPromoVisitedLessonVisitDate: Instant | None
    lastPaidPromoVisitedLessonSubjectName: str | None
    lastPaidPromoVisitedLessonTeacherName: str | None
    countPaidPromoFullPaidSubscriptions: int
    countPaidPromoActiveSubscriptions: int
    lastPaidPromoFullPaidSubscriptionLastPaymentDate: Instant | None
    lastPaidPromoFullPaidSubscriptionSubjectNames: list
    hasFreePromoVisitedLesson: bool
    lastFreePromoVisitedLessonVisitDate: Instant | None
    lastFreePromoVisitedLessonSubjectName: str | None
    lastFreePromoVisitedLessonTeacherName: str | None


def on_contact_edit(contact_data: ContactData):
    contact = None
    try:
        if contact_data["amoId"]:
            contact = Contact.objects.get(contact_data["amoId"])
    except NotFound:
        print(f'Контакт с id {contact_data["amoId"]} не найден')

    if not contact:
        print(f'Поиск контакта по docrm_id {contact_data["id"]} и по номеру телефона {contact_data["phone"]}')
        if contact_data['phone'] == "Используется номер другого клиента":
            contact = find_contacts(contact_data["id"])
        else:
            contact = find_contact_by_docrm_data(contact_data["id"], contact_data["phone"])
        if contact:
            print('Контакт найден, отправляем в DoCRM')
            async_to_sync(update_or_create_contact)(contact)

    need_to_create_lead = False
    if not contact:
        if not Config.whitelist_enabled():
            print(f"Не нашли контакт по номеру {contact_data['phone']} - создаем новый контакт")
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

    if contact_data['remainedGroupLessonsCount'] is not None:
        contact.remained_group_lesson_count = contact_data['remainedGroupLessonsCount']

    if contact_data['remainedIndividualLessonsCount'] is not None:
        contact.remained_individual_lesson_count = contact_data['remainedIndividualLessonsCount']

    if contact_data['lastGroupLessonVisitDate'] is not None:
        contact.last_group_lesson_visit_date = time_for_amo(contact_data['lastGroupLessonVisitDate'])

    if contact_data['lastGroupLessonVisitDirection'] is not None:
        contact.last_group_lesson_visit_direction = contact_data['lastGroupLessonVisitDirection']

    if contact_data['lastGroupLessonVisitTeacher'] is not None:
        contact.last_group_lesson_visit_teacher = contact_data['lastGroupLessonVisitTeacher']

    if contact_data['lastCancelledRecordDate'] is not None:
        contact.last_cancelled_record_date = time_for_amo(contact_data['lastCancelledRecordDate'])

    if contact_data['lastReceiveTime'] is not None:
        contact.last_receive_time = time_for_amo(contact_data['lastReceiveTime'])

    # новые поля
    if contact_data['lastPaidLessonDate'] is not None:
        contact.last_paid_lesson_date = time_for_amo(contact_data['lastPaidLessonDate'])

    if contact_data['lastPaidFutureLessonDate'] is not None:
        contact.last_paid_future_lesson_date = time_for_amo(contact_data['lastPaidFutureLessonDate'])

    if contact_data['lastPaidVisitedLessonVisitDate'] is not None:
        contact.last_paid_visited_lesson_date = time_for_amo(contact_data['lastPaidVisitedLessonVisitDate'])

    if contact_data['lastPaidVisitedLessonSubjectName'] is not None:
        contact.last_paid_visited_subject_name = contact_data['lastPaidVisitedLessonSubjectName']

    if contact_data['lastPaidVisitedLessonTeacherName'] is not None:
        contact.last_paid_visited_teacher_name = contact_data['lastPaidVisitedLessonTeacherName']

    if contact_data['countPaidFullPaidSubscriptions'] is not None:
        contact.count_paid_full_paid_subscriptions = contact_data['countPaidFullPaidSubscriptions']

    if contact_data['lastPaidFullPaidSubscriptionLastPaymentDate'] is not None:
        contact.last_paid_full_paid_subscription_last_payment_date = \
            time_for_amo(contact_data['lastPaidFullPaidSubscriptionLastPaymentDate'])

    if contact_data['lastPaidFullPaidSubscriptionLastPaymentSum'] is not None:
        contact.last_paid_full_paid_subscription_last_payment_sum =\
            contact_data['lastPaidFullPaidSubscriptionLastPaymentSum']

    if contact_data['lastPaidFullPaidSubscriptionSubjectNames'] is not None:
        contact.last_paid_full_paid_subscription_subject_names = contact_data['lastPaidFullPaidSubscriptionSubjectNames']

    if contact_data['countPaidPartiallyPaidSubscriptions'] is not None:
        contact.count_paid_partially_paid_subscriptions = contact_data['countPaidPartiallyPaidSubscriptions']

    if contact_data['lastPaidPartiallyPaidSubscriptionLastPaymentDate'] is not None:
        contact.last_paid_partially_paid_subscription_last_payment_date = \
            time_for_amo(contact_data['lastPaidPartiallyPaidSubscriptionLastPaymentDate'])

    if contact_data['countPaidActiveSubscriptions'] is not None:
        contact.count_paid_active_subscriptions = contact_data['countPaidActiveSubscriptions']

    if contact_data['hasPaidActiveNotUsedSubscription'] is not None:
        contact.has_paid_active_not_used_subscription = HasPaidActiveNotUsedSubscription.yes \
        if contact_data['hasPaidActiveNotUsedSubscription'] else HasPaidActiveNotUsedSubscription.no

    if contact_data['hasPaidActiveSubscriptionWithRemainingUnits'] is not None:
        contact.has_paid_active_subscription_with_remaining_units = HasPaidActiveSubscriptionWithRemainingUnits.yes \
        if contact_data['hasPaidActiveSubscriptionWithRemainingUnits'] else \
            HasPaidActiveSubscriptionWithRemainingUnits.no

    if contact_data['hasPaidArchiveSubscriptionWithRemainingUnits'] is not None:
        contact.has_paid_archive_subscription_with_remaining_units = HasPaidArchiveSubscriptionWithRemainingUnits.yes \
        if contact_data['hasPaidArchiveSubscriptionWithRemainingUnits'] else \
            HasPaidArchiveSubscriptionWithRemainingUnits.no

    if contact_data['hasPaidPromoVisitedLesson'] is not None:
        contact.has_paid_promo_visited_lesson = HasPaidPromoVisitedLesson.yes \
        if contact_data['hasPaidPromoVisitedLesson'] else HasPaidPromoVisitedLesson.no

    if contact_data['lastPaidPromoVisitedLessonVisitDate'] is not None:
        contact.last_paid_promo_visited_lesson_visit_date = \
            time_for_amo(contact_data['lastPaidPromoVisitedLessonVisitDate'])

    if contact_data['lastPaidPromoVisitedLessonSubjectName'] is not None:
        contact.last_paid_promo_visited_lesson_subject_name = contact_data['lastPaidPromoVisitedLessonSubjectName']

    if contact_data['lastPaidPromoVisitedLessonTeacherName'] is not None:
        contact.last_paid_promo_visited_lesson_teacher_name = contact_data['lastPaidPromoVisitedLessonTeacherName']

    if contact_data['countPaidPromoFullPaidSubscriptions'] is not None:
        contact.count_paid_promo_full_paid_subscriptions = contact_data['countPaidPromoFullPaidSubscriptions']

    if contact_data['countPaidPromoActiveSubscriptions'] is not None:
        contact.count_paid_promo_active_subscriptions = contact_data['countPaidPromoActiveSubscriptions']

    if contact_data['lastPaidPromoFullPaidSubscriptionLastPaymentDate'] is not None:
        contact.last_paid_promo_full_paid_subscription_last_payment_date = \
            time_for_amo(contact_data['lastPaidPromoFullPaidSubscriptionLastPaymentDate'])

    if contact_data['lastPaidPromoFullPaidSubscriptionSubjectNames'] is not None:
        contact.last_paid_promo_full_paid_subscription_subject_names = \
            contact_data['lastPaidPromoFullPaidSubscriptionSubjectNames']

    if contact_data['hasFreePromoVisitedLesson'] is not None:
        contact.has_free_promo_visited_lesson = HasFreePromoVisitedLesson.yes \
        if contact_data['hasFreePromoVisitedLesson'] else HasFreePromoVisitedLesson.no

    if contact_data['lastFreePromoVisitedLessonVisitDate'] is not None:
        contact.last_free_promo_visited_lesson_visit_date = \
            time_for_amo(contact_data['lastFreePromoVisitedLessonVisitDate'])

    if contact_data['lastFreePromoVisitedLessonSubjectName'] is not None:
        contact.last_free_promo_visited_lesson_subject_name = contact_data['lastFreePromoVisitedLessonSubjectName']

    if contact_data['lastFreePromoVisitedLessonTeacherName'] is not None:
        contact.last_free_promo_visited_lesson_teacher_name = contact_data['lastFreePromoVisitedLessonTeacherName']


    # if contact_data['crmSegment'] is not None:
    #     lead = contact.leads_loaded[0]
    #     lead.pipeline = Config.primary_leads_pipeline_id
    #     lead.status = Config.lead_status_primary_rejection
    #     access_token = tokens.default_token_manager.get_access_token()
    #     create_tags(lead, [contact_data['crmSegment']], access_token)
    #     lead.save()

    contact.save()


    if need_to_create_lead:
        new_lead = Lead()
        new_lead.name = contact_data["name"] if contact_data["name"] else "Сделка"
        new_lead.responsible_user = Config.user_free_cc_tasks_holder_id
        new_lead.pipeline = Config.primary_leads_pipeline_id
        new_lead.status = Config.lead_status_new_lead_value_id
        new_lead.price = 0
        new_lead.save()
        # TODO Дальше будет очень некрасивый хак, надо сделать PR в библиотеку и исправить его
        contacts = new_lead.contacts
        links = contacts._links
        links.link(for_entity=contacts._instance, to_entity=contact, main=False, metadata={"is_main": True})

