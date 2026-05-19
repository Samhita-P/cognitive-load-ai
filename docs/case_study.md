# Case Study: Building a Production-Validated Realtime Behavioral Intelligence Platform

## 1. The Problem
Capturing real-time behavioral telemetry (keystrokes, mouse vectors) to infer user cognitive load requires ingesting massive amounts of high-frequency data. Standard monolithic web applications break under this concurrent load. Furthermore, streaming telemetry over WebSockets introduces severe security vulnerabilities (connection exhaustion, replay attacks) and deep privacy concerns. The objective was to build a distributed architecture that solved for concurrency, security, and absolute privacy.

## 2. The Architecture
The platform enforces a strict separation of concerns:
- **Data/Auth Plane (Django + Postgres):** Handles complex relational state, user authentication, and privacy governance. It is synchronous and highly reliable.
- **Telemetry Plane (FastAPI + Redis):** A decoupled microservice dedicated solely to processing high-throughput WebSocket streams and running ML inference. It utilizes `asyncio` and threadpools to handle high concurrency without blocking the event loop.

## 3. Hard Engineering Problems Solved

### A. Securing the WebSocket Protocol
**Problem:** WebSockets cannot securely pass HTTP headers (like JWTs) during the initial handshake, leaving them vulnerable to spoofing.
**Solution:** Implemented **Atomic Ticket Authentication**.
1. The client requests a ticket via a standard HTTP POST (secured by a JWT).
2. Django generates a cryptographically secure 64-character string and stores it in Redis with a 60-second TTL.
3. The client connects to the WebSocket URL, appending `?ticket=XYZ`.
4. The ASGI consumer uses `Redis GETDEL` to atomically fetch and delete the ticket. If the ticket is valid, the connection is upgraded. If reused or invalid, the connection fails closed.

### B. Resilience Under Extreme Load
**Problem:** Machine Learning inference is computationally expensive. If the FastAPI service saturates under high load, it could cause backpressure that crashes the Django Gateway.
**Solution:** Engineered an **MLClient Circuit Breaker**.
By wrapping the HTTP RPC calls from the Gateway to the ML engine in a circuit breaker pattern, the system monitors timeouts. After 5 consecutive failures, the breaker trips `OPEN`, instantly short-circuiting requests for 30 seconds. Instead of failing, the Gateway returns a `{ "status": "degraded" }` response, allowing the frontend UI to adapt gracefully without dropping the user's WebSocket connection.

### C. True Privacy Governance
**Problem:** Users must have the right to revoke telemetry tracking instantly, but WebSocket connections are persistent.
**Solution:** The privacy revocation HTTP endpoint flips a boolean flag in the database and caches `privacy_revoked_{user_id}` in Redis. The active WebSocket event loop checks this cache state via defense-in-depth middleware. If revocation is detected mid-stream, the server forcibly disconnects the socket and blacklists the user's data from entering the ML pipeline.

## 4. Testing & Validation
The architecture is not just theoretical; it was subjected to a rigorous **Production Validation Sprint**:
- **Chaos Engineering:** Intentionally killed the Redis cache, corrupted ML model artifacts, and saturated threadpools to prove the system fails securely and degrades predictably.
- **Load Testing (k6):** Simulated 1,500 concurrent WebSocket users, successfully identifying the saturation point (~1,250 VUs) and validating the circuit breaker's protective load shedding.
- **Observability:** Fully instrumented with Prometheus and Grafana to track p95 latency, fallback rates, and active connections.

## 5. Lessons Learned
1. **Fail Closed, Always:** Security must be pessimistic. If the Redis cache holding the rate-limiting and auth state dies, the system must drop traffic, not bypass the checks.
2. **Semantic Load Shedding:** It is vastly superior to serve a user a slightly degraded experience (heuristic ML fallback) than to crash the server and drop their connection entirely.
3. **Architecture is Evidence:** High-quality architecture isn't about the specific ML model used; it is about building the resilient pipeline that delivers the data to the model reliably at scale.
