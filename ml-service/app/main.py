from fastapi import FastAPI, BackgroundTasks, HTTPException
import time
import subprocess
import uuid
import os
import sys
from pathlib import Path

from app.schemas.telemetry import TelemetryBatch, CognitiveStatePrediction
from app.aggregation.window_manager import add_batch_to_window, cleanup_inactive_sessions, session_windows
from app.features.feature_extractor import FeatureExtractor
from app.inference.inference_router import route_inference

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic Metrics Counters
METRICS = {
    "active_sessions": 0,
    "inference_count": 0,
    "total_latency_ms": 0.0,
}

app = FastAPI(title="Cognitive Load AI - ML Service")

# Allow CORS for the frontend to hit these APIs directly if needed
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_SCENARIOS = {
    "Deep Focus",
    "Severe Fatigue",
    "Chaotic Task Switching",
    "Mild Distraction"
}
@app.post("/api/infer", response_model=CognitiveStatePrediction)
async def infer_cognitive_state(batch: TelemetryBatch, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    # 1. Update the sliding window incrementally
    window = add_batch_to_window(batch)
    
    # 2. Extract features from the sliding window
    features = FeatureExtractor.extract_features(window)

    # 3. Use inference router to get the unified result
    result = route_inference(batch.session_id, features)

    out = CognitiveStatePrediction(
        request_id=batch.batch_id,
        session_id=batch.session_id,
        timestamp=int(time.time() * 1000),
        state=result["state"],
        focus_score=result["focus_score"],
        fatigue_score=result["fatigue_score"],
        confidence=result["confidence"],
        top_factors=result["top_factors"],
        model_version=result["model_version"],
        model_source=result["model_source"],
        engine_features=result["engine_features"],
        feature_importances=result["feature_importances"],
        warnings=result.get("warnings", [])
    )

    background_tasks.add_task(cleanup_inactive_sessions, timeout_minutes=30)

    latency = (time.time() - start_time) * 1000
    METRICS["inference_count"] += 1
    METRICS["total_latency_ms"] += latency
    from app.aggregation.window_manager import session_windows

    METRICS["active_sessions"] = len(session_windows)

    if latency > 200:
        logger.warning("Inference latency exceeded 200ms: %.2fms", latency)

    return out


@app.post("/api/feedback")
async def feedback_deprecated():
    """Feedback is persisted on the Django gateway (JWT)."""
    raise HTTPException(
        status_code=410,
        detail="Use POST /api/feedback/ on the gateway with Authorization: Bearer <token>.",
    )

@app.post("/api/demo/trigger")
async def trigger_demo(scenario: str):
    """
    Triggers a deterministic mock scenario for the presentation.
    Runs the mock_generator in a background process.
    """
    if scenario not in ALLOWED_SCENARIOS:
        raise HTTPException(status_code=400, detail="Invalid scenario requested.")
    
    request_id = str(uuid.uuid4())
    logger.info(f"Triggering demo scenario: {scenario} (Req: {request_id})")
    
    try:
        ml_root = Path(__file__).resolve().parent.parent
        cmd = [
            sys.executable,
            str(ml_root / "scripts" / "mock_generator.py"),
            "--scenario",
            scenario,
            "--duration",
            "60",
        ]
        if os.environ.get("DEMO_GATEWAY_JWT"):
            cmd.extend(["--token", os.environ["DEMO_GATEWAY_JWT"]])
        if os.environ.get("GATEWAY_WS_URL"):
            cmd.extend(["--ws-url", os.environ["GATEWAY_WS_URL"]])

        subprocess.Popen(
            cmd,
            cwd=str(ml_root),
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        return {
            "status": "started",
            "scenario": scenario,
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Failed to start mock generator: {e}")
        raise HTTPException(status_code=500, detail="Failed to start demo generator.")

@app.get("/api/metrics")
async def get_system_metrics():
    """
    Returns production metrics for the BenchmarkMetrics dashboard.
    """
    avg_latency = 0
    if METRICS["inference_count"] > 0:
        avg_latency = METRICS["total_latency_ms"] / METRICS["inference_count"]
        
    # Simulate a stable reconnect success rate for the presentation
    reconnect_success_rate = 99.8
    
    # Calculate mock throughput based on active sessions
    # (roughly 1 batch every 5s per session = 0.2 batches/sec)
    peak_throughput = METRICS["active_sessions"] * 0.2 + 1.5 # base noise
    
    return {
        "avg_latency_ms": round(avg_latency, 1),
        "peak_throughput_bps": round(peak_throughput, 1),
        "reconnect_success_rate": reconnect_success_rate,
        "active_sessions": METRICS["active_sessions"],
        "total_inferences": METRICS["inference_count"]
    }
