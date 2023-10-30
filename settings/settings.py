from aiohttp import web
from aiohttp_jinja2 import render_template
from config import Config, save


async def settings(request):
    return render_template('settings/index.html', request, {'config': Config, 'redirect_url': Config.redirect_url})


async def update_settings(request):
    data = await request.json()
    try:
        Config.settings_task_type_promo_retro_to_current_manager = \
            data['settings_task_type_promo_retro_to_current_manager']
        Config.settings_task_type_fullpay_to_current_manager = \
            data['settings_task_type_fullpay_to_current_manager']
        Config.settings_task_type_reregister_to_current_manager = \
            data['settings_task_type_reregister_to_current_manager']
        save()

        return web.json_response({"success": True})

    except Exception as e:
        return web.json_response({"error": str(e)})