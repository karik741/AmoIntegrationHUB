import aiohttp

from config import Config


async def get_subscription(id_subscription):
    print(id_subscription)
    send_data = {
        'subscriptionId': f'subscription-{id_subscription}'
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(f"{Config.docrm_url}/api/SubscriptionApiExternal/Get", json=send_data)
        data = await response.json()

    print(data)
    subscription = {
        'subjects': [subject['name'] for subject in data['result']['allowedSubjects']],
        'programType': data['result']['programType'],
        'isIndividual': data['result']['isIndividual']
    }
    return subscription
