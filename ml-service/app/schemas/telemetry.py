from pydantic import BaseModel, Field
from typing import List, Optional

class KeyboardTelemetry(BaseModel):
    keystrokes: int = Field(ge=0)
    backspaces: int = Field(ge=0)
    longest_pause_ms: int = Field(ge=0)

class MouseTelemetry(BaseModel):
    distance_px: float = Field(ge=0)
    clicks: int = Field(ge=0)
    variance_x: float = Field(ge=0)
    variance_y: float = Field(ge=0)

class SessionTelemetry(BaseModel):
    idle_time_ms: int = Field(ge=0)
    tab_hidden: bool
    user_baseline: Optional[dict] = None

class TelemetryBatch(BaseModel):
    batch_id: str
    session_id: str
    timestamp_start: int
    timestamp_end: int
    keyboard: KeyboardTelemetry
    mouse: MouseTelemetry
    session: SessionTelemetry

class CognitiveStatePrediction(BaseModel):
    request_id: str
    session_id: str
    timestamp: int
    state: str
    focus_score: float
    fatigue_score: float
    confidence: float
    probabilities: Optional[dict[str, float]] = None
    top_factors: List[str]
    model_version: str
    model_source: str = "heuristic"
    engine_features: dict = Field(default_factory=dict)
    feature_importances: Optional[dict[str, float]] = None
    warnings: List[str] = Field(default_factory=list)

class FeedbackLabel(BaseModel):
    session_id: str
    prediction_state: str
    confidence: float
    human_label: str
    timestamp: int
    features_snapshot: dict
