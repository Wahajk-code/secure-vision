import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8001/ws/stats"
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
