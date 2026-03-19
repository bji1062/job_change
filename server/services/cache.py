import time

_cache = {}
DEFAULT_TTL = 3600  # 1 hour

def get(key: str):
    entry = _cache.get(key)
    if entry and time.time() < entry["exp"]:
        return entry["data"]
    return None

def set(key: str, data, ttl: int = DEFAULT_TTL):
    _cache[key] = {"data": data, "exp": time.time() + ttl}

def delete(key: str):
    _cache.pop(key, None)

def clear():
    _cache.clear()
