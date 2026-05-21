import json
import logging
import httpx
import time
import collections
import redis
import uuid
from urllib.parse import parse_qs
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import CognitiveSession, CompressedTelemetry, CognitivePrediction, UserPrivacyProfile
from .ticket_store import WSTicketStore

logger = logging.getLogger(__name__)

User = get_user_model()


@sync_to_async
def get_user_from_ticket(ticket):
    try:
        payload = WSTicketStore.consume(ticket)
        
        if not payload:
            return AnonymousUser()
            
        if payload.get("purpose") != "ws_auth":
            return AnonymousUser()
            
        user = User.objects.get(id=payload.get("user_id"))
        return user
    except Exception as e:
        logger.error("Ticket validation error: %s", e)
        return AnonymousUser()


@sync_to_async
def get_dev_bypass_user():
    """
    Shared user for local/demo telemetry when ALLOW_DEV_INSECURE_TELEMETRY is on.
    Never use in production.
    """
    user, _ = User.objects.get_or_create(
        username="telemetry_dev",
        defaults={"email": "telemetry_dev@localhost"},
    )
    return user


@sync_to_async
def get_or_create_active_session(user):
    session, created = CognitiveSession.objects.get_or_create(
        user=user,
        ended_at__isnull=True,
        defaults={},
    )
    return session


@sync_to_async
def save_telemetry_and_prediction(session, payload, prediction=None, batch_id=None):
    """
    Groups telemetry save, session update, and prediction save into a single
    atomic transaction to prevent partial state corruption.
    """
    with transaction.atomic():
        from django.utils import timezone
        session.last_activity_at = timezone.now()
        session.save(update_fields=['last_activity_at'])
        
        CompressedTelemetry.objects.create(
            session=session,
            keyboard_data=payload.get("keyboard", {}),
            mouse_data=payload.get("mouse", {}),
            activity_data=payload.get("session", {}),
        )
        
        if prediction:
            bid = (batch_id or prediction.get("request_id") or "")[:64]
            obj = CognitivePrediction.objects.create(
                session=session,
                batch_id=bid,
                focus_score=float(prediction.get("focus_score", 0)),
                fatigue_score=float(prediction.get("fatigue_score", 0)),
                predicted_state=str(prediction.get("state", "Normal"))[:50],
                confidence=float(prediction.get("confidence", 0)),
                model_version=str(prediction.get("model_version", "v1_heuristic"))[:50],
                top_factors=prediction.get("top_factors") or [],
            )
            return obj.pk
        return None

class TelemetryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()

        logger.warning("RAW QUERY STRING: %s", query_string)

        query_params = parse_qs(query_string)
        ticket = query_params.get("ticket", [None])[0]

        logger.warning("PARSED TICKET: %s", ticket)

        user = None

        if ticket:
            user = await get_user_from_ticket(ticket)

            if isinstance(user, AnonymousUser) or user is None:
                logger.warning("INVALID TICKET")
                await self.close()
                return

        elif getattr(settings, "ALLOW_DEV_INSECURE_TELEMETRY", False):
            user = await get_dev_bypass_user()

            logger.warning(
                "WebSocket telemetry connected without ticket "
                "(ALLOW_DEV_INSECURE_TELEMETRY)"
            )

        else:
            logger.warning("WebSocket rejected: no ticket and dev bypass disabled")
            await self.close(code=4001)
            return

        self.user = user

        if not isinstance(self.user, AnonymousUser):
            profile_consent = await sync_to_async(
                lambda u: getattr(u, "privacy_profile", None)
                and u.privacy_profile.telemetry_consent
            )(self.user)

            if (
                not profile_consent
                and not getattr(settings, "ALLOW_DEV_INSECURE_TELEMETRY", False)
            ):
                logger.warning(
                    "User %s rejected WS connection due to lack of telemetry consent",
                    self.user.username,
                )
                await self.close(code=4003)
                return

            self.user_group_name = f"user_{self.user.id}"

            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name,
            )

        self.session = await get_or_create_active_session(self.user)
        self.connection_id = str(uuid.uuid4())

        self.max_connections = getattr(
            settings,
            "WS_MAX_CONNECTIONS_PER_USER",
            3,
        )

        try:
            redis_url = settings.CACHES["default"].get(
                "LOCATION",
                "redis://127.0.0.1:6379/0",
            )

            client = redis.from_url(redis_url)

            conn_key = f"ws_connections:{self.user.id}"

            client.sadd(conn_key, self.connection_id)
            client.expire(conn_key, 3600)

            if client.scard(conn_key) > self.max_connections:
                client.srem(conn_key, self.connection_id)

                logger.warning(
                    "[conn_id=%s] Max concurrent connections exceeded",
                    self.connection_id,
                )

                await self.close(code=1008)
                return

        except Exception as e:
            logger.error("Redis connection tracking failed: %s", e)
            await self.close(code=1011)
            return

        self.max_messages = getattr(
            settings,
            "WS_MAX_MESSAGES_PER_MIN",
            30,
        )

        self.message_times = collections.deque(
            maxlen=self.max_messages
        )

        self.last_sequence_number = -1
        self.inference_semaphore = asyncio.Semaphore(1)

        await self.accept()

        logger.info(
            "[conn_id=%s] WebSocket connected: %s",
            self.connection_id,
            self.user.username,
        )
        
    async def disconnect(self, close_code):
        logger.info(
            "[conn_id=%s] WebSocket disconnected with code: %s",
            getattr(self, "connection_id", "unknown"),
            close_code,
        )

        if hasattr(self, "user") and not isinstance(self.user, AnonymousUser):
            if hasattr(self, "user_group_name"):
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name,
                )

        if hasattr(self, "user") and hasattr(self, "connection_id"):
            try:
                redis_url = settings.CACHES["default"].get(
                    "LOCATION",
                    "redis://127.0.0.1:6379/0",
                )
                client = redis.from_url(redis_url)
                client.srem(
                    f"ws_connections:{self.user.id}",
                    self.connection_id,
                )
            except Exception as e:
                logger.error("Redis connection untracking failed: %s", e)

        if hasattr(self, "session") and self.session:
            try:
                from .session_manager import finalize_session
                await sync_to_async(finalize_session)(
                    self.session.id,
                    reason="normal_disconnect",
                )
            except Exception as e:
                logger.error(
                    "Failed to finalize session on disconnect: %s",
                    e,
                )

    async def receive(self, text_data):
        # 1. Privacy Revocation Check (Defense in Depth)
        if hasattr(self, 'user') and not isinstance(self.user, AnonymousUser):
            from django.core.cache import cache
            if cache.get(f"privacy_revoked_{self.user.id}"):
                logger.warning("[conn_id=%s] Privacy revoked (Cache hit). Dropping message.", self.connection_id)
                await self.close(code=4003)
                return
                
            consent = await sync_to_async(
                lambda u: getattr(u, 'privacy_profile', None) and u.privacy_profile.telemetry_consent
            )(self.user)
            
            if not consent:
                logger.warning("[conn_id=%s] Privacy revoked (DB fallback). Dropping message.", self.connection_id)
                await self.close(code=4003)
                return

        # Payload size cap (Default 50KB)
        max_payload_bytes = getattr(settings, "WS_MAX_PAYLOAD_BYTES", 51200)
        if len(text_data) > max_payload_bytes:
            logger.warning("Payload exceeded max size limit for user %s. Closing connection.", getattr(self.user, 'username', 'anonymous'))
            await self.close(code=1009)
            return

        # Per-connection rate limiting
        now = time.time()
        while self.message_times and self.message_times[0] < now - 60:
            self.message_times.popleft()
            
        if len(self.message_times) >= self.max_messages:
            logger.warning("Per-connection rate limit exceeded for user %s. Closing.", self.user.username)
            await self.close(code=1008)
            return
            
        self.message_times.append(now)

        # Global per-user rate limiting via Redis
        try:
            redis_url = settings.CACHES["default"].get("LOCATION", "redis://127.0.0.1:6379/0")
            client = redis.from_url(redis_url)
            
            # 1. Refresh active connection set TTL (heartbeat)
            if hasattr(self, 'user'):
                client.expire(f"ws_connections:{self.user.id}", 3600)
                
            # 2. Check global message rate limits
            rate_key = f"ws_rate:{self.user.id}"
            current_rate = client.incr(rate_key)
            if current_rate == 1:
                client.expire(rate_key, 60)
                
            if current_rate > self.max_messages * 2: # Global threshold (e.g., across 2 tabs)
                logger.warning("[conn_id=%s] Global rate limit exceeded for user %s. Closing.", self.connection_id, getattr(self.user, 'username', 'anonymous'))
                await self.close(code=1008)
                return
        except Exception as e:
            logger.error("Redis rate limit check failed: %s", e)
            await self.close(code=1011) # Fail closed for security
            return

        payload = None
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received on websocket.")
            return

        schema_version = payload.get("schema_version")
        if schema_version not in getattr(settings, "SUPPORTED_SCHEMA_VERSIONS", {"telemetry.v1"}):
            logger.warning("Unsupported schema version: %s", schema_version)
            await self.close(code=1003)
            return

        batch_id = payload.get("batch_id")
        if not batch_id:
            logger.warning("Missing batch_id in payload")
            return

        redis_url = settings.CACHES["default"].get("LOCATION", "redis://127.0.0.1:6379/0")
        client = redis.from_url(redis_url)
        dedupe_key = f"telemetry_seen:{self.user.id}:{self.session.id}:{batch_id}"
        if client.set(dedupe_key, 1, nx=True, ex=300) is None:
            logger.warning("[conn_id=%s] Dropping duplicate batch: %s", self.connection_id, batch_id)
            return

        sequence_number = payload.get("sequence_number")
        if sequence_number is not None:
            if hasattr(self, 'last_sequence_number'):
                if sequence_number <= self.last_sequence_number:
                    logger.warning("[conn_id=%s] Dropping stale batch: seq=%s, last_seq=%s", self.connection_id, sequence_number, self.last_sequence_number)
                    return
                elif sequence_number <= self.last_sequence_number + 10:
                    pass
                else:
                    logger.warning("[conn_id=%s] Massive sequence jump detected. last=%s, new=%s", self.connection_id, self.last_sequence_number, sequence_number)
            self.last_sequence_number = sequence_number

        trace_id = payload.pop("trace_id", str(uuid.uuid4()))

        if getattr(self, "inference_semaphore", None) and self.inference_semaphore.locked():
            logger.warning("[conn_id=%s] Inference busy. Dropping incoming batch (backpressure).", getattr(self, 'connection_id', ''))
            return

        async def _process_batch(payload_dict, trace_id_str):
            async with self.inference_semaphore:
                from .ml_client import MLClient
                try:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "ack",
                                "batch_id": payload_dict.get("batch_id"),
                                "status": "success",
                            }
                        )
                    )

                    prediction = await MLClient.predict(payload_dict, trace_id=trace_id_str)
                    
                    if prediction.get("status") == "degraded":
                        logger.warning("[conn_id=%s] ML service returned degraded fallback prediction.", getattr(self, 'connection_id', ''))

                    pred_pk = await save_telemetry_and_prediction(
                        self.session,
                        payload_dict,
                        prediction,
                        batch_id=payload_dict.get("batch_id"),
                    )

                    if prediction:
                        prediction["gateway_prediction_id"] = pred_pk
                        await self.send(
                            text_data=json.dumps(
                                {
                                    "type": "prediction",
                                    "payload": prediction,
                                }
                            )
                        )
                except Exception as e:
                    logger.exception("Unexpected error in background processing: %s", str(e))

        asyncio.create_task(_process_batch(payload, trace_id))

    async def force_disconnect(self, event):
        """
        Handler to forcefully disconnect the socket when consent is revoked.
        """
        logger.info("Forcibly disconnecting WebSocket for %s due to consent revocation.", self.user.username)
        await self.close(code=4003)

