# Chaos Engineering Results

**Date:** 2026-05-19  

This document logs the outcomes of the chaos drills defined in `docs/chaos_engineering.md`.

## 1. Redis Outage
**Drill:** Stopped the Upstash Redis container / blocked Redis port.
- **Expected Behavior:** Ticket auth fails closed. Existing telemetry degrades predictably. No worker crash. Reconnect attempts fail securely.
- **Observed Behavior:**
  - `POST /api/ws/ticket/` immediately returned HTTP 500 (handled cleanly by API, no crash).
  - Attempting to connect to WS without a valid ticket failed closed with 1011.
  - Active WebSockets dropped connection. Reconnect logic on the frontend initiated but failed cleanly.
- **Result:** **PASS**. No unhandled exceptions in the ASGI workers. Secure fail-closed behavior confirmed.

## 2. FastAPI Latency Injection
**Drill:** Injected `time.sleep(5)` into the `POST /predict` endpoint on the ML service.
- **Expected Behavior:** ML Client breaker opens after 5 failures. Fallback returned. Latency bounded.
- **Observed Behavior:**
  - First 5 telemetry batches per worker hit the 2.0s timeout and raised `httpx.ReadTimeout`.
  - Circuit Breaker tripped to **OPEN**.
  - Subsequent batches immediately returned `{"status": "degraded"}` without waiting 2.0s.
  - WS connection remained stable; ACK latency dropped back to ~15ms.
- **Result:** **PASS**. No WebSocket worker exhaustion. Graceful degradation successful.

## 3. Corrupt Model Artifact
**Drill:** Overwrote `rf_model.pkl` with random string bytes and restarted ML service.
- **Expected Behavior:** Startup hard fail.
- **Observed Behavior:**
  - FastAPI `lifespan` function raised `joblib.externals.loky.process_executor.TerminatedWorkerError` / `UnpicklingError`.
  - Service refused to boot, returning exit code 1.
- **Result:** **PASS**. Service prevents serving garbage predictions by failing fast.

## 4. Threadpool Exhaustion
**Drill:** Set `MAX_THREADPOOL_WORKERS=2` on ML service and blasted it with 500 concurrent requests via k6.
- **Expected Behavior:** Timeouts occur, graceful degraded mode kicks in, no deadlocks.
- **Observed Behavior:**
  - The `asyncio.Semaphore(2)` correctly queued requests.
  - Due to queueing, latency spiked past the Gateway's 2.0s timeout threshold.
  - Gateway Circuit Breaker tripped **OPEN**.
  - System stabilized in degraded mode rather than deadlocking or OOMing.
- **Result:** **PASS**. Backpressure and semantic shedding function correctly.

## 5. Postgres Outage
**Drill:** Scaled Neon DB replica down to 0 / blocked connection string.
- **Expected Behavior:** Auth/Data APIs fail clearly. Telemetry behavior documented.
- **Observed Behavior:**
  - `POST /api/auth/login/` and `POST /api/feedback/` timed out and returned HTTP 500.
  - Active WebSocket telemetry (which relies only on JWT and Redis for auth validation) **CONTINUED TO FUNCTION** without disruption.
  - ML Inference continued to function.
- **Result:** **PASS**. Hard decoupling between core data plane and realtime telemetry plane proven.
