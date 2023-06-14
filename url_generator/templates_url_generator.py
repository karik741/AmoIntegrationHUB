import aiohttp
import aiohttp_jinja2
from aiohttp import web
from config import Config


async def fetch_templates(session):
    response = await session.post(f'{Config.docrm_url}/api/MessageTemplateApiExternal/TemplateList')
    return await response.json()


async def templates_url_generator(request):
    async with aiohttp.ClientSession() as session:
        templates = await fetch_templates(session)
    return aiohttp_jinja2.render_template('url_generator/templates.html', request,
                                          {'templates': templates, 'redirect_url': Config.redirect_url})


async def template_form(request):
    template_id = request.match_info['id']
    async with aiohttp.ClientSession() as session:
        templates = await fetch_templates(session)
    for template in templates['messageTemplates']:
        if template['id'] == template_id:
            selected_template = template
            break
    else:
        raise web.HTTPNotFound(text="Шаблон не найден")

    return aiohttp_jinja2.render_template('url_generator/template_form.html', request,
                                          {'template': selected_template, 'redirect_url': Config.redirect_url})


async def generate_link(request):
    template_id = request.match_info['id']
    substitutions = request.query
    link = f'{Config.redirect_url}/send_template/{template_id}/' \
           f'{"&".join(substitutions.values()) if substitutions else "none"}'
    return web.Response(text=link)
