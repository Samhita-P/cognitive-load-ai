from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

class PredictionTargets(BaseModel):
    focus: float = Field(..., ge=1.0, le=5.0)
    fatigue: float = Field(..., ge=1.0, le=5.0)
    workload: float = Field(..., ge=1.0, le=5.0)

class PredictionUncertainty(BaseModel):
    focus_interval: List[float] = Field(default_factory=list)
    fatigue_interval: List[float] = Field(default_factory=list)
    workload_interval: List[float] = Field(default_factory=list)
    heuristic_confidence: Optional[float] = None # For fallback logic

class PredictionResult(BaseModel):
    """
    Standard interface for all models (Heuristic and Supervised) 
    to enable clean Shadow Deployment logging.
    """
    predictions: PredictionTargets
    uncertainty: PredictionUncertainty
    model_version: str
    model_source: str # e.g. "heuristic", "rf_v1"
    inference_latency_ms: float = 0.0
    fallback_triggered: bool = False
    
class ShadowLogPayload(BaseModel):
    """
    The exact payload structure standardized for logging in Phase 3.
    """
    timestamp: str
    user_id: str
    session_id: str
    feature_schema_version: str
    input_hash: str
    
    heuristic_prediction: Dict[str, Any]
    ml_prediction: Dict[str, Any]
    fallback_triggered: bool
    model_version: str
