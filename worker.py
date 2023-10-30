from celery.signals import worker_process_init
from celery.exceptions import SoftTimeLimitExceeded, MaxRetriesExceededError
from typing import List
from celery import Celery
import requests


from amo_auto_install import create_all
from monkey_patch import patch
from asgiref.sync import async_to_sync
from amocrm.v2 import tokens, Pipeline


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

patch()

app = Celery(broker=Config.broker_url, backend='rpc://')
app.conf.task_default_queue = Config.task_queue


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Обновляем токены каждый час.
    sender.add_periodic_task(3600, refresh_tokens_task.s(), name='Refresh tokens every hour')


@app.task(queue=f'{Config.task_queue}_contacts_create', priority=1, soft_time_limit=300)
def amo_contact_create_task(id: int):
    try:
        async_to_sync(on_amo_contact_task)(id)
    except SoftTimeLimitExceeded as e:
        amo_contact_create_task.delay(id)
        print(e)


@app.task(queue=f'{Config.task_queue}_contacts_update', priority=2, soft_time_limit=300)
def amo_contact_update_task(id: int):
    try:
        async_to_sync(on_amo_contact_task)(id)
    except SoftTimeLimitExceeded as e:
        amo_contact_update_task.delay(id)
        print(e)


@app.task(queue=f'{Config.task_queue}_contacts_update', priority=2, soft_time_limit=300)
def contact_edit_task(contact_data: ContactData):
    try:
        on_contact_edit(contact_data)
    except SoftTimeLimitExceeded as e:
        contact_edit_task.delay(contact_data)
        print(e)


@app.task(priority=6, soft_time_limit=300)
def deal_changed_task(deal_data: DealData):
    try:
        on_deal_changed(deal_data)
    except SoftTimeLimitExceeded as e:
        deal_changed_task.delay(deal_data)
        print(e)


@app.task(priority=5, soft_time_limit=300)
def add_lead_from_promoter_task(promoter_lead_data: PromoterLead):
    try:
        on_add_lead_from_promoter(promoter_lead_data)
    except SoftTimeLimitExceeded as e:
        add_lead_from_promoter_task.delay(promoter_lead_data)
        print(e)


@app.task(queue=f'{Config.task_queue}_push_leads', priority=11, soft_time_limit=300)
def push_amo_leads_task(number, pipeline_id, status_id, loss_reason_id, deal_name, tag):
    try:
        on_push_amo_leads(number, pipeline_id, status_id, loss_reason_id, deal_name, tag)

    except SoftTimeLimitExceeded as e:
        push_amo_leads_task.delay(number)
        print(e)

    except Exception as e:
        print(e)


@app.task(priority=0)
def get_pipelines_task():
    pipelines = []
    _pipelines = Pipeline.objects.all()
    for _pipline in _pipelines:
        statuses = [{'id': status.id, 'name': status.name} for status in _pipline.statuses]
        pipelines.append({'id': _pipline.id, 'name': _pipline.name, 'statuses': statuses})
    return pipelines


@app.task(priority=0)
def get_loss_reasons_task():
    token = tokens.default_token_manager.get_access_token()
    api_call_headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(f'https://{Config.subdomain}.amocrm.ru/ajax/v3/loss_reasons', headers=api_call_headers,
                            verify=True)
    loss_reasons = response.json().get('_embedded', {}).get('items', [])
    return loss_reasons


@app.task(priority=7, soft_time_limit=300)
def record_updated_task(task_data: RecordData):
    try:
        on_record_updated(task_data)
    except SoftTimeLimitExceeded as e:
        record_updated_task.delay(task_data)
        print(e)


@app.task(priority=10, soft_time_limit=300)
def create_and_save_task_task(lesson, contact_id):
    try:
        create_and_save_task(lesson, contact_id)
    except SoftTimeLimitExceeded as e:
        create_and_save_task_task.delay(lesson, contact_id)
        print(e)


@app.task(priority=4, soft_time_limit=300)
def wordpress_task(task_data: WordpressData):
    try:
        on_wordpress_task(task_data)
    except SoftTimeLimitExceeded as e:
        wordpress_task.delay(task_data)
        print(e)


@app.task(priority=9, soft_time_limit=300)
def qtickets_event_task(task_data: List[QticketsInfo]):
    try:
        on_qtickets_event(task_data)
    except SoftTimeLimitExceeded as e:
        qtickets_event_task.delay(task_data)
        print(e)


@app.task(queue=f'{Config.task_queue}_send_templates', priority=3, bind=True, soft_time_limit=300, max_retries=5)
def send_template_task(self, templates: List[Template], lead_id: str):
    try:
        on_send_template_task(templates, lead_id)
    except SoftTimeLimitExceeded as e:
        try:
            self.retry(countdown=20)
        except MaxRetriesExceededError as max_retry_error:
            print('Достигнуто максимальное количество попыток для задачи send_template_task:', max_retry_error)
        print(e)


@app.task(priority=0, soft_time_limit=300)
def refresh_tokens_task():
    try:
        tokens.default_token_manager.get_access_token()
    except SoftTimeLimitExceeded as e:
        refresh_tokens_task.delay()
        print(e)


@app.task
def set_init_code_task(code: str):
    try:
        tokens.default_token_manager.init(code=code)
    except Exception as e:
        print(e)


@worker_process_init.connect
def init_worker_process(sender, **kwargs):
    print('Initializing worker process')

    if not tokens.default_token_manager._client_id:
        tokens.default_token_manager(
            client_id=Config.client_id,
            client_secret=Config.client_secret,
            subdomain=Config.subdomain,
            redirect_url=Config.redirect_url,
            storage=tokens.FileTokensStorage(directory_path=Config.token_directory)
        )

    token = ''
    try:
        token = tokens.default_token_manager.get_access_token()
    except Exception as e:
        print(f'Error getting access token: {e}')
        token = ''

    print('Token: ' + token)
    print('Code: ' + Config.code)

    if not token and Config.code:
        tokens.default_token_manager.init(code=Config.code)
        try:
            token = tokens.default_token_manager.get_access_token()
        except Exception as e:
            print(f'Error getting access token after init: {e}')
            token = ''

    print('Token after init: ' + token)

    if Config.primary_leads_pipeline_id == 0:
        create_all()
        save()

