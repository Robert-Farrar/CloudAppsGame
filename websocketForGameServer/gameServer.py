import asyncio
import websockets
import json
import logging
# FIX 1: Use the explicit path for the server protocol class to resolve ImportError
from websockets.server import ServerProtocol
from typing import Dict, Any, Optional, List
import aiomysql 

# --- Configuration & Initialization ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Global database pool instance (essential for performance in async apps)
DB_POOL: Optional[aiomysql.Pool] = None

# Configuration variables (matching what you had for environment variables)
# DB_HOST remains 'mariadb' (the service name in docker-compose)
DB_HOST = "db"
DB_USER = "cloud"
DB_PASSWORD = "ThisIsThePassword1!"
DB_NAME = "cloudgame"         

# FIX 1: Use WebSocketServerProtocol for type hinting
USERS: Dict[str, ServerProtocol] = {} # {user_id: websocket}


async def init_db_pool():
    """
    Initializes the MariaDB connection pool using aiomysql with retry logic.
    Implements exponential backoff to handle the DB not being ready at server start.
    """
    global DB_POOL
    max_retries = 10
    base_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to MariaDB (Attempt {attempt + 1}/{max_retries})...")
            # Establish connection pool
            DB_POOL = await aiomysql.create_pool(
                host=DB_HOST,
                port=3306, # Explicitly use the default port
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                minsize=1,
                maxsize=10,
                autocommit=True # Ensure commits happen automatically for simple queries
            )
            logging.info(f"Successfully connected to MariaDB: {DB_NAME}")
            return
        except Exception as e:
            logging.warning(f"Failed to connect to MariaDB: {e}")
            if attempt + 1 == max_retries:
                logging.error("Exceeded max retries. Database connection failed permanently.")
                # Raise an error if the server can't connect to the DB after all retries
                raise RuntimeError("Database connection failed, server cannot start.") from e
            
            # Exponential backoff: 2s, 4s, 8s, 16s, ...
            delay = base_delay * (2 ** attempt)
            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

# --- Database Operations (Refactored to be Async) ---

async def fetch_game_state_from_db(game_id: str, player_id: str) -> Dict:
    """Retrieves game state and the specific player's hand from MariaDB asynchronously."""
    if not DB_POOL: return {"status": "error", "message": "Database not initialized."}

    try:
        async with DB_POOL.acquire() as conn:
            # Using DictCursor returns results as dictionaries, making them easy to use.
            async with conn.cursor(aiomysql.DictCursor) as cur:
                
                # 1. Fetch Game State
                await cur.execute(
                    "SELECT gameID, status, currentTurnPlayerID, lastCardPlayedValue FROM Game WHERE gameID = %s", 
                    (game_id,)
                )
                game_state = await cur.fetchone()

                if not game_state:
                    return {"status": "error", "message": f"Game {game_id} not found."}
                
                # 2. Fetch Player Hand (Cards in Deck linked to playerID)
                # NOTE: We use the Card table to get the full card details
                await cur.execute("""
                    SELECT c.cardID, c.cardValue, c.color, c.operation, d.deckID
                    FROM Deck d
                    JOIN Card c ON d.cardID = c.cardID
                    WHERE d.playerID = %s
                """, (player_id,))
                player_hand = await cur.fetchall()

                # 3. Combine results into a single state object
                game_state['player_hand'] = player_hand
                # Convert keys to match client expectation (e.g., game_id instead of gameID)
                final_state = {
                    "game_id": game_state['gameID'],
                    "status": game_state['status'],
                    "current_turn": game_state['currentTurnPlayerID'],
                    "last_card": game_state['lastCardPlayedValue'],
                    "player_hand": game_state['player_hand'],
                    # Mock players list since we only have the current player's ID for now
                    "players": [game_state['currentTurnPlayerID']],
                    "player_id": int(player_id) # Send back the ID used to fetch the hand
                }
                return final_state
                
    except Exception as e:
        logging.error(f"Async Error fetching game state: {e}")
        return {"status": "error", "message": "Failed to fetch game state from DB."}

async def persist_game_state_to_db(game_id: str, state: Dict, card_played_id: Optional[int] = None):
    """Saves game state to MariaDB asynchronously and optionally removes the played card from the Deck."""
    if not DB_POOL: 
        logging.error("Database not initialized. Cannot persist game state.")
        return

    try:
        async with DB_POOL.acquire() as conn:
            async with conn.cursor() as cur:
                # 1. Update Game table
                update_query = """
                    UPDATE Game 
                    SET status = %s, lastCardPlayedValue = %s, currentTurnPlayerID = %s
                    WHERE gameID = %s
                """
                await cur.execute(
                    update_query,
                    (
                        state.get("status", "active"), 
                        state.get("last_card", 0), 
                        state.get("current_turn"), 
                        game_id
                    )
                )

                # 2. Remove played card from the Deck (player's hand)
                if card_played_id is not None:
                    player_id_to_update = state.get("player_id") 
                    
                    if player_id_to_update:
                        # Delete the specific card from the player's hand (Deck table)
                        delete_query = """
                            DELETE FROM Deck 
                            WHERE playerID = %s AND cardID = %s 
                            LIMIT 1
                        """
                        # NOTE: We cast player_id_to_update to str as it comes from the DB as int but is passed to DB as string
                        await cur.execute(delete_query, (str(player_id_to_update), card_played_id)) 
                        logging.info(f"Removed cardID {card_played_id} from Player {player_id_to_update}'s hand.")

                await conn.commit()
                logging.info(f"Game {game_id} state persisted to MariaDB.")
    except Exception as e:
        logging.error(f"Async Error persisting game state: {e}")


# --- WebSocket & Broadcast Logic ---
# FIX 1: Use ServerProtocol for type hinting
async def send_message(websocket: ServerProtocol, type: str, data: Dict):
    """Utility function to send structured JSON message."""
    message = json.dumps({"type": type, "data": data})
    await websocket.send(message)

# NEW FUNCTION: Broadcast game state to all connected users
async def broadcast_game_state(game_id: str, state: Dict):
    """
    Sends the state update to all registered users.
    NOTE: In a real game, this should only send to users belonging to the specific game_id.
    """
    # For this conceptual implementation, we broadcast to ALL registered users.
    websockets_to_send = list(USERS.values())
    if not websockets_to_send:
        logging.info("No connected users to broadcast to.")
        return
        
    logging.info(f"Broadcasting STATE_UPDATE for game {game_id} to {len(websockets_to_send)} users.")
    
    # We create a list of send tasks and run them concurrently
    messages = [send_message(ws, "STATE_UPDATE", state) for ws in websockets_to_send]
    await asyncio.gather(*messages, return_exceptions=True)

# FIX 1: Use WebSocketServerProtocol for type hinting
async def register(websocket: ServerProtocol, user_id: str):
    """Handles new user registration and connection."""
    USERS[user_id] = websocket
    logging.info(f"User {user_id} connected. Total users: {len(USERS)}")

async def unregister(user_id: str):
    """Handles user disconnection."""
    if user_id in USERS:
        del USERS[user_id]
    logging.info(f"User {user_id} disconnected. Total users: {len(USERS)}")

# FIX 1: Use WebSocketServerProtocol for type hinting
async def handle_message(websocket: ServerProtocol, message: str):
    """Parses incoming message and executes game logic."""
    try:
        data = json.loads(message)
        msg_type = data.get("type")
        payload = data.get("payload", {})
        
        # User ID is mandatory for game actions
        user_id_str = payload.get("user_id") 
        game_id = payload.get("game_id")
        
        if not user_id_str or not user_id_str.isdigit():
             # For the mock setup, we assume user_id is the PlayerID (int=1)
            return await send_message(websocket, "ERROR", {"message": "Invalid or missing numeric user_id"})
        
        user_id = int(user_id_str)


        if msg_type == "CONNECT":
            await register(websocket, user_id_str)
            # Fetch and send the initial state for the known mock game (ID=1)
            initial_game_id = "1"
            initial_state = await fetch_game_state_from_db(initial_game_id, user_id_str)
            await send_message(websocket, "STATE_UPDATE", initial_state)
            await send_message(websocket, "STATUS", {"message": f"Connected and joined game {initial_game_id}. Turn: {initial_state.get('current_turn')}"})


        elif msg_type == "PLAY_CARD" and game_id:
            card_value = payload.get("card_value")
            card_id = payload.get("card_id")
            
            # 1. Fetch current state from MariaDB
            state = await fetch_game_state_from_db(game_id, user_id_str)
            
            # --- Conceptual Game Logic Execution ---
            if state.get("status") == "active" and user_id == state.get("current_turn"):
                
                # Mock update:
                state['last_card'] = card_value
                # NOTE: Swapping turn to PlayerID 2 for mock purposes
                state['current_turn'] = 2 
                state['player_id'] = user_id # Needed for persist to know which hand to update
                
                # 2. Save state back to MariaDB and remove the played card
                await persist_game_state_to_db(game_id, state, card_id)
                
                # 3. Re-fetch the updated state (now without the played card in hand)
                updated_state = await fetch_game_state_from_db(game_id, user_id_str)
                
                # 4. Broadcast the change to all players
                # In a real app, you would fetch each player's state separately and send
                await broadcast_game_state(game_id, updated_state)
                
                # 5. Send confirmation back to the client that played the card
                await send_message(websocket, "STATUS", {"message": f"Card {card_value} played. It is now turn {updated_state.get('current_turn')}"})
            else:
                await send_message(websocket, "ERROR", {"message": "Not your turn or game inactive."})
            # -------------------------------------

    except json.JSONDecodeError:
        await send_message(websocket, "ERROR", {"message": "Invalid JSON format."})
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await send_message(websocket, "ERROR", {"message": "Server error."})


# FIX 1: Use WebSocketServerProtocol for type hinting
async def game_handler(websocket: ServerProtocol, path: str):
    """Main entry point for new WebSocket connections."""
    # Use memory address as a temporary ID until the client sends a CONNECT message
    temp_user_id = str(id(websocket)) 

    try:
        # We wait for the client to send the CONNECT message with a proper user_id (PlayerID)
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.ConnectionClosed:
        pass
    finally:
        # Unregister happens when the socket closes
        await unregister(temp_user_id) 


async def main():
    """Starts the database pool and the WebSocket server."""
    await init_db_pool() # Initialize DB pool before starting the server
    
    logging.info("Starting Async WebSocket Game Server with MariaDB on 0.0.0.0:8000")
    # CRITICAL: Server listens on all interfaces (0.0.0.0) on port 8000 for Docker/Load Balancer
    async with websockets.serve(game_handler, "0.0.0.0", 8000):
        await asyncio.Future() 

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Catches the RuntimeError if DB connection fails in init_db_pool
        logging.error(f"FATAL: {e}")
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
