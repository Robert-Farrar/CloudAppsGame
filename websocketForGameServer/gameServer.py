import asyncio
import websockets
import json
import logging
from typing import Dict, Any

# --- Configuration ---
# idk if we need this but keeping it here for now someone might need the info later 
# NOTE: This section has been updated to reflect connection to a SQL Database (MariaDB)

DATABASE_MOCK: Dict[str, Any] = {}
USERS: Dict[str, websockets.WebSocketServerProtocol] = {} # {user_id: websocket}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def fetch_game_state_from_db(game_id: str) -> Dict:
    """Mocks fetching game state from MariaDB."""
    # In a real application, this would execute a SELECT query.
    return DATABASE_MOCK.get(game_id, {"status": "new", "players": []})

def persist_game_state_to_db(game_id: str, state: Dict):
    """Mocks saving game state to MariaDB via an UPDATE query."""
    # In a real application, this would execute an UPDATE query wrapped in a transaction.
    DATABASE_MOCK[game_id] = state
    logging.info(f"Game {game_id} state persisted to MariaDB.")

async def send_message(websocket: websockets.WebSocketServerProtocol, type: str, data: Dict):
    """Utility function to send structured JSON message."""
    message = json.dumps({"type": type, "data": data})
    await websocket.send(message)

async def broadcast_game_state(game_id: str, state: Dict):
    """Sends the new state to all connected players in the game."""
    for user_id, ws in USERS.items():
        # Check if the user is part of the game (simplified check)
        if user_id in state.get('players', []):
            await send_message(ws, "STATE_UPDATE", state)
            
async def register(websocket: websockets.WebSocketServerProtocol, user_id: str):
    """Handles new user registration and connection."""
    USERS[user_id] = websocket
    logging.info(f"User {user_id} connected. Total users: {len(USERS)}")

async def unregister(user_id: str):
    """Handles user disconnection."""
    if user_id in USERS:
        del USERS[user_id]
    logging.info(f"User {user_id} disconnected. Total users: {len(USERS)}")
    # In a real app, this would clean up game session in the DB if necessary

async def handle_message(websocket: websockets.WebSocketServerProtocol, message: str):
    """Parses incoming message and executes game logic."""
    try:
        data = json.loads(message)
        msg_type = data.get("type")
        payload = data.get("payload", {})
        user_id = payload.get("user_id")
        game_id = payload.get("game_id")

        if not user_id:
            return await send_message(websocket, "ERROR", {"message": "Missing user_id"})

        if msg_type == "CONNECT":
            await register(websocket, user_id)
            # Find or create a game for the user

        elif msg_type == "PLAY_CARD" and game_id:
            # 1. Fetch state from MariaDB
            state = fetch_game_state_from_db(game_id)
            
            # --- Conceptual Game Logic Execution ---
            if state["status"] == "active" and user_id == state.get("current_turn"):
                card_played = payload["card"]
                # 2. Update game state based on card_played
                # 3. Set next turn
                
                # Mock update:
                state['last_card'] = card_played
                state['current_turn'] = 'other_player' # Simplified turn swap
                
                # 4. Save state back to MariaDB
                persist_game_state_to_db(game_id, state)
                
                # 5. Broadcast the change to all players in the game
                await broadcast_game_state(game_id, state)
            else:
                await send_message(websocket, "ERROR", {"message": "Not your turn or game inactive."})
            # -------------------------------------

    except json.JSONDecodeError:
        await send_message(websocket, "ERROR", {"message": "Invalid JSON format."})
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await send_message(websocket, "ERROR", {"message": "Server error."})


async def game_handler(websocket: websockets.WebSocketServerProtocol, path: str):
    """Main entry point for new WebSocket connections."""
    user_id = str(id(websocket)) # Use memory address as a temporary ID

    # A connection is open, but the user must send an initial "CONNECT" message
    try:
        await register(websocket, user_id) # Register with temporary ID
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.ConnectionClosed:
        pass
    finally:
        await unregister(user_id) # Unregister on disconnect


async def main():
    """Starts the WebSocket server."""
    # This server binds to 0.0.0.0:8000 inside the container
    logging.info("Starting WebSocket Game Server on 0.0.0.0:8000")
    async with websockets.serve(game_handler, "0.0.0.0", 8000):
        await asyncio.Future() # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server shutting down.")