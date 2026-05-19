# 5-Minute Demo Script

Use this script during live interviews or when recording a Loom video for your portfolio. It is designed to aggressively highlight the complex backend engineering beneath the UI.

## 0:00 - The Hook (System Overview)
"Hi, this is Cognitive Load AI. It’s a distributed platform designed to track real-time behavioral telemetry and infer user cognitive load. The UI is clean, but the real complexity is under the hood—it's built to handle massive concurrency without crashing. Let me show you."

## 1:00 - Authentication & Consent
*Action: Register a new user and log in.*
"First, I authenticate. But before any telemetry is collected, the system enforces a strict privacy gate."
*Action: Click 'Opt-In' to telemetry.*
"Once I consent, the React frontend doesn't just open a WebSocket. It securely requests a short-lived, single-use ticket via HTTP. This ticket is instantly consumed in Redis when the WebSocket connects, making replay attacks impossible."

## 2:00 - The Telemetry Stream
*Action: Move mouse rapidly, click, and switch tabs.*
"Now I'm connected. Every keystroke and mouse movement is batched and streamed over the WebSocket. You can see the UI reacting to my simulated cognitive load. Underneath, the Django Gateway is securely routing this stream over RPC to a highly concurrent FastAPI inference engine."

## 3:00 - Simulating Failure (The Circuit Breaker)
*Action: Open the Demo Control Panel and click "Simulate ML Latency".*
"In distributed systems, downstream services fail. I just injected a 5-second latency spike into the ML Engine. Watch what happens."
*Action: Keep moving the mouse.*
"Instead of crashing the entire Django application or locking up the WebSockets, the MLClient Circuit Breaker detects the timeouts. It instantly trips OPEN. Notice how the UI gracefully shifts into a 'Degraded' state—it stays connected, data isn't lost, but we shed load to protect the system."

## 4:00 - Observability (Grafana)
*Action: Switch tab to Grafana Dashboard.*
"We don't just guess that it works; we measure it. Here is the Prometheus-backed observability plane. You can see the exact moment the p95 latency spiked, the circuit breaker state flipping from 0 to 1, and the fallback response rate jumping to 100%."

## 5:00 - Revocation & Right to be Forgotten
*Action: Switch back to the app. Go to Privacy settings and click 'Revoke Consent'.*
"Finally, privacy is absolute. If a user revokes consent..."
*Action: Show network tab / UI disconnected state.*
"...the system instantly drops the active WebSocket connection server-side. No further telemetry is processed. It's a completely secure, privacy-governed pipeline."
