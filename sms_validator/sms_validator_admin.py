import aiohttp_jinja2
from aiohttp import web
import peewee as pw
from sms_validator.models import Lead
from config import Config


async def sms_validator_admin(request):

    return aiohttp_jinja2.render_template('sms_validator/admin.html', request, {'redirect_url': Config.redirect_url})


async def get_entities(model):
    try:
        entities = [entity.name for entity in model.select()]
        return web.json_response(entities)
    except pw.PeeweeException as e:
        return web.json_response({"error": str(e)})


async def add_entity(request, model):
    data = await request.post()
    try:
        if 'name' in data:
            model.create(name=data['name'])
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": f"Не предоставлено имя для {model.__name__}"})
    except pw.PeeweeException as e:
        return web.json_response({"error": str(e)})


async def edit_entity(request, model):
    data = await request.post()
    try:
        if 'oldName' in data and 'newName' in data:
            entity = model.get(model.name == data['oldName'])
            entity.name = data['newName']
            entity.save()
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": f"Не предоставлено старое или новое имя для {model.__name__}"})
    except pw.DoesNotExist:
        return web.json_response({"error": f"{model.__name__} не найден"})
    except pw.PeeweeException as e:
        return web.json_response({"error": str(e)})


async def delete_entity(request, model):
    data = await request.post()
    try:
        if 'name' in data:
            entity = model.get(model.name == data['name'])
            entity.delete_instance()
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": f"Не предоставлено имя для {model.__name__}"})
    except pw.DoesNotExist:
        return web.json_response({"error": f"{model.__name__} не найден"})
    except pw.PeeweeException as e:
        return web.json_response({"error": str(e)})


async def get_leads(request):
    try:
        leads = Lead.select().order_by(Lead.id.desc())
        leads_data = []
        for lead in leads:
            leads_data.append({
                "id": lead.id,
                "promoter": lead.promoter.name,
                "phone": lead.phone,
                "location": lead.location.name,
                "supervisor": lead.supervisor.name,
                "name": lead.name,
                "direction": lead.direction,
                "type": lead.type,
                "created_at": lead.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return web.json_response(leads_data)
    except Exception as e:
        return web.json_response({"error": str(e)})

