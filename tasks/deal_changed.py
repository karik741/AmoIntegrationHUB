import typing
from datetime import datetime, timedelta
from typing import TypedDict, Union
import time
from asgiref.sync import async_to_sync

from amocrm.v2 import Task, User, tokens
from amocrm.v2.entity.note import _Note

from config import Config
from entity_helpers.contact_search import find_contact_by_docrm_data, Contact
from entity_helpers.enums import ProgramType, LeadFunnels, DealAction, SubscriptionStatus, PaymentMethod
from entity_helpers.lead_custom_fields import Lead
from time_helpers import time_for_amo, Instant, unix_time
from tags_helpers import create_tags
from subscription import get_subscription


class DealPayment(TypedDict):
    amount: float
    when: Instant
    method: int


class DealData(TypedDict):
    customerId: str
    customerName: str
    customerPhone: str
    id: str
    isIndividual: bool
    price: float | None
    type: str
    totalPaid: float
    fullPaid: bool
    programType: int
    payments: list[DealPayment]
    similiarFutureLessons: int
    subjectName: str
    totalTimeUnits: int
    sellers: list[str]
    lastSimiliarFutureLesson: Instant | None
    subscriptionStatus: int
    isDead: bool


def on_deal_changed(deal_data: DealData):
    docrm_id = deal_data['customerId']
    docrm_phone = deal_data['customerPhone']

    if docrm_phone not in Config.allowed_phones and Config.whitelist_enabled():
        return

    if deal_data['totalPaid'] == 0 and deal_data['programType'] != ProgramType.event:
        # Если сумма оплаты по абонементу — 0, то либо абонемент свежесоздан, либо прошёл возвратный платёж.
        # Ничего не делаем.
        return

    if deal_change_should_be_skipped(deal_data):
        # TODO: здесь нужно пояснить, почему логика в методе deal_change_should_be_skipped именно такая.
        return

    contact = find_contact_by_docrm_data(docrm_id, docrm_phone)

    if not contact:
        # Не нашли контакт в АМО, ничего не делаем
        return

    if deal_data['payments'][0]['method'] == PaymentMethod.inner_transfer:
        return

    if deal_data['programType'] == ProgramType.event:
        process_event_deal(contact, deal_data)
        return

    if (deal_data['subscriptionStatus'] == SubscriptionStatus.paid or
        deal_data['subscriptionStatus'] == SubscriptionStatus.prepaid):
        if deal_data['type'] == 'Первичный':
            leads = contact.primary_leads()
            process_primary_deal(contact, deal_data, leads)
            return

        if deal_data['type'] == 'Вторичный':
            leads = contact.secondary_leads()
            process_secondary_deal(contact, deal_data, leads)
            return

    if deal_data['subscriptionStatus'] == SubscriptionStatus.archived:
        print(f'Абонемент стал архивным.\n'
              f'Телефон клиента: {docrm_phone}'
              f'ID клиента {docrm_id}')
        leads = contact.primary_and_secondary_leads()
        process_archived(contact, deal_data, leads)

    return


def process_archived(contact: Contact, deal_data: DealData, leads: list[Lead]):
    lead = choose_lead_for_archived(leads, deal_data)
    if lead:
        create_note_for_archived(lead, deal_data)
        create_task_for_archived(lead, deal_data)
        lead.status = Config.lead_status_zero_lessons_remained_value_id
        lead.save()

    else:
        create_note_for_archived(contact, deal_data)
        create_task_for_archived(contact, deal_data)
        contact.save()



def create_task_for_archived(entity: Union[Lead, Contact], deal_data: DealData):
    task = Task()
    task.text = (f'{datetime.now().strftime("%d.%m.%Y %H:%M")} '
                 f'ушел в архив абонемент {"индивидуальный" if deal_data["isIndividual"] else "групповой"}'
                 f'{deal_program_type(deal_data)}, '
                 f'направление: {deal_data["subjectName"]} на {deal_data["totalTimeUnits"]} часа(ов).'
                 f' за {deal_data["price"]} рублей.')

    task.entity_id = entity.id
    task.entity_type = 'leads' if isinstance(entity, Lead) else 'contacts'
    task.task_type_id = Config.task_type_renew_value_id
    task.responsible_user = Config.user_sales_person_id
    task.complete_till = datetime.now() + timedelta(seconds=60)
    task.save()


def create_note_for_archived(entity: Union[Lead, Contact], deal_data: DealData):
    entity.notes.objects.create(
        note_type='common',
        params={
            "text": f'Истек абонемент {"индивидуальный" if deal_data["isIndividual"] else "групповой"} '
                    f'{deal_program_type(deal_data)}, '
                    f'направление: {deal_data["subjectName"]} на {deal_data["totalTimeUnits"]} часа(ов).'
                    f' за {deal_data["price"]} рублей.'
        }
    )


def process_event_deal(contact: Contact, deal_data: DealData):
    access_token = tokens.default_token_manager.get_access_token()
    lead = choose_lead_for_tag(contact)
    if deal_data['price'] == contact.paid_sum_full:
        lead_tags = ['НЕ студент школы купил билет на концерт']
        contact_tags = ['НЕ студент школы купил билет на концерт']
        create_tags(contact, contact_tags, access_token)
        create_tags(lead, lead_tags, access_token)
    lead.roistat_user = "лид с концерта"
    lead.save()


def process_paid_promo(contact: Contact, deal_data: DealData, leads: list[Lead]):
    payment_time = time_for_amo(deal_data['payments'][0]['when'])
    lead = choose_lead_for_paid_promo(contact, leads, deal_data)
    if lead.id_subscription_paid_promo is not None:
        promo_ids = lead.id_subscription_paid_promo.split(', ')
        promo_ids.append(deal_data['id'])
        lead.id_subscription_paid_promo = ', '.join(promo_ids)
    else:
        lead.id_subscription_paid_promo = deal_data['id']
    lead.price = new_price_for_lead(lead, deal_data)
    lead.notes.objects.create(
        note_type='common',
        params={
            "text": f'{datetime.utcfromtimestamp(payment_time).strftime("%d.%m.%Y %H:%M")} '
                    f'получен платеж {deal_data["payments"][0]["amount"]}. '
                    f'{"Индивидуальный" if deal_data["isIndividual"] else "Групповой"} '
                    f'{deal_program_type(deal_data)}. '
                    f'Направление: {deal_data["subjectName"]}'
        }
    )
    lead.pipeline = Config.primary_leads_pipeline_id
    lead.status = Config.lead_status_payed_for_promo_value_id
    lead.save()
    create_paid_promo_task(deal_data, lead)


def process_primary_deal(contact: Contact, deal_data: DealData, leads: list[Lead]):
    if deal_data['programType'] == ProgramType.paid:
        lead = choose_lead_for_deal(contact, leads, deal_data)
        lead.price = new_price_for_lead(lead, deal_data)
        payment_time = time_for_amo(deal_data['payments'][0]['when'])
        create_note_for_lead(lead, deal_data, payment_time)
        lead.id_subscription_payments = deal_data['id']
        lead.pipeline = Config.primary_leads_pipeline_id
        lead.status = Config.lead_status_primary_payed_for_course_value_id \
            if deal_data['fullPaid'] else Config.lead_status_prepayed_for_course_value_id
        lead.save()
        on_paid_deal_payment(deal_data, contact, lead, DealAction.bought)

    if deal_data['programType'] == ProgramType.paid_promo:
        process_paid_promo(contact, deal_data, leads)



def process_secondary_deal(contact: Contact, deal_data: DealData, leads: list[Lead]):
    if deal_data['programType'] == ProgramType.paid:
        leads = contact.primary_and_secondary_leads()
        lead = choose_lead_for_deal(contact, leads, deal_data)
        lead.price = new_price_for_lead(lead, deal_data)
        payment_time = time_for_amo(deal_data['payments'][0]['when'])
        create_note_for_lead(lead, deal_data, payment_time)
        lead.pipeline = Config.secondary_leads_pipeline_id
        lead.id_subscription_payments = deal_data['id']
        lead.status = Config.lead_status_secondary_payed_value_id \
            if deal_data['fullPaid'] else Config.lead_status_secondary_prepayed_value_id
        lead.save()
        on_paid_deal_payment(deal_data, contact, lead, DealAction.visits)

    if deal_data['programType'] == ProgramType.paid_promo:
        leads = contact.primary_leads()
        process_paid_promo(contact, deal_data, leads)


def create_note_for_lead(lead: Lead, deal_data: DealData, payment_time: int):
    new_deal_text = 'Сделка успешно завершается, тк получена полная оплата абонемента с типом платный урок.'
    lead.notes.objects.create(
        note_type='common',
        params={
            "text": f'{datetime.utcfromtimestamp(payment_time).strftime("%d.%m.%Y %H:%M")} '
                    f'получен платеж {deal_data["payments"][0]["amount"]}, '
                    f'общая полученная по абонементу сумма {deal_data["totalPaid"]}. '
                    f'{"Индивидуальный" if deal_data["isIndividual"] else "Групповой"} '
                    f'{deal_program_type(deal_data)}, '
                    f'направление: {deal_data["subjectName"]} на {deal_data["totalTimeUnits"]} часа(ов). \n\n'
                    f'{new_deal_text if deal_data["fullPaid"] else ""}'
        }
    )


def create_paid_promo_task(deal_data: DealData, lead: Lead):
    new_task = Task()
    new_task.text = f'Оплачен платный промоурок. Нужно записать. ' \
                    f'Передать задачу {", ".join(deal_data["sellers"])}, ' \
                    f'если менеджер на смене, или записать самостоятельно.'
    new_task.entity_id = lead.id
    new_task.entity_type = 'leads'
    new_task.task_type_id = Config.task_type_cc_promo_register_value_id
    new_task.responsible_user = Config.user_free_cc_tasks_holder_id
    new_task.complete_till = datetime.now() + timedelta(seconds=60)
    new_task.save()


def on_paid_deal_payment(deal_data: DealData, contact: Contact, lead: Lead, action: DealAction):
    if deal_data['fullPaid']:
        new_lead = create_lead(deal_data, contact, LeadFunnels.secondary, action)
        move_tasks_and_notes_to_lead(lead, new_lead)
        copy_fields(lead, new_lead, deal_data)
        record_task(deal_data, new_lead)
        promo_retro_result_text = 'Задача завершена автоматически после оплаты'
        renew_result_text = 'Задача завершена автоматически после получения вторичного платежа'
        fullpay_result_text = 'Задача завершена автоматически после доплаты депозита'
        complete_tasks(new_lead, Config.task_type_promo_retro_value_id, promo_retro_result_text)
        complete_tasks(new_lead, Config.task_type_fullpay_value_id, fullpay_result_text)
        complete_tasks(new_lead, Config.task_type_renew_value_id, renew_result_text)
    else:
        active_users = [typing.cast(User, user) for user in User.objects.all() if user.is_active]
        new_task = Task()
        new_task.text = 'Внес предоплату. Нужно назначить адекватный срок для задачи на доплату'
        new_task.entity_id = lead.id
        new_task.entity_type = 'leads'
        new_task.task_type_id = Config.task_type_fullpay_value_id
        new_task.responsible_user = lead.responsible_user.id if Config.settings_task_type_fullpay_to_current_manager else \
            record_active_user_id_or_default(Config.user_sales_person_id, active_users)
        new_task.complete_till = datetime.now() + timedelta(seconds=60)
        new_task.save()
        record_task(deal_data, lead)
        promo_retro_result_text = 'Задача завершена автоматически после частичной оплаты'
        complete_tasks(lead, Config.task_type_promo_retro_value_id, promo_retro_result_text)


def record_task(deal_data: DealData, lead: Lead):
    new_task = Task()
    payment_time = time_for_amo(deal_data['payments'][0]['when'])

    new_task.text = f'{datetime.utcfromtimestamp(payment_time).strftime("%d.%m.%Y %H:%M")} ' \
                    f'получена {"полная оплата" if deal_data["fullPaid"] else "предоплата"}. Записать.'
    new_task.entity_id = lead.id
    new_task.entity_type = 'leads'
    new_task.task_type_id = Config.task_type_register_new_value_id
    new_task.responsible_user = Config.user_admin_1_id
    new_task.complete_till = deal_time_to_task(deal_data)
    new_task.save()


def create_lead(deal_data: DealData, contact: Contact, lead_funnel: int, deal_action=DealAction.buys):
    lead = Lead()
    lead.price = 0
    lead.pipeline = Config.primary_leads_pipeline_id \
        if lead_funnel == LeadFunnels.primary else Config.secondary_leads_pipeline_id
    lead.status = Config.lead_status_contacted_value_id \
        if lead_funnel == LeadFunnels.primary else Config.lead_status_fullpayed_for_course_value_id
    lead.name = \
        f'{deal_data["customerName"]} {"вторичная " if lead_funnel == LeadFunnels.secondary else ""}' \
        f'{"покупает" if deal_action == DealAction.buys else "посещает" if deal_action == DealAction.visits else "купил"} ' \
        f'{"индивидуальный" if deal_data["isIndividual"] else "групповой"} ' \
        f'{deal_program_type(deal_data)}, ' \
        f'направление: {deal_data["subjectName"]} на {deal_data["totalTimeUnits"]} часа(ов) ' \
        f'за {deal_data["totalPaid"]}'

    lead.save()
    lead.contacts.append(contact, False)
    return lead


def move_tasks_and_notes_to_lead(old_lead: Lead, new_lead: Lead):
    old_lead_tasks = [typing.cast(Task, x) for x in old_lead.tasks]
    old_lead_notes = [typing.cast(_Note, x) for x in old_lead.notes.objects.filter()]
    if len(old_lead_notes) == 0 and len(old_lead_tasks) == 0:
        return

    active_users = [typing.cast(User, user) for user in User.objects.all() if user.is_active]
    if len(old_lead_tasks) > 0:
        for old_lead_task in old_lead_tasks:
            copy_and_move_task(old_lead_task, new_lead.id, active_users)
            time.sleep(0.15)
    if len(old_lead_notes) > 0:
        for old_lead_note in old_lead_notes:
            copy_lead_note(old_lead_note, new_lead, active_users)
            time.sleep(0.15)



def copy_fields(old_lead: Lead, new_lead: Lead, deal_data: DealData):
    # TODO следующее поле не заполнено в конфиге ни у кого, кроме Гитардо
    # Надо с ним разобраться, пока завернул в try-except
    try:
        new_lead.roistat_user = old_lead.roistat_user
    except:
        pass

    new_lead.utm_content = old_lead.utm_content
    new_lead.utm_medium = old_lead.utm_medium
    new_lead.utm_campaign = old_lead.utm_campaign
    new_lead.utm_source = old_lead.utm_source
    new_lead.utm_term = old_lead.utm_term
    new_lead.utm_referrer = old_lead.utm_referrer
    new_lead.roistat = old_lead.roistat
    new_lead.id_subscription_lessons = deal_data['id']
    new_lead.save()


def create_figure_out_task_for_contact(contact: Contact, text: str):
    new_task = Task()
    new_task.text = text
    new_task.entity_type = 'contacts'
    new_task.entity_id = contact.id
    new_task.task_type_id = Config.task_type_fill_info_value_id
    new_task.responsible_user = Config.user_sales_leader_online_id
    new_task.complete_till = datetime.now() + timedelta(seconds=60)
    new_task.save()


def copy_and_move_task(old_task: Task, new_lead_id: str, active_users: list[User]):
    if not old_task.is_completed:
        Task.objects.update(
            old_task.id,
            entity_id=new_lead_id)
    else:
        new_task = Task()
        new_task.created_by = active_user_id_or_default(old_task, 'created_by', active_users)
        new_task.responsible_user = active_user_id_or_default(old_task, 'responsible_user', active_users)
        new_task.created_at = old_task.created_at
        new_task.updated_at = old_task.updated_at
        new_task.entity_id = new_lead_id
        new_task.entity_type = 'leads'
        new_task.duration_sec = old_task.duration_sec
        new_task.is_completed = old_task.is_completed
        new_task.task_type_id = old_task.task_type_id
        new_task.text = old_task.text if old_task.text else "    "
        new_task.result = old_task.result
        new_task.complete_till = old_task.complete_till

        new_task.save()


def copy_lead_note(note: _Note, new_lead: Lead, active_users: list[User]):
    new_lead.notes.objects.create(
        note_type=note.note_type,
        created_at=int(note.created_at.timestamp()),
        created_by=active_user_id_or_default(note, 'created_by', active_users),
        responsible_user_id=active_user_id_or_default(note, 'responsible_user', active_users),
        params=create_note_params(note)
    )


def create_note_params(note: _Note):
    if 'params' not in note._data:
        return {}

    params = note._data['params'].copy()
    if 'call_result' in params:
        if not params['call_result']:
            del params['call_result']

    return params


def deal_time_to_task(deal_data: DealData):
    if deal_data['similiarFutureLessons'] == 0:
        payment_time = time_for_amo(deal_data['payments'][0]['when'])
        time_to_task = datetime.utcfromtimestamp(payment_time)
    else:
        lesson_time = time_for_amo(deal_data['lastSimiliarFutureLesson'])
        time_to_task = datetime.utcfromtimestamp(lesson_time)
    return time_to_task


def active_user_id_or_default(entity: typing.Any, field_name: str, active_users: list[User]):
    try:
        user = getattr(entity, field_name)
        return next((u.id for u in active_users if u.id == user.id), Config.user_technician_id)
    except:
        return Config.user_technician_id


def record_active_user_id_or_default(user_id, active_users: list[User]):
    try:
        return next((u.id for u in active_users if u.id == user_id), Config.user_free_cc_tasks_holder_id)
    except:
        return Config.user_free_cc_tasks_holder_id


def deal_change_should_be_skipped(deal_data: DealData):
    return is_not_payment(deal_data)


def new_price_for_lead(lead: Lead, deal_data: DealData):
    if not deal_data['payments'][0]['amount']:
        return lead.price
    new_price = (lead.price if lead is not None else 0) + int(deal_data['payments'][0]['amount'])
    return new_price if new_price > 0 else 0


def choose_lead_for_deal(contact: Contact, leads: list[Lead], deal_data: DealData):
    if len(leads) > 0:
        for lead in leads:
            if lead.id_subscription_payments == deal_data['id']:
                return lead
        not_payments_leads = [lead for lead in leads if lead.id_subscription_payments is None]
        if len(not_payments_leads) > 0:
            lessons_leads = [lead for lead in not_payments_leads if lead.id_subscription_lessons is not None]
            if len(lessons_leads) > 0:
                for lead in lessons_leads:
                    subscription = async_to_sync(get_subscription)(lead.id_subscription_lessons)
                    if (deal_data['subjectName'] in subscription['subjects'] and
                        deal_data['programType'] == subscription['programType'] and
                        deal_data['isIndividual'] == subscription['isIndividual']):
                        return lead
                for lead in lessons_leads:
                    subscription = async_to_sync(get_subscription)(lead.id_subscription_lessons)
                    if deal_data['subjectName'] in subscription['subjects']:
                        return lead
        for lead in leads:
            if lead.id_subscription_payments is None and lead.id_subscription_lessons is None:
                return lead

    lead = create_lead(deal_data, contact, LeadFunnels.secondary)
    return lead


def choose_lead_for_paid_promo(contact: Contact, leads: list[Lead], deal_data: DealData):
    if len(leads) > 0:
        for lead in leads:
            if lead.id_subscription_paid_promo is not None:
                ids = lead.id_subscription_paid_promo.split(', ')
                if deal_data['id'] in ids:
                    return lead
        return leads[0]
    else:
        if deal_data['type'] == "Первичный":
            lead = create_lead(deal_data, contact, LeadFunnels.primary)
            return lead
        if deal_data['type'] == "Вторичный":
            lead = create_lead(deal_data, contact, LeadFunnels.secondary)
            return lead


def deal_program_type(deal_data: DealData):
    match deal_data['programType']:
        case ProgramType.paid:
            return 'платный урок'
        case ProgramType.free_promo:
            return 'бесплатный промоурок'
        case ProgramType.paid_promo:
            return 'платный промоурок'
        case ProgramType.event:
            return 'мероприятие'


def is_not_payment(deal_data: DealData):
    timestamp = int(time.time())
    if len(deal_data['payments']) > 0:
        return timestamp - unix_time(deal_data['payments'][0]['when']) > 600
    else:
        return True


def complete_tasks(lead: Lead, task_type: int, result_text: str):
    for task in lead.tasks:
        if task.task_type_id == task_type:
            Task.objects.update(
                task.id,
                is_completed=True,
                result={'text': result_text}
            )


def choose_lead_for_tag(contact: Contact):
    leads = contact.leads_loaded
    if len(leads) == 1:
        if datetime.now() - contact.leads_loaded[0].created_at < timedelta(minutes=5):
            return contact.leads_loaded[0]
        return Lead()
    else:
        return Lead()


def choose_lead_for_archived(leads: list[Lead], deal_data: DealData):
    if len(leads) > 0:
        for lead in leads:
            if lead.id_subscription_paid_promo == deal_data['id']:
                return lead
            if lead.id_subscription_payments == deal_data['id']:
                return lead
            if lead.id_subscription_payments == deal_data['id']:
                return lead
    return None