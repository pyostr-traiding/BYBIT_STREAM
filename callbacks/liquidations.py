import json

from conf.settings import redis_client


def handle_liquidations(message):
    print('bybit_liquidations', message)
    redis_client.publish('stream:bybit_liquidations', json.dumps(message))
