# Interview Pack: Systems Engineering Deep Dive

Use this document to prepare for technical interviews. It maps the architectural decisions made in Cognitive Load AI directly to common senior/SDE systems design questions.

## 1. Architecture

**Q: Why split the backend into Django and FastAPI instead of a monolith?**
**A:** Separation of concerns based on I/O profiles. Django is unmatched for stateful, relational data management (Auth, ORM, Privacy Governance) and is synchronous by nature. However, ML inference is highly concurrent and CPU-bound. FastAPI, built on Starlette and asyncio, excels at high-throughput concurrent workloads. Decoupling them allows the ML engine to scale (or fail) independently without taking down the core authentication plane.

**Q: Why use Redis Pub/Sub or Redis state instead of just a database?**
**A:** Ephemeral, high-velocity state (like WebSocket rate limits and single-use tickets) would overwhelm PostgreSQL with transaction locks and dead tuples (bloat). Redis operates entirely in memory, making atomic operations (like `GETDEL`) microseconds fast, which is critical for real-time telemetry validation.

## 2. Security

**Q: Why use "Ticket Auth" for WebSockets instead of just passing a JWT?**
**A:** WebSockets natively lack support for HTTP Headers (like Authorization). Passing a JWT in a URL query parameter is highly insecure (logged in server access logs, proxies, browser history). Our solution issues a cryptographically secure, short-lived (60s) ticket via an authenticated HTTP request. The ticket is then passed in the WS connection and atomically consumed in Redis using `GETDEL`, neutralizing replay attacks.

**Q: Why "Fail Closed"?**
**A:** In security, if the authentication provider (Redis) goes down, the system should reject all connections rather than bypass checks. If Redis is unavailable, our WebSocket consumer intentionally returns a `1011` error. Permitting unauthenticated access during an outage is a catastrophic vulnerability.

## 3. Resilience

**Q: What is a Circuit Breaker and why did you build one?**
**A:** A circuit breaker prevents cascading failures. If the ML inference engine becomes overloaded and latency spikes past 2.0s, requests queue up, starving the ASGI worker threads in Django. Our `MLClient` tracks failures. After 5 timeouts, it trips `OPEN`, instantly short-circuiting future calls to the ML engine for 30 seconds. This allows the ML service to recover while the Django gateway remains responsive.

**Q: How does Graceful Degradation work in this system?**
**A:** When the circuit breaker is `OPEN`, instead of throwing 500 errors to the client, the Gateway returns a synthesized `{ "status": "degraded" }` prediction payload. The frontend detects this and subtly adapts the UI (e.g., pausing heavy animations or showing a warning icon) without dropping the WebSocket connection or disrupting the user's primary workflow.

## 4. Privacy & Governance

**Q: How do you enforce consent in real-time?**
**A:** Telemetry pipelines are incredibly fast. If a user revokes consent via the HTTP API, we immediately flip a boolean flag in the database and cache. Crucially, the WebSocket consumer checks this `privacy_revoked_{user_id}` flag during its event loop. If triggered, it executes a server-side force disconnect and blacklists the session, ensuring no data is processed even a millisecond after revocation.

## 5. ML Honesty

**Q: How accurate is your model at predicting cognitive load?**
**A:** *Be brutally honest here.* 
"Currently, the inference engine uses a deterministic heuristic fallback to simulate predictions based on hardcoded thresholds (e.g., high keystroke velocity + frequent tab switching = high load). The MLOps pipeline (data collection, preprocessing, and the Random Forest inference script) is fully built and production-ready. However, it is intentionally gated because I refuse to deploy an untrained ML model in a production environment until we collect a statistically significant, ethically-sourced dataset of real human labels to train against."
