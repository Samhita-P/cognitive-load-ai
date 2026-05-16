import math
import logging
from typing import Any

from app.features.metric_keys import CLASS_SCORE_TABLE, TRAINING_FEATURE_KEYS
from app.inference.model_loader import get_model, get_metadata

logger = logging.getLogger(__name__)

def calculate_entropy_confidence(probs: list[float], num_classes: int) -> float:
    """
    Calculate confidence using normalized Shannon Entropy.
    entropy = -sum(p * log2(p) for p in probs if p > 0)
    max_entropy = log2(num_classes)
    normalized_entropy = entropy / max_entropy
    confidence = (1 - normalized_entropy) * 100
    """
    if num_classes <= 1:
        return 100.0
    
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    max_entropy = math.log2(num_classes)
    
    if max_entropy == 0:
        return 100.0
        
    normalized_entropy = entropy / max_entropy
    confidence = (1.0 - normalized_entropy) * 100.0
    return round(max(0.0, min(100.0, confidence)), 2)

def infer_rf(features: dict) -> dict:
    """
    Runs the RF prediction on the given features.
    Raises ValueError if model is not available or input is invalid.
    """
    clf = get_model()
    meta = get_metadata()
    
    if clf is None or meta is None:
        raise ValueError("RF model is not loaded.")

    names: list[str] = list(meta.get("features") or TRAINING_FEATURE_KEYS)
    classes: list[str] = list(meta.get("classes") or [])
    
    if not classes:
        raise ValueError("Classes metadata is missing.")

    row = [float(features.get(n) or 0.0) for n in names]

    proba = clf.predict_proba([row])[0].tolist()
    pred_idx = int(proba.index(max(proba)))
    state = str(classes[pred_idx]) if pred_idx < len(classes) else "Unknown"
    
    # Calculate confidence using Shannon Entropy
    confidence = float(calculate_entropy_confidence(proba, len(classes)))

    scores = CLASS_SCORE_TABLE.get(state, CLASS_SCORE_TABLE["Unknown"])
    focus_score = scores["focus_score"]
    fatigue_score = scores["fatigue_score"]

    imp_pairs = sorted(
        zip(names, clf.feature_importances_.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )
    top_factors = [f"{n} ({v:.3f})" for n, v in imp_pairs[:4]]
    feature_importances = {n: round(float(v), 4) for n, v in imp_pairs}

    return {
        "state": state,
        "focus_score": focus_score,
        "fatigue_score": fatigue_score,
        "confidence": confidence,
        "top_factors": top_factors or ["RF decision"],
        "feature_importances": feature_importances,
        "model_version": str(meta.get("model_version", "v2_random_forest")),
    }
