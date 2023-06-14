import typing
from typing import Iterable, Type

from amocrm.v2 import tokens, Contact, Lead, User, Pipeline, Status
from amocrm.v2.account import Account, AccountInteraction
from amocrm.v2.entity import custom_field
from amocrm.v2.interaction import GenericInteraction
from amocrm.v2.manager import Manager
from amocrm.v2.model import Model

client_id = ''
client_secret = ''
subdomain = ''
redirect_url = ''
code = ''
filename = ''

tokens.default_token_manager(
    client_id=client_id,
    client_secret=client_secret,
    subdomain=subdomain,
    redirect_url=redirect_url,
    storage=tokens.MemoryTokensStorage()
)

tokens.default_token_manager.init(code)


models = [
    {'name': 'контакта', 'model': Contact},
    {'name': 'лида', 'model': Lead},
]


def generate():
    with open(filename, 'w') as output:
        for model in models:
            output.write(f'Поля модели {model["name"]}\n')
            fields = get_fields_for(model["model"])
            for field in fields:
                output.write(f'{field.name}: {field.id}\n')
                if field.enums and field.type in (custom_field.MULTISELECT, custom_field.RADIOBUTTON, custom_field.SELECT):
                    output.write(f'    Значения:\n')
                    for enum in field.enums:
                        output.write(f'     {enum["value"]}: {enum["id"]}\n')
            output.write('\n\n')

        output.write(f'Пользователи:\n')
        users = [typing.cast(User, user) for user in User.objects.all()]
        for user in users:
            output.write(f'{user.name}: {user.id}, {"активен" if user.is_active else "неактивен"}\n')
        output.write('\n\n')

        output.write(f'Воронки:\n')
        pipelines = [typing.cast(Pipeline, pipeline) for pipeline in Pipeline.objects.all()]
        for pipeline in pipelines:
            output.write(f'{pipeline.name}: {pipeline.id}{", в архиве" if pipeline.is_archive else ""}\n')
            statuses = [typing.cast(Status, status) for status in pipeline.statuses]
            if len(statuses) > 0:
                output.write(f'    Статусы:\n')
                for status in statuses:
                    output.write(f'     {status.name}: {status.id}\n')
        output.write('\n\n')

        output.write(f'Типы задач:\n')
        account = AccountInteraction().get(include=['task_types'])
        task_types = Account(account).task_types
        for task_type in task_types:
            output.write(f'{task_type["name"]}: {task_type["id"]}\n')
        output.write('\n')


def get_fields_for(model: Type[Model]) -> Iterable[custom_field.CustomFieldModel]:
    return Manager(
        GenericInteraction(
            path=f"{model.objects._interaction.path}/custom_fields",
            field="custom_fields",
        ),
        model=custom_field.CustomFieldModel,
    ).all()


generate()
