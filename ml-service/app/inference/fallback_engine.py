import logging

logger = logging.getLogger(__name__)

class FallbackEngine:
    @staticmethod
    def timeout_prediction(session_id: str, request_id: str = "fallback"):
        """
        Returns a safe default prediction when the ML pipeline times out
        or the inference threadpool becomes saturated.
        """
        logger.warning(f"Inference timeout/saturation for session {session_id}. Falling back to default.")
        return {
            "state": "Unknown",
            "focus_score": 50.0,
            "fatigue_score": 0.0,
            "confidence": 10.0,
            "top_factors": ["Timeout fallback"],
            "model_version": "fallback_v1",
            "model_source": "timeout_fallback",
            "engine_features": {},
            "feature_importances": None,
            "warnings": ["inference_timeout"]
        }
