import json

from conf.settings import redis_client


def handle_orderbook(message):
    redis_client.publish('stream:bybit_orderbook', json.dumps(message))
