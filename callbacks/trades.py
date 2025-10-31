import json

from conf.settings import redis_client


def handle_trades(message):
    redis_client.publish('stream:bybit_trades', json.dumps(message))
