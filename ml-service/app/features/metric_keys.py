"""Ordered feature keys used for RF training and inference (must stay aligned)."""

TRAINING_FEATURE_KEYS = [
    "idle_ratio",
    "activity_density",
    "error_rate",
    "max_pause_ms",
    "avg_mouse_variance",
    "total_keystrokes",
]

# Score hints for UI when using classifier-only outputs (no regression head).
CLASS_SCORE_TABLE = {
    "Focused": {"focus_score": 82.0, "fatigue_score": 18.0},
    "Normal": {"focus_score": 55.0, "fatigue_score": 35.0},
    "Distracted": {"focus_score": 42.0, "fatigue_score": 48.0},
    "Fatigued": {"focus_score": 32.0, "fatigue_score": 78.0},
    "Overloaded": {"focus_score": 25.0, "fatigue_score": 85.0},
    "Unknown": {"focus_score": 50.0, "fatigue_score": 40.0},
}
