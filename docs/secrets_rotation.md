# Secrets Rotation Runbook

This document defines the strict, actionable procedures for rotating critical credentials in the Cognitive Load AI platform. 

## 1. Django SECRET_KEY

The `SECRET_KEY` is used for cryptographic signing in Django (e.g., session cookies, password reset tokens).

- **Impact of Rotation:** All active Django sessions (browser-based admin panel, etc.) will be invalidated. Users will be forced to log in again. JWTs (handled by `SIMPLE_JWT`) are NOT invalidated by this unless they rely on the same key (we use separate keys, see below).
- **Downtime:** 0 downtime.
- **Procedure:**
  1. Generate a new secure key (e.g., `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`).
  2. Update the `SECRET_KEY` environment variable in the deployment environment (Render).
  3. The service will automatically restart.
  4. Verify the application boots successfully.

## 2. JWT Signing Key

The `JWT_SIGNING_KEY` is used to sign the access and refresh tokens.

- **Impact of Rotation:** **CRITICAL**. ALL existing user tokens (access and refresh) immediately become invalid. ALL users will be immediately logged out and any active WebSockets will eventually fail to reconnect once their tickets expire. This is a highly disruptive event.
- **Downtime:** 0 downtime, but massive UX disruption.
- **Procedure:**
  1. Coordinate this rotation during low-traffic windows or during a security incident.
  2. Generate a new cryptographic key.
  3. Update the `JWT_SIGNING_KEY` environment variable in Render.
  4. The service will automatically restart.
  5. Monitor Grafana for a spike in 401 Unauthorized errors (expected) followed by new login events.

## 3. Database Credentials (Neon PostgreSQL)

- **Impact of Rotation:** The application will be unable to connect to the database until the new credentials are live.
- **Downtime:** ~1-2 minutes during the transition.
- **Procedure:**
  1. Navigate to the Neon Console -> Project -> Roles.
  2. Select the database role and choose **Reset Password**.
  3. Copy the newly generated `DATABASE_URL`.
  4. Update the `DATABASE_URL` environment variable in Render.
  5. Trigger a manual deploy/restart of the `backend-gateway`.
  6. **Warning:** Any requests hitting the gateway between steps 2 and 5 will fail with HTTP 500s.

## 4. Redis Credentials (Upstash)

- **Impact of Rotation:** Active WebSockets will be dropped when the connection resets, and users will need to re-authenticate for WebSocket tickets.
- **Downtime:** ~1-2 minutes of realtime telemetry interruption.
- **Procedure:**
  1. Navigate to the Upstash Console.
  2. Go to the Redis database settings and click **Reset Password**.
  3. Copy the new `REDIS_URL`.
  4. Update the `REDIS_URL` in Render.
  5. Restart the `backend-gateway`.

## 5. Sentry DSN

- **Impact of Rotation:** Error logging will momentarily pause; no impact on user experience or system stability.
- **Downtime:** 0 downtime.
- **Procedure:**
  1. Navigate to Sentry -> Project Settings -> Client Keys (DSN).
  2. Generate a new DSN key.
  3. Update `SENTRY_DSN` in both Render (Gateway) and Vercel (Frontend).
  4. Revoke the old DSN key in Sentry.
  5. Ensure new errors are still being captured in the Sentry dashboard.
