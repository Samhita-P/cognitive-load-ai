import httpx
import logging
from django.conf import settings
import time
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class MLClient:
    """
    Client for interacting with the FastAPI ML service.
    Implements a Circuit Breaker pattern to protect the Gateway from cascading failures
    when the ML service is saturated, timing out, or unavailable.
    """
    
    _breaker_state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
    _failure_count = 0
    _last_failure_time = 0
    
    # Policy Configurations
    FAILURE_THRESHOLD = 5
    OPEN_DURATION_SEC = 30
    TIMEOUT_SEC = 2.0

    @classmethod
    def _update_breaker_state(cls):
        now = time.time()
        if cls._breaker_state == "OPEN":
            if now - cls._last_failure_time > cls._OPEN_DURATION_SEC():
                cls._breaker_state = "HALF-OPEN"
                logger.info("ML Service Circuit Breaker moving to HALF-OPEN state.")

    @classmethod
    def _OPEN_DURATION_SEC(cls):
        return getattr(settings, "ML_CIRCUIT_OPEN_DURATION_SEC", cls.OPEN_DURATION_SEC)
    
    @classmethod
    def _FAILURE_THRESHOLD(cls):
        return getattr(settings, "ML_CIRCUIT_FAILURE_THRESHOLD", cls.FAILURE_THRESHOLD)

    @classmethod
    def _record_failure(cls):
        cls._failure_count += 1
        cls._last_failure_time = time.time()
        if cls._failure_count >= cls._FAILURE_THRESHOLD() and cls._breaker_state == "CLOSED":
            cls._breaker_state = "OPEN"
            logger.error("ML Service Circuit Breaker OPENED. Fast-failing for %d seconds.", cls._OPEN_DURATION_SEC())

    @classmethod
    def _record_success(cls):
        cls._failure_count = 0
        if cls._breaker_state != "CLOSED":
            cls._breaker_state = "CLOSED"
            logger.info("ML Service Circuit Breaker CLOSED. Service restored.")

    @classmethod
    def _get_degraded_prediction(cls, payload):
        """Fallback prediction when the circuit is open or times out."""
        return {
            "status": "degraded",
            "batch_id": payload.get("batch_id", ""),
            "state": "Normal", # Default fallback
            "focus_score": 0.5,
            "fatigue_score": 0.5,
            "confidence": 0.0,
            "model_version": "fallback_degraded",
            "top_factors": [{"feature": "circuit_breaker", "importance": 1.0}]
        }

    @classmethod
    async def predict(cls, payload, trace_id=None):
        """
        Asynchronously sends telemetry to ML service.
        Returns prediction dict (healthy or degraded).
        """
        cls._update_breaker_state()

        if cls._breaker_state == "OPEN":
            return cls._get_degraded_prediction(payload)

        ml_url = getattr(settings, "ML_SERVICE_URL", "http://127.0.0.1:8001/api/infer")
        
        headers = {}
        if trace_id:
            headers["X-Trace-ID"] = trace_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ml_url,
                    json=payload,
                    headers=headers,
                    timeout=getattr(settings, "ML_SERVICE_TIMEOUT", cls.TIMEOUT_SEC),
                )
                response.raise_for_status()
                prediction = response.json()
                
                cls._record_success()
                return prediction

        except httpx.TimeoutException:
            logger.warning("ML Service Timeout! Circuit failure recorded.")
            cls._record_failure()
            return cls._get_degraded_prediction(payload)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                logger.error("ML Service HTTP 500+ Error: %s", e.response.status_code)
                cls._record_failure()
            return cls._get_degraded_prediction(payload)
            
        except httpx.RequestError as e:
            logger.error("ML Service Connection Error: %s", str(e))
            cls._record_failure()
            return cls._get_degraded_prediction(payload)
