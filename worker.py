from celery.signals import worker_process_init, worker_ready
from celery.exceptions import MaxRetriesExceededError
from billiard.exceptions import SoftTimeLimitExceeded
from typing import List
from celery import Celery
from kombu import Queue, Exchange


from amo_auto_install import create_all, create_new_contact_custom_fields
from entity_helpers.amo_init import init_tokens
from monkey_patch import patch
from asgiref.sync import async_to_sync
from amocrm.v2 import tokens
from amocrm.v2.exceptions import UnAuthorizedException, AmoApiException


from config import Config, save
from tasks.amo_contact_create import on_amo_contact_task
from tasks.contact_edit import ContactData, on_contact_edit
from tasks.deal_changed import DealData, on_deal_changed
from tasks.record_updated import on_record_updated, RecordData
from tasks.wordpress import on_wordpress_task, WordpressData
from tasks.task_for_confirmation import create_and_save_task
from tasks.send_template import on_send_template_task, Template
from tasks.on_qtickets_event import on_qtickets_event, QticketsInfo
from tasks.add_lead_from_promoter import on_add_lead_from_promoter, PromoterLead
from tasks.amo_temp_update import on_push_amo_leads
from tasks.ai_confirmation import on_ai_confirmation, ConfirmationData

patch()

app = Celery(broker=Config.broker_url, backend='rpc://')

exchange_name = Config.task_queue

app.conf.task_queues = (
    Queue(f'{Config.task_queue}', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
    Queue(f'{Config.task_queue}_contacts_create', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
    Queue(f'{Config.task_queue}_contacts_update', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
    Queue(f'{Config.task_queue}_push_leads', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
    Queue(f'{Config.task_queue}_send_templates', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
    Queue(f'{Config.task_queue}_ai_confirmation', exchange=Exchange(exchange_name, type='direct'), routing_key=f'{Config.task_queue}', queue_arguments={'x-max-priority': 10}),
)

app.conf.task_default_queue = Config.task_queue
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5


@worker_ready.connect()
def start(**kwargs):
    token = init_tokens()
    if Config.client_docrm_uuid_field_id == 0:
        create_all()
        save()

    if Config.last_paid_lesson_date_id == 0:
        create_new_contact_custom_fields(token)
        save()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Обновляем токены каждый час.
    sender.add_periodic_task(3600, refresh_tokens_task.s(), name='Refresh tokens every hour')


@app.task(queue=f'{Config.task_queue}_contacts_create', priority=9, soft_time_limit=300, bind=True, max_retries=5)
def amo_contact_create_task(self, id: int):
    try:
        async_to_sync(on_amo_contact_task)(id)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)



@app.task(queue=f'{Config.task_queue}_contacts_update', priority=7, soft_time_limit=300, bind=True, max_retries=5)
def amo_contact_update_task(self, id: int):
    try:
        async_to_sync(on_amo_contact_task)(id)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(queue=f'{Config.task_queue}_contacts_update', priority=7, soft_time_limit=300, bind=True, max_retries=5)
def contact_edit_task(self, contact_data: ContactData):
    try:
        on_contact_edit(contact_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)



@app.task(queue=f'{Config.task_queue}_contacts_update', priority=0, soft_time_limit=300, bind=True, max_retries=5)
def contact_edit_from_hf_task(self, contact_data: ContactData):
    try:
        on_contact_edit(contact_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=4, soft_time_limit=300, bind=True, max_retries=5)
def deal_changed_task(self, deal_data: DealData):
    try:
        on_deal_changed(deal_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=5, soft_time_limit=300, bind=True, max_retries=5)
def add_lead_from_promoter_task(self, promoter_lead_data: PromoterLead):
    try:
        on_add_lead_from_promoter(promoter_lead_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(queue=f'{Config.task_queue}_push_leads', priority=2, soft_time_limit=300, bind=True, max_retries=5)
def push_amo_leads_task(self, number, pipeline_id, status_id, loss_reason_id, deal_name, tag):
    try:
        on_push_amo_leads(number, pipeline_id, status_id, loss_reason_id, deal_name, tag)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)



@app.task(priority=3, soft_time_limit=600, bind=True, max_retries=5)
def record_updated_task(self, task_data: RecordData):
    try:
        on_record_updated(task_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=0, soft_time_limit=300, bind=True, max_retries=5)
def create_and_save_task_task(self, lesson, contact_phone):
    try:
        create_and_save_task(lesson, contact_phone)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=6, soft_time_limit=300, bind=True, max_retries=5)
def wordpress_task(self, task_data: WordpressData):
    try:
        on_wordpress_task(task_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=1, soft_time_limit=600, bind=True, max_retries=5)
def qtickets_event_task(self, task_data: List[QticketsInfo]):
    try:
        on_qtickets_event(task_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(queue=f'{Config.task_queue}_ai_confirmation', priority=1, soft_time_limit=600, bind=True, max_retries=5)
def ai_confirmation_task(self, task_data: ConfirmationData):
    try:
        on_ai_confirmation(task_data)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print('test')
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(queue=f'{Config.task_queue}_send_templates', priority=8, bind=True, soft_time_limit=300, max_retries=5)
def send_template_task(self, templates: List[Template], lead_id: str):
    try:
        on_send_template_task(templates, lead_id)
    except SoftTimeLimitExceeded as e:
        try:
            self.retry(countdown=20)
        except MaxRetriesExceededError as max_retry_error:
            print('Достигнуто максимальное количество попыток для задачи send_template_task:', max_retry_error)
        print(e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(priority=0, soft_time_limit=300, bind=True, max_retries=5)
def refresh_tokens_task(self):
    try:
        tokens.default_token_manager.get_access_token()
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)


@app.task(bind=True, max_retries=5, soft_time_limit=300)
def set_init_code_task(self, code: str):
    try:
        tokens.default_token_manager.init(code=code)
    except SoftTimeLimitExceeded as e:
        print(e)
        raise self.retry(exc=e)
    except UnAuthorizedException as e:
        print(e)
        raise self.retry(exc=e)
    except AmoApiException as e:
        if "Connection aborted." in str(e):
            print("Обработка исключения AmoApiException: Connection aborted.")
            raise self.retry(exc=e)
        else:
            print(e)
            print("Обработка других исключений AmoApiException")
            raise self.retry(exc=e)
    except Exception as e:
        print(e)

@worker_process_init.connect
def init_worker_process(sender, **kwargs):
    init_tokens()





