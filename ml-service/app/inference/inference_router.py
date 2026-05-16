import logging

from app.inference.model_loader import is_model_ready
from app.inference.rf_engine import infer_rf
from app.inference.heuristic_engine import HeuristicEngine

logger = logging.getLogger(__name__)

def route_inference(session_id: str, features: dict) -> dict:
    """
    Routes the inference request to either RF or Heuristic engine.
    Returns a unified dictionary with the prediction results.
    """
    engine_features = dict(features) if features else {}
    
    if is_model_ready() and features:
        try:
            rf_out = infer_rf(features)
            
            result = {
                "state": rf_out["state"],
                "focus_score": rf_out["focus_score"],
                "fatigue_score": rf_out["fatigue_score"],
                "confidence": rf_out["confidence"],
                "top_factors": rf_out["top_factors"],
                "model_version": rf_out["model_version"],
                "model_source": "random_forest",
                "engine_features": engine_features,
                "feature_importances": rf_out["feature_importances"],
                "warnings": []
            }
            
            if result["confidence"] < 35.0:
                result["warnings"].append("low_confidence")
                
            return result
        except Exception as e:
            logger.error("RF Inference failed, falling back to heuristic: %s", e)
            # Fallthrough to heuristic

    # Fallback to Heuristic Engine
    state, focus, fatigue, confidence, top_factors = HeuristicEngine.infer_state(
        session_id=session_id,
        features=features,
    )
    
    return {
        "state": state,
        "focus_score": focus,
        "fatigue_score": fatigue,
        "confidence": confidence,
        "top_factors": top_factors,
        "model_version": "v1_heuristic",
        "model_source": "heuristic",
        "engine_features": engine_features,
        "feature_importances": None,
        "warnings": []
    }
