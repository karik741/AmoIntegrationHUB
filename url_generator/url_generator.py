import json
from aiohttp import web
import urllib.parse
import aiohttp
from aiohttp_jinja2 import render_template
from config import Config


async def fetch_templates(session):
    response = await session.post(f'{Config.docrm_url}/api/MessageTemplateApiExternal/TemplateList')
    return await response.json()


async def templates_url_generator(request):
    async with aiohttp.ClientSession() as session:
        templates = await fetch_templates(session)
    return render_template('url_generator/templates.html', request,
                                          {'templates': templates, 'redirect_url': Config.redirect_url})


async def templates_fields(request):
    templates_ids = request.match_info['ids'].split('&')
    async with aiohttp.ClientSession() as session:
        templates = await fetch_templates(session)
    templates_dict = {template['id']: template for template in templates['messageTemplates']}
    matching_templates = [templates_dict[template_id] for template_id in templates_ids]

    return render_template('url_generator/templates_fields.html', request,
                                          {'templates': matching_templates, 'redirect_url': Config.redirect_url})


async def generate_link(request):
    data = await request.json()
    json_str = json.dumps(data)
    encoded_json_str = urllib.parse.quote_plus(json_str)
    link = f'{Config.redirect_url}/send_template?data={encoded_json_str}'

    return web.Response(text=link)
