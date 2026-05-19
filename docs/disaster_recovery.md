# Disaster Recovery Runbook

This document defines the recovery procedures for critical stateful components of the Cognitive Load AI platform to ensure rapid restoration of service during catastrophic failures.

## 1. Neon PostgreSQL (Core Database)

The PostgreSQL database stores user accounts, authentication tokens, privacy consent records, and high-value human feedback.

- **Recovery Point Objective (RPO):** 5 minutes (based on Neon's continuous WAL archiving).
- **Recovery Time Objective (RTO):** 30 minutes.

### Recovery Procedure
1. Navigate to the Neon Console for the project.
2. Select **Branches** -> **Restore from Point in Time**.
3. Select a timestamp immediately preceding the corruption or deletion event.
4. Create a new branch (e.g., `production-restore-YYYYMMDD`).
5. Once the branch is active, update the `DATABASE_URL` secret in Render/Vercel to point to the new connection string.
6. Trigger a restart of the `backend-gateway` service to establish connections to the restored DB.
7. Verify functionality by logging in via the frontend.

## 2. Upstash Redis (Cache & Realtime State)

Redis manages ephemeral data: rate limits, WebSocket tickets, and connection tracking. 

- **Recovery Point Objective (RPO):** N/A (Ephemeral state). Data loss here is acceptable.
- **Recovery Time Objective (RTO):** 10 minutes.
- **Impact of Loss:** Active WebSockets will disconnect. Users must refresh their page or click "Reconnect" to acquire a new ticket.

### Recovery Procedure
1. If the Redis instance crashes or data is wiped, the application is designed to fail securely. WebSockets will refuse new connections (Code 1011).
2. To restore, either wait for Upstash to auto-recover, or provision a new Upstash Redis database.
3. Update the `REDIS_URL` in the environment variables.
4. Restart the `backend-gateway` service.
5. Existing users will automatically re-authenticate and open new WebSocket sessions.

## 3. ML Model Artifacts

The ML service relies on serialized model artifacts (e.g., `rf_model.pkl`, `scaler.pkl`).

- **Recovery Point Objective (RPO):** N/A (Models are immutable).
- **Recovery Time Objective (RTO):** 15 minutes.

### Recovery Procedure
1. If an artifact is deleted or corrupted, the ML service will **hard fail on startup** to prevent serving garbage predictions.
2. The artifacts are tracked via Git LFS (or reproducible via the benchmark training scripts).
3. To rebuild the models from scratch (if Git LFS is unavailable):
   ```bash
   cd ml-service
   python scripts/train_benchmark.py
   ```
4. This will generate fresh `.pkl` files in the `models/` directory.
5. Commit and push the rebuilt models, which will trigger a new Render deployment.

## 4. Disaster Incident Response Flow
1. **Declare Incident:** Acknowledge alerts from Grafana/Sentry.
2. **Contain:** If corrupted data is spreading, scale down the `backend-gateway` to 0 instances to stop writes.
3. **Diagnose:** Check Neon DB status, Redis availability, and application logs.
4. **Restore:** Follow the component-specific recovery procedure above.
5. **Verify:** Run the E2E tests (`pytest tests/test_e2e_telemetry.py`) locally against the restored production endpoints (using test accounts).
6. **Post-Mortem:** Document the root cause and mitigation in the project wiki.
