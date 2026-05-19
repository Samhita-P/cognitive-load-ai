import asyncio
import httpx
import websockets
import json
import pytest
import os
import uuid

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
WS_URL = os.environ.get("WS_URL", "ws://127.0.0.1:8000")

@pytest.mark.asyncio
async def test_full_telemetry_lifecycle():
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    password = "e2epassword123"

    async with httpx.AsyncClient() as client:
        # 1. Register and Login
        reg_res = await client.post(f"{BASE_URL}/api/auth/register/", json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com"
        })
        assert reg_res.status_code in (200, 201)

        login_res = await client.post(f"{BASE_URL}/api/auth/login/", json={
            "username": username,
            "password": password
        })
        assert login_res.status_code == 200
        token = login_res.json()["access"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Grant Telemetry Consent
        consent_res = await client.post(
            f"{BASE_URL}/api/privacy/consent/",
            json={"telemetry_consent": True, "privacy_mode": False},
            headers=headers
        )
        assert consent_res.status_code == 200

        # 3. Get WS Ticket
        ticket_res = await client.post(
            f"{BASE_URL}/api/ws/ticket/",
            headers=headers
        )
        assert ticket_res.status_code == 201
        ticket = ticket_res.json()["ticket"]

    # 4. Connect WebSocket
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as websocket:
        # 5. Send Telemetry Batch
        batch_id = str(uuid.uuid4())
        payload = {
            "batch_id": batch_id,
            "session_id": "test_session",
            "schema_version": "telemetry.v1",
            "sequence_number": 1,
            "trace_id": str(uuid.uuid4()),
            "keyboard": {"key_presses": 10},
            "mouse": {"clicks": 2},
            "session": {"tab_switches": 0}
        }
        await websocket.send(json.dumps(payload))

        # 6. Receive ACK
        ack_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
        ack_data = json.loads(ack_msg)
        assert ack_data["type"] == "ack"
        assert ack_data["batch_id"] == batch_id

        # 7. Receive Prediction
        pred_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        pred_data = json.loads(pred_msg)
        assert pred_data["type"] == "prediction"
        assert "gateway_prediction_id" in pred_data["payload"]

        # 8. Submit Human Feedback
        async with httpx.AsyncClient() as client:
            fb_res = await client.post(f"{BASE_URL}/api/feedback/", json={
                "prediction_id": pred_data["payload"]["gateway_prediction_id"],
                "focus_score": 4,
                "fatigue_score": 2,
                "workload_score": 3,
                "confidence_score": 5,
                "features_snapshot": {}
            }, headers=headers)
            assert fb_res.status_code == 201

        # 9. Revoke Consent (Should Trigger Force Disconnect)
        async with httpx.AsyncClient() as client:
            revoke_res = await client.post(
                f"{BASE_URL}/api/privacy/consent/",
                json={"telemetry_consent": False},
                headers=headers
            )
            assert revoke_res.status_code == 200

        # 10. Verify Forced Disconnect
        with pytest.raises(websockets.exceptions.ConnectionClosed):
            await asyncio.wait_for(websocket.recv(), timeout=2.0)

    # 11. Verify HTTP Feedback Rejection
    async with httpx.AsyncClient() as client:
        fb_res_after_revoke = await client.post(f"{BASE_URL}/api/feedback/", json={
            "focus_score": 1,
            "features_snapshot": {}
        }, headers=headers)
        assert fb_res_after_revoke.status_code == 403

    print("✅ Full E2E Telemetry Lifecycle & Privacy Governance verified!")

@pytest.mark.asyncio
async def test_ticket_replay_rejection():
    # Attempt to reuse a ticket
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        token = login.json()["access"]
        headers = {"Authorization": f"Bearer {token}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        
        ticket_res = await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)
        ticket = ticket_res.json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    
    # First connection should succeed
    async with websockets.connect(ws_uri) as ws1:
        # Second connection with same ticket should be rejected immediately
        with pytest.raises(websockets.exceptions.InvalidStatusCode) as exc:
            await websockets.connect(ws_uri)
        assert exc.value.status_code == 403 # Or disconnected immediately

@pytest.mark.asyncio
async def test_oversized_payload_rejection():
    # Test 1009 rejection
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as ws:
        large_payload = "A" * 60000 # 60KB
        await ws.send(json.dumps({"batch_id": "test", "schema_version": "telemetry.v1", "data": large_payload}))
        
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc:
            await ws.recv()
        assert exc.value.code == 1009

@pytest.mark.asyncio
async def test_connection_caps():
    # Test max connections (1008)
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        
        sockets = []
        try:
            # Open 4 connections (default max is 3)
            for _ in range(4):
                ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
                ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
                sockets.append(await websockets.connect(ws_uri))
                
            # The 4th connection should be closed immediately with 1008
            with pytest.raises(websockets.exceptions.ConnectionClosed) as exc:
                await sockets[3].recv()
            assert exc.value.code == 1008
        finally:
            for s in sockets:
                if not s.closed:
                    await s.close()

@pytest.mark.asyncio
async def test_rate_limiting():
    # Test per-minute rate limits (1008)
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as ws:
        # Spam 65 messages (limit is 30/min or 60/min global)
        for i in range(65):
            await ws.send(json.dumps({
                "batch_id": f"test_{i}", 
                "schema_version": "telemetry.v1", 
                "sequence_number": i,
                "session_id": "test_session",
                "keyboard": {}, "mouse": {}, "session": {}
            }))
            
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc:
            for _ in range(65):
                await ws.recv()
        assert exc.value.code == 1008

@pytest.mark.asyncio
async def test_logout_token_blacklist():
    # Test that logging out invalidates the refresh token
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        refresh_token = login.json()["refresh"]
        
        # Test refresh works before logout
        refresh_res = await client.post(f"{BASE_URL}/api/auth/token/refresh/", json={"refresh": refresh_token})
        assert refresh_res.status_code == 200
        
        # Blacklist the token
        logout_res = await client.post(
            f"{BASE_URL}/api/auth/token/blacklist/", 
            json={"refresh": refresh_token}
        )
        assert logout_res.status_code in (200, 204, 205)
        
        # Test refresh fails after logout
        refresh_res_after = await client.post(f"{BASE_URL}/api/auth/token/refresh/", json={"refresh": refresh_token})
        assert refresh_res_after.status_code == 401

@pytest.mark.asyncio
async def test_unsupported_schema_rejection():
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as ws:
        await ws.send(json.dumps({
            "batch_id": str(uuid.uuid4()),
            "schema_version": "telemetry.v999"
        }))
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc:
            await ws.recv()
        assert exc.value.code == 1003

@pytest.mark.asyncio
async def test_dedupe_duplicate_batch_rejection():
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as ws:
        batch_id = str(uuid.uuid4())
        payload = {
            "batch_id": batch_id,
            "session_id": "test_session",
            "schema_version": "telemetry.v1",
            "sequence_number": 1,
            "trace_id": str(uuid.uuid4()),
            "keyboard": {}, "mouse": {}, "session": {}
        }
        
        # First send
        await ws.send(json.dumps(payload))
        ack = json.loads(await ws.recv())
        assert ack["status"] == "success"
        
        # Drain prediction message
        await ws.recv()
        
        # Second send (Duplicate) - should be silently dropped, no ack, no close
        await ws.send(json.dumps(payload))
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            assert False, "Expected no message, duplicate batch was processed!"
        except asyncio.TimeoutError:
            pass # Passed

@pytest.mark.asyncio
async def test_strict_ordering_gap_policy():
    username = f"e2e_user_{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/api/auth/register/", json={"username": username, "password": "pw", "email": f"{username}@test.com"})
        login = await client.post(f"{BASE_URL}/api/auth/login/", json={"username": username, "password": "pw"})
        headers = {"Authorization": f"Bearer {login.json()['access']}"}
        await client.post(f"{BASE_URL}/api/privacy/consent/", json={"telemetry_consent": True}, headers=headers)
        ticket = (await client.post(f"{BASE_URL}/api/ws/ticket/", headers=headers)).json()["ticket"]
        
    ws_uri = f"{WS_URL}/ws/telemetry/?ticket={ticket}"
    async with websockets.connect(ws_uri) as ws:
        def make_payload(seq):
            return json.dumps({
                "batch_id": str(uuid.uuid4()),
                "session_id": "test_session",
                "schema_version": "telemetry.v1",
                "sequence_number": seq,
                "trace_id": str(uuid.uuid4()),
                "keyboard": {}, "mouse": {}, "session": {}
            })
            
        # Send 1
        await ws.send(make_payload(1))
        ack = json.loads(await ws.recv())
        assert ack["status"] == "success"
        await ws.recv() # Wait for prediction
        
        # Send 2
        await ws.send(make_payload(2))
        ack = json.loads(await ws.recv())
        assert ack["status"] == "success"
        await ws.recv() # Wait for prediction
        
        # Send 5 (Jump forward) - should accept
        await ws.send(make_payload(5))
        ack = json.loads(await ws.recv())
        assert ack["status"] == "success"
        await ws.recv() # Wait for prediction
        
        # Send 4 (Stale) - should drop silently
        await ws.send(make_payload(4))
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            assert False, "Expected stale message to be dropped!"
        except asyncio.TimeoutError:
            pass # Passed
