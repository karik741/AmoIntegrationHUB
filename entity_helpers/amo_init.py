from amocrm.v2 import tokens

from config import Config


def init_tokens():
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