import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    _metrics = {
        "active_sessions": 0,
        "inference_count": 0,
        "total_latency_ms": 0.0,
        "timeout_count": 0,
        "fallback_count": 0,
        "failure_count": 0,
    }

    @classmethod
    def increment_timeout(cls):
        cls._metrics["timeout_count"] += 1
        cls._metrics["fallback_count"] += 1

    @classmethod
    def increment_failure(cls):
        cls._metrics["failure_count"] += 1
        cls._metrics["fallback_count"] += 1

    @classmethod
    def record_inference(cls, latency_ms: float, active_sessions: int):
        cls._metrics["inference_count"] += 1
        cls._metrics["total_latency_ms"] += latency_ms
        cls._metrics["active_sessions"] = active_sessions

    @classmethod
    def get_metrics(cls) -> dict:
        return dict(cls._metrics)

