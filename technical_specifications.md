# Technical Specifications: Cognitive Load AI

This document details the critical technical foundations of the "realtime behavioral signal intelligence and adaptive computing platform."

## 1. MVP Boundaries

To ensure successful delivery, we draw a strict line between the Core MVP (Build Now) and Advanced/Future Scope.

### ✅ MUST BUILD (Core MVP - Next 30 Days)
*   **Telemetry pipeline** (Keyboard, Mouse, Session tracking)
*   **Event compression & batching**
*   **Sliding Session Windows** (30s)
*   **Feature engineering**
*   **Heuristic inference engine** (Rule-based scoring)
*   **Adaptive Intervention Engine** (Basic UI adaptations)
*   **Analytics Dashboard**
*   **Human-in-the-loop feedback popup**
*   **Basic Supervised ML model** (Random Forest trained on feedback)
*   **Explainability basics** (Feature importance)

### ⚠️ OPTIONAL / ADVANCED (Future Scope)
*   Behavioral drift detection
*   Cognitive recovery modeling
*   Risk escalation logic
*   Cognitive trend forecasting
*   Multimodal AI (Webcam, Eye tracking)

---

## 2. Session Lifecycle & Data Schema

Everything in the platform revolves around sessions. We define the explicit **Session Lifecycle** as follows:
*   **Session Start**: Triggered by the first interaction event.
*   **Session Active**: Continuous interaction events are being tracked.
*   **Session Pause**: Triggered if idle time > 5 minutes.
*   **Session End**: Triggered if inactivity > 30 mins OR browser/tab is closed.

### Database Schema (PostgreSQL/SQLite)

The backend database will act as the source of truth and Behavioral Feature Store.

*   `users` / `user_baselines`
*   `raw_events`: Older raw telemetry is automatically aggregated or deleted after 30 days (**Data Retention Policy**).
*   `feature_windows` (Behavioral Feature Store)
*   `predictions`: Includes a **`model_version`** field (e.g., `v1_heuristic`, `v2_random_forest`) to track inference generation.
*   `feedback_labels` (Human-in-the-Loop)
*   `interventions`

---

## 3. Event Compression & WebSocket Strategy

To prevent overloading the API Gateway, the frontend Edge Preprocessing layer compresses events before sending. 

### WebSocket Failure Strategy & Rate Limiting
*   If the WebSocket disconnects, compressed telemetry batches are temporarily queued locally and retransmitted after reconnection. Target reconnect time: **<3s**.
*   **Rate Limiting**: Maximum WebSocket payload frequency is capped per client (e.g., max 1 payload every 3s) to prevent accidental flooding or buggy performance spikes.

### Compression Details
*   **Batching Interval**: 5 seconds.
*   **Payload Structure (Sent every 5s)**:
    ```json
    {
      "session_id": "abc-123",
      "timestamp_start": 1678880000,
      "timestamp_end": 1678880005,
      "keyboard": { "keystrokes": 45, "backspaces": 3, "longest_pause_ms": 1200 },
      "mouse": { "distance_px": 850, "clicks": 2, "variance_x": 45.2, "variance_y": 12.8 },
      "session": { "idle_time_ms": 500, "tab_hidden": false }
    }
    ```

---

## 4. Feature Intelligence & Sliding Windows

Feature extraction uses a **Feature Window Scheduler** implementing **Sliding Windows** to ensure smoother predictions and realtime responsiveness. Every 5 seconds, a new 30-second rolling window is calculated (e.g., 0-30s, 5-35s, 10-40s).

### Core Features
*   **`typing_consistency`**: Variance in time intervals between keystrokes.
*   **`idle_ratio`**: `Total Idle Time / Window Duration`.
*   **`mouse_variance`**: Standard deviation of mouse directional changes.
*   **`error_rate`**: `Total Backspaces / Total Keystrokes`.
*   **`activity_density`**: Total interaction events per second over the 30s window.

---

## 5. Cognitive Scoring Logic & Inference Engine

Before supervised ML is trained, the inference engine uses rule-based logic to generate continuous scores. The target inference latency is **<200ms**.

### Explainability Output Structure
```json
{
  "state": "Fatigued",
  "confidence": 82,
  "top_factors": [ "High idle ratio (0.65)", "High error rate (18%)" ]
}
```

### Temporal Smoothing & State Transition Constraints
*   **Smoothing**: `current_score = (previous_score * 0.7) + (new_calculated_score * 0.3)`
*   **State Transition Constraints**: To simulate cognitive realism, states cannot jump radically. For example, `Focused → Fatigued` must transition through `Distracted` first.
*   **Persistence**: A state must be predicted for **3 consecutive sliding windows** before triggering UI changes.

### Intervention Priority & Cooldown Logic
*   **Priority System**: Only one active intervention is allowed at a time based on rank (Deep Work Mode < Break Suggestion < Burnout Warning) to prevent collisions.
*   **Cooldown**: No repeated interventions within **15 minutes** unless cognitive risk escalates significantly.

---

## 6. MLOps & Future Escalation Logic

### Model Retraining Strategy
*   **Retraining Trigger**: Automatically retrain every **500 newly labeled sessions**, or weekly.

### Cognitive Risk Escalation Logic
*   `risk_score = fatigue_duration × frequency × severity`
*   Escalates from **Low Risk** ➔ **Medium Risk** ➔ **High Risk**.

---

## 7. Implementation Targets

### Repository Structure
```
/cognitive-load-ai
  /frontend           # React, Vite, Tailwind, Edge Telemetry
  /backend-gateway    # Django, DRF, Channels, Redis, DB Auth
  /ml-service         # FastAPI, Pandas, Scikit-Learn, Feature Store
  /shared             # Shared schemas / documentation
```

### WebSocket Message Contracts
*   **Request Payloads**: `TelemetryBatch` (sent by frontend every 5s)
*   **Prediction Payloads**: `CognitiveStatePrediction` (sent by Gateway to frontend)
*   **Intervention Payloads**: `AdaptiveAction` (triggered by inference engine)
