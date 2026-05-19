import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Custom Metrics
const wsLatency = new Trend('ws_ack_latency_ms');
const mlTimeoutRate = new Rate('ml_timeout_rate');
const mlFallbackRate = new Rate('ml_fallback_rate');
const wsConnectionSuccess = new Rate('ws_connection_success');
const wsDisconnects = new Counter('ws_disconnects');
const connectionErrors = new Counter('connection_errors');

export const options = {
    scenarios: {
        websocket_load: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 100 },  // Stage 1: 100 concurrent
                { duration: '1m', target: 500 },   // Stage 2: 500 concurrent
                { duration: '1m', target: 1000 },  // Stage 3: 1000 concurrent
                { duration: '2m', target: 1000 },  // Hold max load
                { duration: '30s', target: 0 },    // Ramp down
            ],
        },
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const WS_URL = __ENV.WS_URL || 'ws://127.0.0.1:8000';

// We run the login in the default function but only once per VU.
// This is achieved by having the VU login, get a ticket, and then enter a long-running WebSocket session.
export default function () {
    const vuId = __VU;
    
    // 1. Register / Login (using a deterministic mock user per VU)
    const username = `test_user_${vuId}`;
    const password = 'testpassword123';
    
    // Try to login. If fails, try to register.
    let loginRes = http.post(`${BASE_URL}/api/auth/login/`, {
        username: username,
        password: password
    });

    if (loginRes.status !== 200) {
        http.post(`${BASE_URL}/api/auth/register/`, {
            username: username,
            password: password,
            email: `${username}@test.com`
        });
        loginRes = http.post(`${BASE_URL}/api/auth/login/`, {
            username: username,
            password: password
        });
    }

    if (loginRes.status !== 200) {
        connectionErrors.add(1);
        return; // Skip if auth fails
    }

    const token = loginRes.json('access');

    // Opt-in to telemetry (required)
    http.post(`${BASE_URL}/api/privacy/consent/`, 
        { telemetry_consent: true, privacy_mode: false },
        { headers: { 'Authorization': `Bearer ${token}` } }
    );

    // 2. Get WebSocket Ticket
    const ticketRes = http.post(`${BASE_URL}/api/ws/ticket/`, null, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (ticketRes.status !== 201) {
        connectionErrors.add(1);
        return; // Skip if ticket fails
    }

    const ticket = ticketRes.json('ticket');

    // 3. Connect WebSocket
    const url = `${WS_URL}/ws/telemetry/?ticket=${ticket}`;
    
    const res = ws.connect(url, {}, function (socket) {
        wsConnectionSuccess.add(1);

        socket.on('open', () => {
            // Keep sending telemetry while the socket is open
            socket.setInterval(() => {
                const batchId = `batch_${vuId}_${Date.now()}`;
                const payload = {
                    batch_id: batchId,
                    session_id: `session_${vuId}`,
                    keyboard: { key_presses: 15 },
                    mouse: { clicks: 2, distance: 300 },
                    session: { tab_switches: 0 }
                };

                const start = Date.now();
                socket.send(JSON.stringify(payload));

                // We simulate listening for the ack and prediction
                socket.on('message', (msg) => {
                    try {
                        const data = JSON.parse(msg);
                        if (data.type === 'ack' && data.batch_id === batchId) {
                            wsLatency.add(Date.now() - start);
                        } else if (data.type === 'error' && data.error_type === 'InferenceTimeout') {
                            mlTimeoutRate.add(1);
                        } else if (data.type === 'prediction') {
                            if (data.payload.status === 'degraded') {
                                mlFallbackRate.add(1);
                            } else {
                                mlFallbackRate.add(0);
                            }
                            mlTimeoutRate.add(0);
                        }
                    } catch (e) {
                        // ignore parsing errors
                    }
                });
            }, 5000); // Send every 5 seconds
        });

        socket.on('close', () => {
            wsDisconnects.add(1);
        });
        
        socket.on('error', (e) => {
            connectionErrors.add(1);
        });

        // Keep socket open for the duration of the VU's lifecycle (simulated 3 minutes)
        socket.setTimeout(function () {
            socket.close();
        }, 180000); 
    });

    check(res, { 'status is 101': (r) => r && r.status === 101 });
}
