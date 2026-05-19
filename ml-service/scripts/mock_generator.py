import asyncio
import websockets
import json
import time
import uuid
import random
import argparse
import os

DEFAULT_WS_URL = "wss://cognitive-ai-gateway.onrender.com/ws/telemetry/"


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


async def run_scenario(archetype: str, duration_sec: int, ws_url: str):
    session_id = str(uuid.uuid4())

    print(f"Starting scenario: {archetype}")
    print(f"Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            end_time = time.time() + duration_sec

            while time.time() < end_time:
                batch = generate_batch(session_id, archetype)

                await websocket.send(json.dumps(batch))
                print("Telemetry sent")

                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    print("Received:", response)

                except asyncio.TimeoutError:
                    print("No prediction received")

                await asyncio.sleep(5)

        print(f"Scenario completed: {archetype}")

    except Exception as e:
        print(f"WebSocket connection failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=str, default="Deep Focus")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--ws-url", type=str, default=os.environ.get("GATEWAY_WS_URL", DEFAULT_WS_URL))

    args = parser.parse_args()

    asyncio.run(
        run_scenario(
            args.scenario,
            args.duration,
            args.ws_url,
        )
    )