from celery.signals import worker_ready
from celery.exceptions import SoftTimeLimitExceeded
from typing import List


from amo_auto_install import create_all
from monkey_patch import patch
from asgiref.sync import async_to_sync
from amocrm.v2 import tokens

from celery import Celery

from config import Config, save
from tasks.amo_contact_create import on_amo_contact_create
from tasks.amo_task_create import on_amo_task_create
from tasks.contact_edit import ContactData, on_contact_edit
from tasks.deal_changed import DealData, on_deal_changed
from tasks.record_updated import on_record_updated, RecordData
from tasks.wordpress import on_wordpress_task, WordpressData
from tasks.task_for_confirmation import create_and_save_task
from tasks.send_template import on_send_template_task
from tasks.on_qtickets_event import on_qtickets_event, QticketsInfo
from tasks.add_lead_from_promoter import on_add_lead_from_promoter, PromoterLead

patch()

app = Celery(broker=Config.broker_url)
app.conf.task_default_queue = Config.task_queue


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Обновляем токены каждый час.
    sender.add_periodic_task(3600, refresh_tokens_task.s(), name='Refresh tokens every hour')


@worker_ready.connect
def at_start(sender, **kwargs):
    print('calling worker_init_task')
    worker_init_task.delay()


@app.task
def amo_contact_create_task(id: int):
    async_to_sync(on_amo_contact_create)(id)


@app.task
def amo_task_create_task(id: int):
    on_amo_task_create(id)


@app.task
def contact_edit_task(contact_data: ContactData):
    on_contact_edit(contact_data)


@app.task
def deal_changed_task(deal_data: DealData):
    on_deal_changed(deal_data)


@app.task
def add_lead_from_promoter_task(promoter_lead_data: PromoterLead):
    on_add_lead_from_promoter(promoter_lead_data)


@app.task
def record_updated_task(task_data: RecordData):
    on_record_updated(task_data)


@app.task(soft_time_limit=300)
def create_and_save_task_task(lesson, contact_id):
    try:
        create_and_save_task(lesson, contact_id)
    except SoftTimeLimitExceeded as e:
        create_and_save_task_task.delay(lesson, contact_id)
        print(e)


@app.task
def wordpress_task(task_data: WordpressData):
    on_wordpress_task(task_data)


@app.task
def qtickets_event_task(task_data: List[QticketsInfo]):
    on_qtickets_event(task_data)


@app.task
def send_template_task(template_id: str, substitutions: list, lead_id: str):
    on_send_template_task(template_id, substitutions, lead_id)


@app.task
def refresh_tokens_task():
    tokens.default_token_manager.get_access_token()


@app.task
def set_init_code_task(code: str):
    try:
        tokens.default_token_manager.init(
            code=code)
    except Exception as e:
        print(e)


@app.task
def worker_init_task():
    if not tokens.default_token_manager._client_id:
        tokens.default_token_manager(
            client_id=Config.client_id,
            client_secret=Config.client_secret,
            subdomain=Config.subdomain,
            redirect_url=Config.redirect_url,
            storage=tokens.FileTokensStorage(directory_path=Config.token_directory)  # by default FileTokensStorage
        )

    token = ''
    try:
        token = tokens.default_token_manager.get_access_token()
    except:
        token = ''

    print('Token: ' + token)
    print('Code: ' + Config.code)

    if not token and Config.code:
        tokens.default_token_manager.init(
            code=Config.code)

    try:
        token = tokens.default_token_manager.get_access_token()
    except:
        token = ''

    print('Token after init: ' + token)

    if Config.primary_leads_pipeline_id == 0:
        create_all()
        save()

