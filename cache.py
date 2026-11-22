"""Redis cache. If Redis is down the app still works, just without caching."""
import json
import redis
from config import REDIS_URL, CACHE_TTL

_r = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=0.3)


def get(key):
    try:
        v = _r.get(key)
        return json.loads(v) if v else None
    except redis.RedisError:
        return None


def put(key, value):
    try:
        _r.setex(key, CACHE_TTL, json.dumps(value))
    except redis.RedisError:
        pass


def clear(uid=1):
    try:
        for k in _r.scan_iter(f"u{uid}:*"):
            _r.delete(k)
    except redis.RedisError:
        pass