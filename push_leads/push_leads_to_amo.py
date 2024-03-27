import requests
from aiohttp_jinja2 import render_template
from aiohttp import web
import asyncio

from amocrm.v2 import tokens, Pipeline

from config import Config
from worker import push_amo_leads_task



def get_loss_reasons():
    token = tokens.default_token_manager.get_access_token()
    api_call_headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(f'https://{Config.subdomain}.amocrm.ru/ajax/v3/loss_reasons', headers=api_call_headers,
                            verify=True)
    loss_reasons = response.json().get('_embedded', {}).get('items', [])
    return loss_reasons



def get_pipelines():
    pipelines = []
    _pipelines = Pipeline.objects.all()
    for _pipline in _pipelines:
        statuses = [{'id': status.id, 'name': status.name} for status in _pipline.statuses]
        pipelines.append({'id': _pipline.id, 'name': _pipline.name, 'statuses': statuses})
    return pipelines



async def push_leads(request):
    pipelines = get_pipelines()
    loss_reasons = get_loss_reasons()

    return render_template('push_leads/index.html', request, {
        'pipelines': pipelines,
        'loss_reasons': loss_reasons,
        'redirect_url': Config.redirect_url
    })


async def on_push_leads(request):
    data = await request.json()
    try:
        tasks = []
        for number in data['numbers']:
            task = push_amo_leads_task.delay(number, data['pipeline_id'], data['status_id'], data['loss_reason_id'],
                                             data['deal_name'], data['tag'])
            tasks.append(task)
        await asyncio.gather(*tasks)

        return web.json_response({"success": True})

    except Exception as e:
        return web.json_response({"error": str(e)})
