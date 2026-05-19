# Resume Bullets: Cognitive Load AI

These bullets are optimized to frame this project correctly based on the role you are applying for. **Do not market this as a basic machine learning project.** Market it as a production-grade distributed systems project.

## Option 1: SDE / Distributed Systems Focus
*(Best for backend-heavy Software Development Engineer roles)*

- Engineered a production-validated distributed real-time telemetry platform using Django, FastAPI, Redis, and WebSockets to process high-frequency behavioral data streams.
- Architected a resilient RPC pipeline between microservices, implementing a custom Circuit Breaker (Asyncio Semaphores) that shed load at 1,250 concurrent connections, triggering graceful UI degradation and preventing cascading failures.
- Hardened WebSocket security by replacing long-lived tokens with atomic, single-use tickets managed via Redis `GETDEL`, neutralizing connection exhaustion and replay attacks.
- Validated system reliability using chaos engineering drills and k6 load testing, defining explicit saturation points and observability alerts via Prometheus, Grafana, and Sentry.

## Option 2: Backend Engineering Focus
*(Best for roles emphasizing API design, data planes, and security)*

- Designed a secure backend architecture decoupling the core relational data plane (Neon PostgreSQL) from the high-throughput telemetry plane (Upstash Redis + WebSockets).
- Enforced strict privacy governance and data lifecycle policies, engineering an atomic right-to-be-forgotten pipeline that immediately force-disconnects active user WebSocket sessions upon consent revocation.
- Hardened API endpoints with defense-in-depth security measures including strict 1009 payload limits, per-user connection caps, and Redis-backed rate limiting to mitigate abuse.
- Established CI/CD maturity by pinning dependencies and writing comprehensive end-to-end security integration tests covering ticket replay rejection and load-shedding behaviors.

## Option 3: Full-Stack Engineering Focus
*(Best for roles bridging frontend React with robust backend APIs)*

- Built a complete full-stack real-time intelligence platform utilizing React (TypeScript) on the frontend and a decoupled Django/FastAPI microservices architecture on the backend.
- Developed an adaptive, responsive React UI that dynamically alters state based on real-time inference streaming via WebSockets, ensuring seamless UX even during backend ML fallback states.
- Implemented a secure authentication flow leveraging HTTP-only JWTs to securely request short-lived, single-use WebSocket tickets, solving the inherent vulnerabilities of authenticating native WS connections.
- Designed an interactive observability overlay directly within the React client, displaying real-time p95 latency and telemetry payload metrics.
