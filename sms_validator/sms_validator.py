import aiohttp_jinja2
import random
import time
from aiohttp import web
from peewee import *

from sms_validator.smsc_api import SMSC
from sms_validator.models import Lead as ModelLead, Promoter, Supervisor, Location
from config import Config
from worker import add_lead_from_promoter_task


phone_numbers = {}
MAX_ATTEMPTS = 3
smsc = SMSC()
redirect_url = Config.redirect_url
# redirect_url = 'http://localhost:8093'


async def sms_validator(request):
    return aiohttp_jinja2.render_template('sms_validator/index.html', request, {'redirect_url': redirect_url})


async def send_sms(request):
    data = await request.post()
    phone_number = data['phone_number']
    code = random.randint(1000, 9999)

    if phone_number not in phone_numbers or int(time.time()) - phone_numbers[phone_number]['time_sent'] > 30:
        phone_numbers[phone_number] = {'code': code, 'attempts': 0, 'time_sent': int(time.time())}
        smsc.send_sms(phone_number, str(code), sender="sms")

    return aiohttp_jinja2.render_template('sms_validator/verify.html', request,
                                          {'phone_number': phone_number,
                                           'attempts': MAX_ATTEMPTS,
                                           'time_sent': phone_numbers[phone_number]['time_sent'],
                                           'redirect_url': redirect_url})


async def verify_code(request):
    data = await request.post()
    phone_number = data['phone_number']
    code = data['code']
    if phone_numbers[phone_number]['code'] == int(code):
        raise web.HTTPSeeOther(location=f'{redirect_url}/sms_validator/form/{phone_number}')
    else:
        phone_numbers[phone_number]['attempts'] += 1
        if phone_numbers[phone_number]['attempts'] >= MAX_ATTEMPTS:
            return web.HTTPSeeOther(location=f'{redirect_url}/sms_validator')
        return aiohttp_jinja2.render_template('sms_validator/verify.html', request,
                                              {'phone_number': phone_number,
                                               'attempts': MAX_ATTEMPTS - phone_numbers[phone_number]['attempts'],
                                               'time_sent': phone_numbers[phone_number]['time_sent'],
                                               'error': 'Неверный код, пожалуйста, попробуйте еще раз',
                                               'redirect_url': redirect_url})


async def form(request):
    return aiohttp_jinja2.render_template('sms_validator/form.html',
                                          request, {'phone_number': request.match_info['phone_number'],
                                                    'redirect_url': redirect_url})


async def submit_form(request):
    data = await request.post()

    try:
        promoter = Promoter.get(Promoter.name == data['promoter'])
        location = Location.get(Location.name == data['location'])
        supervisor = Supervisor.get(Supervisor.name == data['supervisor'])

        ModelLead.create(
            promoter=promoter,
            location=location,
            supervisor=supervisor,
            name=data['name'],
            direction=data['direction'],
            type='null',
            phone=data['phone_number']
        )
        simple_dict = {k: v for k, v in data.items()}
        add_lead_from_promoter_task.delay(simple_dict)
        return web.json_response({"success": True})

    except DoesNotExist:
        return web.json_response({"error": "One of the entities does not exist"})

    except Exception as e:
        return web.json_response({"error": str(e)})
