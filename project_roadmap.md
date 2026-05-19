# 🚀 Cognitive Load AI: Future Roadmap & Upgrades

With the initial architecture functioning as a **Production-Deployed MVP**, this document outlines the reprioritized roadmap for the next stages of development. The focus shifts toward achieving enterprise-grade engineering maturity and transitioning the core ML engine from heuristic estimations to validated supervised models.

---

## Phase 1 — Enterprise Foundations (Highest ROI)

### 1) Dockerize Everything
**Why:** Shows immediate deployment maturity and ensures infrastructure reproducibility.
**Implementation Checklist:**
*   Add `Dockerfile` for the Frontend (React/Vite).
*   Add `Dockerfile` for the API Gateway (Django).
*   Add `Dockerfile` for the ML Service (FastAPI).
*   Create a root `docker-compose.yml` to orchestrate the entire stack locally.

### 2) GitHub Actions CI/CD
**Why:** Recruiters and engineering teams look for CI/CD. It shows software engineering maturity, prevents broken deployments, and brings production discipline to the architecture.
**Pipeline:**
*   **Backend / Gateway**: `pytest`, `flake8`, `black check`
*   **Frontend**: `npm test`, `eslint`, `npm run build`
*   **ML-Service**: Unit tests for inference latency and model schemas
*   **Action**: Deploy only if all checks pass.

### 3) Monitoring & Observability
**Why:** Essential for SRE/DevOps maturity. Tracking failures in a distributed architecture is critical.
**Implementation Checklist:**
*   **Sentry Integration**: Add Sentry SDKs to Frontend, Gateway, and ML Service to track frontend crashes, backend exceptions, and ML failures in real-time.

### 4) Security Hardening
**Why:** The system is public and must be resilient against abuse before scaling testing.
**Implementation Checklist:**
*   **Rate Limiting**: DRF throttling to limit API endpoint abuse.
*   **Token Validation**: Enforce strict JWT rotation.
*   **WebSocket Auth**: Validate tokens on WebSocket connect and reject malformed requests instantly.
*   **CORS Tightening**: Restrict to the exact frontend domain.
*   **Secrets Management**: Secure environment variable handling.

---

## Phase 2 — Reliability & Scale Validation

### 5) Load Testing (Massive System Design Value)
**Why:** The architecture relies on real-time WebSockets + Redis. You must know your breaking points securely.
**Testing Specs:**
*   **Users**: 50, 100, 250, 500 concurrent users.
*   **Metrics**: WebSocket connection success, Redis latency, inference latency, dropped packets.
*   **Tools**: **k6** (highly recommended for WebSockets).

---

## Phase 3 — Transition to Validated Machine Learning

### 6) Replace Heuristics with Trained Model
**Why:** The current system uses a rule-based engine to estimate cognitive load. True AI validation requires supervised models trained on ground truth.
**Implementation Checklist:**
*   Train a **Random Forest** model using the labeled feedback data (`feedback.jsonl`), followed by upgrading to **XGBoost**.
*   **Inputs**: typing speed, pause ratio, backspace frequency, mouse entropy, click burst frequency, idle time.
*   **Outputs**: Focused, Distracted, Fatigued, Overloaded.

### 7) Add Evaluation Metrics & Drift Monitoring
**Why:** Without validation metrics, ML claims are weak.
**Implementation Checklist:**
*   Implement tracking for **Accuracy, Precision, Recall, and F1 Scores**.
*   Implement data drift monitoring to ensure input feature distributions do not shift unexpectedly over time.
*   Publish model performance metrics to validate cognitive inference validity.

---

## Phase 4 — "Wow Factor" Upgrades

### 8) Personalized Baselines
**Why:** Currently, the model uses a global baseline. However, a slow typist is not necessarily fatigued. Normalizing data per user provides the most immediate accuracy improvement.
**Implementation:**
*   Per-user baseline normalization: `z = (current - user_mean) / user_std`
*   Track individual typist and interaction profiles over time.

### 9) Long-Term Trend Forecasting
**Why:** Elevates the project from a session-tracker to a genuine wellness product.
**Implementation:**
*   Implement daily and weekly burnout prediction based on accumulated fatigue and interaction consistency over multiple days.
