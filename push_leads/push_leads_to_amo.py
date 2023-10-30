from aiohttp_jinja2 import render_template
from aiohttp import web
import asyncio


from worker import push_amo_leads_task, get_loss_reasons_task, get_pipelines_task
from config import Config



async def push_leads(request):
    _pipelines = get_pipelines_task.delay()
    pipelines = _pipelines.get()

    _loss_reasons = get_loss_reasons_task.delay()
    loss_reasons = _loss_reasons.get()

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
