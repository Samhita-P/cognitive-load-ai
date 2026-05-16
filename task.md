# Implementation Tasks: Cognitive Load AI

This task list tracks the execution of the Core MVP as outlined in the Technical Specifications.

## Week 1: Infrastructure + WebSocket Pipeline
- `[ ]` **Repository Structure**: Initialize `/shared`, `/frontend`, `/backend-gateway`, `/ml-service`
  - *Done When: `npm run dev`, `runserver`, and `uvicorn` all launch successfully.*
- `[ ]` **Environment Variables**: Setup `.env` and `.env.example` across all services.
- `[ ]` **API Validation Layer**: Define DRF serializers and Pydantic models for `TelemetryBatch`.
  - *Done When: Invalid payloads are rejected with 400 Bad Request.*
- `[ ]` **WebSocket Message Contracts**: Setup Django Channels and Redis.
  - *Done When: Frontend successfully connects to WebSocket and sends batch every 5s.*

## Week 2: Feature Engineering + Heuristic Engine
- `[ ]` **Edge Telemetry**: Build React script capturing keystrokes and mouse movement.
  - *Done When: Frontend logs compressed payloads correctly to console.*
- `[ ]` **Feature Pipeline**: Build FastAPI Sliding Window aggregation logic.
  - *Done When: `feature_windows` table correctly populated in DB.*
- `[ ]` **Heuristic Engine**: Implement Cognitive Scoring Logic + Explainability Basics.
  - *Done When: `[Inference]` logs show focus scores and states.*
- `[ ]` **Mock Telemetry Generator**: Create `mock_telemetry_generator.py` to simulate sessions.
  - *Done When: Script can simulate 'Focused', 'Distracted', and 'Fatigued' user states.*

## Week 3: Dashboard + Interventions + ML Pipeline
- `[ ]` **Analytics Dashboard**: Build clean Recharts UI for realtime trends.
  - *Done When: Dashboard displays live Focus/Fatigue charts.*
- `[ ]` **Adaptive UI**: Implement Priority Intervention System + Cooldown Logic.
  - *Done When: UI triggers "Deep Work Mode" popup correctly based on WebSocket prediction.*
- `[ ]` **Human-in-the-Loop Feedback**: Build popup to capture user-reported state.
  - *Done When: Feedback label correctly saves to DB.*

## Week 4: Testing + Optimization + Deployment + Demo Flow
- `[ ]` **ML Pipeline**: Train initial Random Forest model on feedback labels.
- `[ ]` **Demo Flow Verification**: Test complete flow (Focused → Distracted → Fatigued → Intervention → Recovery).
- `[ ]` **System Testing**: Verify reconnect logic and rate limiting.
- `[ ]` **Deployment Setup** (Vercel, Railway/AWS, Render).
