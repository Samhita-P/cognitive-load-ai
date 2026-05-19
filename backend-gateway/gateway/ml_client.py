import httpx
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class MLClient:
    """
    Async client for FastAPI ML service.

    Features:
    - Circuit Breaker (CLOSED / OPEN / HALF-OPEN)
    - Timeout protection
    - Graceful degraded fallback
    - Connection reuse
    """

    _breaker_state = "CLOSED"   # CLOSED, OPEN, HALF-OPEN
    _failure_count = 0
    _last_failure_time = 0

    DEFAULT_FAILURE_THRESHOLD = 5
    DEFAULT_OPEN_DURATION_SEC = 30
    DEFAULT_TIMEOUT_SEC = 5.0

    @classmethod
    def _get_open_duration(cls):
        return getattr(
            settings,
            "ML_CIRCUIT_OPEN_DURATION_SEC",
            cls.DEFAULT_OPEN_DURATION_SEC,
        )

    @classmethod
    def _get_failure_threshold(cls):
        return getattr(
            settings,
            "ML_CIRCUIT_FAILURE_THRESHOLD",
            cls.DEFAULT_FAILURE_THRESHOLD,
        )

    @classmethod
    def _get_timeout(cls):
        return getattr(
            settings,
            "ML_SERVICE_TIMEOUT",
            cls.DEFAULT_TIMEOUT_SEC,
        )

    @classmethod
    def _update_breaker_state(cls):
        """
        Move OPEN -> HALF-OPEN after cooldown expires.
        """
        if cls._breaker_state != "OPEN":
            return

        now = time.time()

        if now - cls._last_failure_time > cls._get_open_duration():
            cls._breaker_state = "HALF-OPEN"
            logger.info("ML circuit breaker moved to HALF-OPEN.")

    @classmethod
    def _record_failure(cls):
        cls._failure_count += 1
        cls._last_failure_time = time.time()

        if cls._breaker_state == "HALF-OPEN":
            cls._breaker_state = "OPEN"
            logger.warning("ML circuit breaker re-opened after HALF-OPEN failure.")
            return

        if (
            cls._breaker_state == "CLOSED"
            and cls._failure_count >= cls._get_failure_threshold()
        ):
            cls._breaker_state = "OPEN"
            logger.error(
                "ML circuit breaker OPENED for %s seconds.",
                cls._get_open_duration(),
            )

    @classmethod
    def _record_success(cls):
        cls._failure_count = 0

        if cls._breaker_state != "CLOSED":
            cls._breaker_state = "CLOSED"
            logger.info("ML circuit breaker CLOSED. Service healthy again.")

    @classmethod
    def _get_degraded_prediction(cls, payload):
        """
        Fallback response when ML service unavailable.
        """
        return {
            "status": "degraded",
            "batch_id": payload.get("batch_id", ""),
            "state": "Normal",
            "focus_score": 0.5,
            "fatigue_score": 0.5,
            "confidence": 0.0,
            "model_version": "fallback_degraded",
            "top_factors": [
                {
                    "feature": "circuit_breaker",
                    "importance": 1.0
                }
            ],
        }

    @classmethod
    async def predict(cls, payload, trace_id=None):
        """
        Send telemetry payload to ML service.
        Returns either:
        - healthy ML prediction
        - degraded fallback prediction
        """

        cls._update_breaker_state()

        if cls._breaker_state == "OPEN":
            logger.warning("ML service unavailable (OPEN breaker). Returning degraded response.")
            return cls._get_degraded_prediction(payload)

        ml_url = getattr(
            settings,
            "ML_SERVICE_URL",
            "http://127.0.0.1:8001/api/infer"
        )

        headers = {}

        if trace_id:
            headers["X-Trace-ID"] = trace_id

        try:
            timeout = httpx.Timeout(cls._get_timeout())

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    ml_url,
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()

                prediction = response.json()

                cls._record_success()

                return prediction

        except httpx.TimeoutException:
            logger.warning("ML service timeout.")
            cls._record_failure()
            return cls._get_degraded_prediction(payload)

        except httpx.HTTPStatusError as e:
            logger.error("ML service HTTP error: %s", e.response.status_code)

            if e.response.status_code >= 500:
                cls._record_failure()

            return cls._get_degraded_prediction(payload)

        except httpx.RequestError as e:
            logger.error("ML service connection error: %s", str(e))
            cls._record_failure()
            return cls._get_degraded_prediction(payload)

        except Exception as e:
            logger.exception("Unexpected ML client error: %s", str(e))
            cls._record_failure()
            return cls._get_degraded_prediction(payload)