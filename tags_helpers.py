import requests
from typing import Union, List


from entity_helpers.lead_custom_fields import Lead
from entity_helpers.contact_search import Contact
from config import Config


def create_tags(entity: Union[Lead, Contact], tags: List[str], access_token: str):
    entity_string = 'leads' if isinstance(entity, Lead) else 'contacts'
    api_call_headers = {'Authorization': 'Bearer ' + access_token}
    old_tags = [{'name': old_tag.name} for old_tag in entity.tags]
    new_tags = [{'name': new_tag} for new_tag in tags]
    tags = old_tags + new_tags
    request = [{
        "id": entity.id,
        "_embedded": {
            "tags": tags
        }
    }]
    requests.patch(f'https://{Config.subdomain}.amocrm.ru/api/v4/{entity_string}',
                   json=request, headers=api_call_headers, verify=True)