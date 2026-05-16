import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.inference.inference_router import route_inference
import json

test_features = {
    "idle_ratio": 0.15,
    "activity_density": 4.5,
    "error_rate": 0.02,
    "max_pause_ms": 600,
    "avg_mouse_variance": 25.0,
    "total_keystrokes": 55
}

result = route_inference("test_session_1", test_features)
print("--- RF Prediction (Focused simulation) ---")
print(json.dumps(result, indent=2))

test_features_distracted = {
    "idle_ratio": 0.5,
    "activity_density": 1.5,
    "error_rate": 0.1,
    "max_pause_ms": 4000,
    "avg_mouse_variance": 120.0,
    "total_keystrokes": 20
}

result_distracted = route_inference("test_session_2", test_features_distracted)
print("\n--- RF Prediction (Distracted simulation) ---")
print(json.dumps(result_distracted, indent=2))
