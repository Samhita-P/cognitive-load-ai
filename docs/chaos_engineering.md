# Phase 4.4: Chaos Engineering Runbooks

This document outlines the expected chaos engineering scenarios and how to trigger them. These tests are critical to validate the `MLClient` circuit breaker, fail-closed security logic, and graceful degradation in production.

## 1. Redis Outage
**Trigger:**
```bash
docker stop redis
```

**Expected Behavior:**
- **WebSockets:** Connection attempts will fail (`1011` fail closed) because connection capping and rate limiting cannot be enforced securely.
- **REST APIs:** Gateway endpoints that rely on caching will degrade or bypass cache, but should ideally stay up if DB is healthy.
- **Tickets:** Issuing and consuming WS tickets will fail.
- **Recovery:** `docker start redis` should immediately restore operations.

## 2. FastAPI (ML Service) Slowdown / Hang
**Trigger:**
Inject a `time.sleep(5)` into `ml-service/app/main.py` in the `/api/infer` endpoint.

**Expected Behavior:**
- **Circuit Breaker:** The `MLClient` in the Gateway will time out after 2.0 seconds. After 5 consecutive failures, the circuit breaker moves to the **OPEN** state.
- **Fallback:** The frontend will receive a prediction with `"status": "degraded"` almost instantly (fast-fail) for the next 30 seconds.
- **Recovery:** Remove the sleep. After 30 seconds, the breaker goes **HALF-OPEN**, probes successfully, and closes.

## 3. Postgres Database Unavailable
**Trigger:**
```bash
docker stop db
```

**Expected Behavior:**
- **Auth/API:** HTTP APIs and authentication will fail with 500 errors.
- **Telemetry:** If a WebSocket is already connected, it will crash when trying to save the telemetry payload atomically with the session. Future improvements could queue to Redis or Kafka.
- **Recovery:** `docker start db` restores state.

## 4. Threadpool Saturation
**Trigger:**
Change `MAX_THREADPOOL_WORKERS=2` in `ml-service` and run the k6 load test.

**Expected Behavior:**
- `asyncio.wait_for` in FastAPI will trigger `TimeoutError` as requests queue up.
- The service will return local fallback predictions without crashing.
- Metrics will show high `timeout_count` and `fallback_count`.

## 5. Corrupted Model Startup
**Trigger:**
Delete or truncate the joblib model files in `ml-service/models/`.

**Expected Behavior:**
- `ModelRegistry.load_once()` fails validation.
- FastAPI raises `RuntimeError` and refuses to start, preventing corrupted inference from serving production traffic.
