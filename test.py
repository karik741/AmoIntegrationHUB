import re

import emoji
from joblib import load

from config import Config
from amocrm.v2 import tokens
from amocrm.v2.entity.note import _Note
from entity_helpers.contact_search import find_contacts, Contact, CustomLinksInteraction
import requests
from amo_auto_install import create_lead_custom_fields


def init_worker_process():
    print('Initializing worker process')
    if not tokens.default_token_manager._client_id:
        tokens.default_token_manager(
            client_id=Config.client_id,
            client_secret=Config.client_secret,
            subdomain=Config.subdomain,
            redirect_url=Config.redirect_url,
            storage=tokens.FileTokensStorage(directory_path=Config.token_directory)
        )

    token = ''
    try:
        token = tokens.default_token_manager.get_access_token()
    except Exception as e:
        print(f'Error getting access token: {e}')
        token = ''

    print('Token: ' + token)
    print('Code: ' + Config.code)

    if not token and Config.code:
        tokens.default_token_manager.init(code=Config.code)
        try:
            token = tokens.default_token_manager.get_access_token()
        except Exception as e:
            print(f'Error getting access token after init: {e}')
            token = ''

    print('Token after init: ' + token)
    return token



model = load('ai_model/model.joblib')
vectorizer = load('ai_model/vectorizer.joblib')

def classify_new_text(text):
    if emoji.purely_emoji(text):
        # Если текст состоит только из эмодзи, возвращаем 1
        return 1
    else:
        # Иначе, продолжаем с классификацией текста
        text_demojized = emoji.demojize(text)
        vectorized_text = vectorizer.transform([text_demojized])
        probabilities = model.predict_proba(vectorized_text)
        return probabilities[0][0]

while True:
    text = input('Введите текст для классификации:')
    print(classify_new_text(text))

