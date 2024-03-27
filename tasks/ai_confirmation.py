from typing import TypedDict
from asgiref.sync import async_to_sync

from amocrm.v2 import Task
from joblib import load
import emoji

from entity_helpers.contact_search import find_contact_by_phone
from config import Config
from tasks.send_template import send_message_to_customer


class ConfirmationData(TypedDict):
    phoneNumber: str
    customerId: str
    customerText: str
    isPromo: bool

model = load('ai_model/model.joblib')
vectorizer = load('ai_model/vectorizer.joblib')


# Функция для классификации текста на основе vectorizer и model:
def classify_new_text(text):
    if text is None:
        return 1
    elif emoji.purely_emoji(text):# Если текст состоит только из эмодзи, возвращаем 1
        return 1
    else:
        # Иначе, продолжаем с классификацией текста
        text_demojized = emoji.demojize(text)
        vectorized_text = vectorizer.transform([text_demojized])
        probabilities = model.predict_proba(vectorized_text)
        return probabilities[0][0]


def on_ai_confirmation(data: ConfirmationData):
    probability = classify_new_text(data['customerText'])
    print(f'Пришел запрос от студента {data["customerId"]} с текстом {data["customerText"]}.\n '
          f'Вероятность: {probability}')
    if probability > 0.9:
        contact = find_contact_by_phone(data['phoneNumber'])
        async_to_sync(send_message_to_customer)("messagetemplate-f79c6634-3fca-48dd-8b66-48d47168cbc2",
                                                [], contact, data['phoneNumber'])
        tasks = contact.tasks
        for task in tasks:
            if task.task_type_id == Config.task_type_confirmation and not task.is_completed:
                result_text = "Подтвердил. Закрыто автоматически из интеграции"
                Task.objects.update(
                    task.id,
                    is_completed=True,
                    result={'text': result_text},
                    responsible_user=8772223 # TODO вынести в конфиг
                )





