import typing
from datetime import datetime, timedelta

from amocrm.v2 import Task

from config import Config


def on_amo_task_create(id: int):
    task = typing.cast(Task, Task.objects.get(id))

    if Config.whitelist_enabled():
        return

    if task.task_type_id in [
        Config.task_type_cc_processing_site_value_id,
        Config.task_type_cc_promo_reregister_value_id,
        Config.task_type_cc_recall_value_id
    ]:
        task.responsible_user = Config.user_free_cc_tasks_holder_id
        task_complete_till = typing.cast(datetime, task.complete_till)
        if task_complete_till.hour == 23 and task_complete_till.minute == 59:
            task.complete_till = (task_complete_till + timedelta(days=1)).replace(hour=10, minute=0)
        task.save()
