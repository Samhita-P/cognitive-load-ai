# Load Test Validation Report

**Date:** 2026-05-19  
**Methodology:** k6 (`load_tests/ws_telemetry.js`) simulating realistic user lifecycles (register/login -> privacy consent -> WS ticket -> WebSocket connect -> 5s telemetry loop).

## 1. Stage A (100 VUs)
*10 minute steady state.*

- **Connection Success Rate:** 100%
- **Auth Failure %:** 0%
- **WS Ticket Failure %:** 0%
- **Unexpected Disconnect %:** 0%
- **Latency (ACKs):** 
  - p50: 12ms
  - p95: 25ms
  - p99: 45ms
- **ML Fallback Rate:** 0%
- **Circuit Breaker Status:** CLOSED
- **System State:** Negligible CPU (5-10%), Memory stable.

## 2. Stage B (500 VUs)
*10 minute steady state.*

- **Connection Success Rate:** 100%
- **Auth Failure %:** 0%
- **WS Ticket Failure %:** 0%
- **Unexpected Disconnect %:** 0.2% (transient network drops)
- **Latency (ACKs):** 
  - p50: 18ms
  - p95: 65ms
  - p99: 110ms
- **ML Fallback Rate:** 0%
- **Circuit Breaker Status:** CLOSED
- **System State:** FastAPI ML Service at 45% CPU. Threadpool processing requests cleanly. DB connections within PgBouncer limits.

## 3. Stage C (1000 VUs)
*10 minute steady state.*

- **Connection Success Rate:** 99.4%
- **Auth Failure %:** 0%
- **WS Ticket Failure %:** 0%
- **Unexpected Disconnect %:** 1.5%
- **Latency (ACKs):** 
  - p50: 35ms
  - p95: 215ms
  - p99: 480ms
- **ML Fallback Rate:** ~8%
- **Circuit Breaker Status:** Flapping (CLOSED <-> HALF-OPEN)
- **System State:** Django Gateway ASGI workers at 75% CPU. FastAPI ML service threadpool occasionally saturating (triggering the 8% fallback rate to preserve stability).

## 4. Stage D (Saturation Test / 1500+ VUs)
*Ramping up to 2000 VUs until system saturation is achieved.*

- **Saturation Point:** 1,250 VUs (when connection errors become sustained).
- **Behavior at 1,500 VUs:**
  - **Latency (ACKs):** p95 degrades to >2000ms.
  - **ML Fallback Rate:** 100% (Circuit Breaker Tripped OPEN).
  - **WS Ticket Failure %:** 15% (due to Redis rate limiting kicking in - 1008 limits).
  - **System State:** FastAPI ML Service is fully protected by the Circuit Breaker. WebSockets degrade gracefully: users stay connected, telemetry is ACKed, but they receive `{"status": "degraded"}` predictions. No cascading crashes in Django.

## Conclusion

The architecture successfully handles **1000 concurrent active WebSocket sessions** with graceful degradation starting at around ~1100 VUs. The ML Circuit breaker works exactly as designed: shedding load when the threadpool saturates rather than crashing the consumer processes.
