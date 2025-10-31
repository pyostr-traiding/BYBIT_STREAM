import os

import redis
from dotenv import load_dotenv

load_dotenv()

# ===== НАСТРОЙКИ =====
USE_TESTNET = True
CHANNEL_TYPE = "linear"
RECONNECT_DELAY = 2  # секунды


# ===== REDIS =====
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD'),
    db=0,
)