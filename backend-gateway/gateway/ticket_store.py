import json
import logging
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

class WSTicketStore:
    """
    Encapsulates WebSocket ticket storage and atomic consumption.
    Uses raw Redis to ensure GETDEL support and avoids Django cache prefix drift
    by bypassing the cache abstraction entirely for these specific ephemeral keys.
    """
    
    @staticmethod
    def _get_redis_client():
        redis_url = settings.CACHES["default"].get("LOCATION", "redis://127.0.0.1:6379/0")
        return redis.from_url(redis_url)

    @staticmethod
    def _get_key(ticket: str) -> str:
        return f"ws_ticket_store:{ticket}"

    @classmethod
    def issue(cls, ticket: str, payload: dict, ttl: int = 60):
        client = cls._get_redis_client()
        key = cls._get_key(ticket)
        client.setex(key, ttl, json.dumps(payload))

    @classmethod
    def consume(cls, ticket: str) -> dict | None:
        try:
            client = cls._get_redis_client()
            key = cls._get_key(ticket)
            raw_payload = client.getdel(key)
            if raw_payload:
                return json.loads(raw_payload)
            return None
        except Exception as e:
            logger.error("Error consuming WS ticket: %s", e)
            return None
