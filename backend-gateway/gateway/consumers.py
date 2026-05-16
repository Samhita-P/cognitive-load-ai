import json
import logging
import httpx
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import CognitiveSession, CompressedTelemetry, CognitivePrediction

logger = logging.getLogger(__name__)

User = get_user_model()


@sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user = User.objects.get(id=access_token["user_id"])
        return user
    except Exception:
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
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        user = None
        if token:
            user = await get_user_from_token(token)
            if isinstance(user, AnonymousUser):
                await self.close()
                return
        elif getattr(settings, "ALLOW_DEV_INSECURE_TELEMETRY", False):
            user = await get_dev_bypass_user()
            logger.warning(
                "WebSocket telemetry connected without JWT (ALLOW_DEV_INSECURE_TELEMETRY). "
                "Disable this flag outside local development."
            )
        else:
            await self.close()
            return

        self.user = user
        self.session = await get_or_create_active_session(self.user)
        await self.accept()
        logger.info("WebSocket client connected: %s", self.user.username)

    async def disconnect(self, close_code):
        logger.info("WebSocket client disconnected with code: %s", close_code)
        try:
            from .session_manager import finalize_session
            await sync_to_async(finalize_session)(self.session.id, reason="normal_disconnect")
        except Exception as e:
            logger.error("Failed to finalize session on disconnect: %s", e)

    async def receive(self, text_data):
        payload = None
        try:
            payload = json.loads(text_data)

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "ack",
                        "batch_id": payload.get("batch_id"),
                        "status": "success",
                    }
                )
            )

            prediction = None
            ml_url = getattr(settings, "ML_SERVICE_URL", "http://127.0.0.1:8001/api/infer")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        ml_url,
                        json=payload,
                        timeout=2.0,
                    )
                    response.raise_for_status()
                    prediction = response.json()
            except httpx.TimeoutException:
                logger.warning(
                    "ML Service Timeout! Skipping prediction for batch %s",
                    (payload or {}).get("batch_id"),
                )
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "error_type": "InferenceTimeout",
                            "message": "Cognitive inference engine is taking too long. Skipping batch.",
                        }
                    )
                )
            except httpx.HTTPStatusError as e:
                logger.error("ML Service HTTP Error: %s", e.response.status_code)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "error_type": "InferenceError",
                            "message": "Cognitive inference engine failed to process batch.",
                        }
                    )
                )

            # Atomic save of telemetry, session update, and prediction (if successful)
            pred_pk = await save_telemetry_and_prediction(
                self.session,
                payload,
                prediction,
                batch_id=payload.get("batch_id"),
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

        except json.JSONDecodeError:
            logger.error("Invalid JSON received on websocket.")
        except Exception as e:
            logger.exception("Unexpected error in websocket: %s", str(e))
