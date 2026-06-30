import asyncio
import websockets
import json
import time
import random

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
GAME_ID = "GAME-123456" # Replace with a valid game_id from DB
NUM_USERS = 1000

async def simulate_user(user_id: int):
    uri = f"{WS_URL}/api/game/{GAME_ID}/ws?user_id={user_id}"
    try:
        async with websockets.connect(uri) as websocket:
            # Random wait to stagger connections
            await asyncio.sleep(random.uniform(0, 2))
            
            # Select a random card
            card_number = random.randint(1, 600)
            await websocket.send(json.dumps({
                "action": "select_card",
                "card_number": card_number
            }))
            
            # Keep connection open and listen to messages
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data.get("type") == "countdown_started":
                    pass
                elif data.get("type") == "number_called":
                    pass
    except Exception as e:
        pass # Ignore connection errors for stress test

async def main():
    print(f"Starting stress test with {NUM_USERS} concurrent users...")
    start_time = time.time()
    
    tasks = []
    for i in range(1, NUM_USERS + 1):
        tasks.append(simulate_user(i))
    
    # Wait for all tasks (they run infinitely until server closes or errors)
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"Test completed in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
