import asyncio
import json
import os

import websockets

async def test_connection():
    token = os.getenv("SECUREVISION_TEST_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Set SECUREVISION_TEST_TOKEN before running the websocket smoke test.")

    uri = f"ws://localhost:8001/ws/stats?token={token}"
    print(f"Attempting to connect to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print(" Connected!")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f" Received: {data.keys()}")
                break # Just need one message to prove it works
    except Exception as e:
        print(f" Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
