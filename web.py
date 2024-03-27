from typing import List
from aiohttp import web
from multidict import MultiDictProxy
from aiohttp_jinja2 import setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
import sys
import json
import urllib.parse
import typing
from datetime import datetime, timedelta
import asyncio


from config import Config
from worker import amo_contact_create_task, deal_changed_task, record_updated_task, contact_edit_task, \
                   set_init_code_task, wordpress_task, send_template_task, qtickets_event_task, \
                   amo_contact_update_task, contact_edit_from_hf_task, ai_confirmation_task
from tasks.contact_edit import ContactData
from tasks.deal_changed import DealData
from tasks.record_updated import RecordData
from tasks.lessons_updated import LessonsData, on_lessons_updated
from tasks.wordpress import WordpressData
from tasks.on_qtickets_event import QticketsInfo
from url_generator.url_generator import templates_url_generator, templates_fields, generate_link
from sms_validator.sms_validator import sms_validator, send_sms, verify_code, form, submit_form
from sms_validator.sms_validator_admin import sms_validator_admin, get_entities, add_entity, edit_entity, \
    delete_entity, get_leads
from sms_validator.models import Promoter, Supervisor, Location
from push_leads.push_leads_to_amo import push_leads, on_push_leads
from settings.settings import settings, update_settings
from entity_helpers.amo_init import init_tokens

app = web.Application()
redirect_url = Config.redirect_url
# redirect_url = 'http://localhost:8093'

logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

last_call = {"phone": None, "date": datetime.now()}

# Парсит айдишники из невероятного способа передачи вебхука из амо
def get_ids(body: MultiDictProxy[str | bytes], entity_type: str, action_type: str):
    counter = 0
    result = []
    while True:
        key = f'{entity_type}[{action_type}][{counter}][id]'
        if key in body:
            id = body[key]
            result.append(id)
            counter = counter + 1
        else:
            return result


def get_lead_id(body: MultiDictProxy[str | bytes]):
    if 'leads[status][0][id]' in body:
        return body['leads[status][0][id]']
    else:
        return body['leads[add][0][id]']


async def amo_callback(request: web.Request):
    body = await request.post()

    contacts_creations = get_ids(body, 'contacts', 'add')
    for item in contacts_creations:
        amo_contact_create_task.delay(item)

    contacts_updates = get_ids(body, 'contacts', 'update')
    for item in contacts_updates:
        amo_contact_update_task.delay(item)

    return web.Response(status=200)


async def deal_changed(request: web.Request):
    body = await request.json()
    deal_changed_task.delay(typing.cast(DealData, body))
    return web.json_response({"result": True, "error": None})


async def record_updated(request: web.Request):
    body = await request.json()
    record_updated_task.delay(typing.cast(RecordData, body))
    return web.json_response({"result": True, "error": None})


async def lessons_updated(request: web.Request):
    body = await request.json()
    on_lessons_updated(typing.cast(LessonsData, body))

    return web.json_response({"result": True, "error": None})


async def wordpress_callback(request: web.Request):
    body = await request.json()
    wordpress_task.delay(typing.cast(WordpressData, body))
    return web.json_response({"result": True, "error": None})


async def qtickets_event(request: web.Request):
    body = await request.json()
    qtickets_event_task.delay(typing.cast(List[QticketsInfo], body))
    return web.json_response({"result": True, "error": None})


async def handle_duplicate(phone, body):
    # Ждем 3 секунды
    await asyncio.sleep(5)
    # Повторно вызываем функцию обработки
    await contact_edit_internal(phone, body)


async def contact_edit_internal(phone, body):
    global last_call
    current_time = datetime.now()

    if phone == last_call["phone"] and current_time - last_call["date"] < timedelta(seconds=1):
        # Запускаем функцию для обработки дубликата
        asyncio.create_task(handle_duplicate(phone, body))
        return

    last_call["phone"] = phone
    last_call["date"] = current_time

    # Основная логика обработки запроса
    if body['metadata'] == "isUpdatedFromJob":
        contact_edit_from_hf_task.delay(typing.cast(ContactData, body))
    else:
        contact_edit_task.delay(typing.cast(ContactData, body))


async def contact_edit(request: web.Request):
    body = await request.json()
    phone = body[0]['phone']
    await contact_edit_internal(phone, body[0])
    return web.json_response({"result": [True], "error": [""]})


async def set_code(request: web.Request):
    code = request.query['code']
    set_init_code_task.delay(code)
    return web.json_response({"result": [True]})


async def send_template(request: web.Request):
    logger.info('Принят запрос')
    body = await request.post()
    data = request.query.get('data', '')
    data = urllib.parse.unquote_plus(data)
    templates = json.loads(data)
    lead_id = get_lead_id(body)
    logger.info(f'Lead id: {lead_id}; Ссылка: {data}')
    send_template_task.delay(templates, lead_id)
    return web.Response(status=200)


async def ai_confirmation(request: web.Request):
    logger.info('запрос')
    body = await request.json()
    logger.info(body)
    ai_confirmation_task.delay(body)
    return web.Response(status=200)


async def check_access(request: web.Request):
    return web.Response(status=200)


setup_jinja2(app, loader=FileSystemLoader('templates'))
app.router.add_static(f'/static/', path='static', name='static')
app.add_routes([web.post('/amo_callback', amo_callback)])
app.add_routes([web.post('/amo/set_code', set_code)])
app.add_routes([web.post('/customer/updated', contact_edit)])
app.add_routes([web.post('/subscription/updated', deal_changed)])
app.add_routes([web.post('/lesson/record_updated', record_updated)])
app.add_routes([web.post('/lessons/updated', lessons_updated)])
app.add_routes([web.post('/wordpress_callback', wordpress_callback)])
app.add_routes([web.post('/send_template', send_template)])
app.add_routes([web.post('/customer/qtickets_event', qtickets_event)])

app.add_routes([web.get('/templates_url_generator', templates_url_generator)])
app.add_routes([web.get('/templates/{ids}', templates_fields)])
app.add_routes([web.post('/generate_link', generate_link)])

app.add_routes([web.get('/sms_validator', sms_validator)])
app.add_routes([web.get('/sms_validator/form/{phone_number}', form)])
app.add_routes([web.post('/sms_validator/send_sms', send_sms)])
app.add_routes([web.post('/sms_validator/verify_code', verify_code)])
app.add_routes([web.post('/sms_validator/submit_form', submit_form)])

app.add_routes([web.get('/sms_validator/b7f6ad2b-0bcc-488c-865b-8c05e01af7c3', sms_validator_admin)])
app.add_routes([web.get('/sms_validator/api/get_supervisors', lambda request: get_entities(Supervisor))])
app.add_routes([web.get('/sms_validator/api/get_locations', lambda request: get_entities(Location))])
app.add_routes([web.get('/sms_validator/api/get_promoters', lambda request: get_entities(Promoter))])
app.add_routes([web.get('/sms_validator/api/get_leads', get_leads)])

app.add_routes([web.post('/sms_validator/api/add_supervisor', lambda request: add_entity(request, Supervisor))])
app.add_routes([web.post('/sms_validator/api/add_promoter', lambda request: add_entity(request, Promoter))])
app.add_routes([web.post('/sms_validator/api/add_location', lambda request: add_entity(request, Location))])

app.add_routes([web.post('/sms_validator/api/edit_supervisor', lambda request: edit_entity(request, Supervisor))])
app.add_routes([web.post('/sms_validator/api/edit_promoter', lambda request: edit_entity(request, Promoter))])
app.add_routes([web.post('/sms_validator/api/edit_location', lambda request: edit_entity(request, Location))])

app.add_routes([web.post('/sms_validator/api/delete_supervisor', lambda request: delete_entity(request, Supervisor))])
app.add_routes([web.post('/sms_validator/api/delete_promoter', lambda request: delete_entity(request, Promoter))])
app.add_routes([web.post('/sms_validator/api/delete_location', lambda request: delete_entity(request, Location))])

app.add_routes([web.get('/push_leads', push_leads)])
app.add_routes([web.post('/push_leads/api/send', on_push_leads)])

app.add_routes([web.post('/message/accept_lesson', ai_confirmation)])

app.add_routes([web.get('/settings', settings)])
app.add_routes([web.post('/settings/api/submit', update_settings)])

app.add_routes([web.get('/check_access', check_access)])

init_tokens()
web.run_app(app, port=Config.web_port)