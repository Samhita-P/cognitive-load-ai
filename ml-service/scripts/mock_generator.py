import asyncio
import json
import os
import time
import uuid
import random
import argparse

import websockets


def default_ws_url() -> str:
    return os.environ.get(
        "GATEWAY_WS_URL",
        "ws://127.0.0.1:8000/ws/telemetry/",
    )


def build_ws_uri(base: str, token: str | None) -> str:
    b = base.strip().rstrip("/")
    if token:
        sep = "?" if "?" not in b else "&"
        return f"{b}{sep}token={token}"
    return f"{b}/"


def generate_batch(session_id: str, archetype: str) -> dict:
    now = int(time.time() * 1000)

    keystrokes = random.randint(10, 30)
    backspaces = random.randint(0, 2)
    longest_pause = random.randint(500, 1500)
    distance_px = random.uniform(200.0, 500.0)
    clicks = random.randint(0, 5)
    variance_x = random.uniform(10.0, 50.0)
    variance_y = random.uniform(10.0, 50.0)
    idle_time_ms = random.randint(0, 500)

    if archetype == "Deep Focus":
        keystrokes = random.randint(40, 80)
        backspaces = random.randint(0, 3)
        longest_pause = random.randint(100, 500)
        distance_px = random.uniform(50.0, 200.0)
        idle_time_ms = 0
    elif archetype == "Severe Fatigue":
        keystrokes = random.randint(5, 15)
        backspaces = random.randint(3, 8)
        longest_pause = random.randint(2000, 4000)
        distance_px = random.uniform(100.0, 300.0)
        variance_x = random.uniform(100.0, 300.0)
        idle_time_ms = random.randint(1000, 3000)
    elif archetype == "Mild Distraction":
        keystrokes = random.randint(0, 10)
        idle_time_ms = random.randint(2000, 4000)
        distance_px = random.uniform(800.0, 1500.0)
        clicks = random.randint(5, 15)
    elif archetype == "Chaotic Task Switching":
        keystrokes = random.randint(10, 50)
        distance_px = random.uniform(1500.0, 3000.0)
        variance_x = random.uniform(200.0, 500.0)
        clicks = random.randint(10, 20)

    return {
        "batch_id": str(uuid.uuid4()),
        "session_id": session_id,
        "timestamp_start": now - 5000,
        "timestamp_end": now,
        "keyboard": {
            "keystrokes": keystrokes,
            "backspaces": backspaces,
            "longest_pause_ms": longest_pause,
        },
        "mouse": {
            "distance_px": distance_px,
            "clicks": clicks,
            "variance_x": variance_x,
            "variance_y": variance_y,
        },
        "session": {
            "idle_time_ms": idle_time_ms,
            "tab_hidden": archetype == "Mild Distraction" and random.random() > 0.5,
        },
    }


async def run_scenario(archetype: str, duration_sec: int, ws_uri: str):
    session_id = str(uuid.uuid4())
    print(f"Starting Scenario: {archetype} (Session: {session_id})")
    safe = ws_uri.split("token=")[0].rstrip("&?") if "token=" in ws_uri else ws_uri
    print(f"Connecting to {safe}...")

    async with websockets.connect(ws_uri) as websocket:
        end_time = time.time() + duration_sec
        while time.time() < end_time:
            batch = generate_batch(session_id, archetype)
            await websocket.send(json.dumps(batch))

            try:
                await websocket.recv()
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                pred = json.loads(response)
                if pred.get("type") == "prediction":
                    state = pred["payload"]["state"]
                    conf = pred["payload"]["confidence"]
                    print(f"[{archetype}] Inferred State: {state} ({conf:.1f}%)")
            except Exception as e:
                print(f"Error receiving prediction: {e}")

            await asyncio.sleep(5)

    print(f"Scenario {archetype} Completed.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Telemetry Generator")
    parser.add_argument(
        "--scenario",
        type=str,
        default="Deep Focus",
        help="Session Archetype",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Duration in seconds",
    )
    parser.add_argument(
        "--ws-url",
        type=str,
        default=None,
        help="WebSocket base URL (token appended if --token set). "
        "Overrides GATEWAY_WS_URL env.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="JWT access token for gateway. Overrides DEMO_GATEWAY_JWT / GATEWAY_JWT env.",
    )
    args = parser.parse_args()

    base = args.ws_url or default_ws_url()
    token = args.token or os.environ.get("DEMO_GATEWAY_JWT") or os.environ.get(
        "GATEWAY_JWT"
    )
    ws_uri = build_ws_uri(base, token)

    asyncio.run(run_scenario(args.scenario, args.duration, ws_uri))
