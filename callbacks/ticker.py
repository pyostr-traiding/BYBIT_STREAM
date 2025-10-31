import json

from conf.settings import redis_client


def handle_ticker(message):
    redis_client.publish('stream:bybit_ticker', json.dumps(message))
