import threading
import time
from datetime import datetime, timezone

import redis
from flask import current_app


_memory_blocklist = {}
_memory_lock = threading.Lock()


def _storage_uri():
    return current_app.config.get("JWT_BLOCKLIST_STORAGE_URI") or current_app.config["RATELIMIT_STORAGE_URI"]


def _redis_client():
    uri = _storage_uri()
    if not uri or uri.startswith("memory://"):
        return None
    return redis.Redis.from_url(uri, socket_connect_timeout=2, socket_timeout=2)


def revoke_token(jti, expires_at):
    if not jti:
        return
    now = datetime.now(timezone.utc).timestamp()
    ttl = max(int(float(expires_at or now) - now), 1)
    client = _redis_client()
    if client is not None:
        client.setex(f"edutrack:jwt:revoked:{jti}", ttl, "1")
        return
    with _memory_lock:
        _memory_blocklist[jti] = time.time() + ttl


def is_token_revoked(jti):
    if not jti:
        return True
    client = _redis_client()
    if client is not None:
        try:
            return bool(client.exists(f"edutrack:jwt:revoked:{jti}"))
        except redis.RedisError:
            current_app.logger.exception("JWT blocklist storage is unavailable; rejecting token.")
            return True
    now = time.time()
    with _memory_lock:
        expired = [key for key, value in _memory_blocklist.items() if value <= now]
        for key in expired:
            _memory_blocklist.pop(key, None)
        return jti in _memory_blocklist
