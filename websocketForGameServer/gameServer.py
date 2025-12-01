import asyncio
import websockets
import json
import logging
from websockets.server import ServerProtocol
from typing import Dict, Any, Optional, List
import aiomysql 
from Card import Card
import traceback

# --- Configuration & Initialization ---

playerID = 0
playerPool = {}
numPlayers = 0
username = ""
currentTurnPlayerID = 0

CURRENT_BATTLE = {
    "active": False,
    "answer": None,
    "winner": None,
    "players_answered": set()
}


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
                final_state = {
                    "game_id": game_state['gameID'],
                    "status": game_state['status'],
                    "current_turn": game_state['currentTurnPlayerID'],
                    "last_card": game_state['lastCardPlayedValue'],
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
async def register(websocket: ServerProtocol, user_id: str, username: str):
    """Handles new user registration and connection and stores player details."""
    global playerID, playerPool, numPlayers
    
    # Extract client IP
    client_ip, client_port = websocket.remote_address

    # Increment playerID counter
    playerID += 1

    #Increment total player counter
    numPlayers += 1

    # Add to USERS
    USERS[playerID] = websocket

    # Add player data to playerPool
    playerPool[playerID] = {
        "ip": client_ip,
        "port": client_port,
        "points": 0,
        "username": username,
        "card": {}

    }

    logging.info(
        f"User {playerID} connected from {client_ip}. "
        f"Assigned playerID={playerID}. Total users: {len(USERS)}"
    )


async def unregister(user_id):
    user_id = user_id  # normalize
    if user_id in USERS:
        del USERS[user_id]
    logging.info(f"User {user_id} disconnected. Total users: {len(USERS)}")

async def get_player_by_ip(ip: str) -> Optional[int]:
    """Finds the player_id of a connected user by IP address."""
    for pid, pdata in playerPool.items():
        if pdata.get("ip") == ip:
            return pid
    return None

# FIX 1: Use WebSocketServerProtocol for type hinting
async def handle_message(websocket: ServerProtocol, message: str):
    """Parses incoming message and executes game logic."""
    try:
        data = json.loads(message)
        msg_type = data.get("type")
        payload = data.get("payload", {})
        
        # User ID is mandatory for game actions
        user_id_str = payload.get("user_id", "") 
        game_id = payload.get("game_id", "")


        if not user_id_str or not user_id_str.isdigit():
             # For the mock setup, we assume user_id is the PlayerID (int=1)
            return await send_message(websocket, "ERROR", {"message": "Invalid or missing numeric user_id"})
        
        user_id = int(user_id_str)


        if msg_type == "CONNECT":
            username = payload.get("username")
            await register(websocket, user_id_str, username)
            initial_game_id = "1"
            await send_message(websocket, "STATUS", {"message": f"Connected and joined game {initial_game_id}."})


        elif msg_type == "PLAY_CARD" and game_id:
            global currentTurnPlayerID
            card_value = None 
            card_color = None 
            card_operator = None 
            user_id = None
            if currentTurnPlayerID == 0:
                currentTurnPlayerID = 1

            if int(payload.get("user_id")) == currentTurnPlayerID:
                card_value = payload.get("value")
                card_color = payload.get("color")
                card_operator = payload.get("operator")
                user_id = int(payload.get("user_id"))

            logging.info("Checking card")
            event, card1, card2 = await checkCard(card_value, card_color, card_operator, user_id)
            logging.info(event)
            if event == "BATTLE":
                battle_state = {
                    "type": "BATTLE",
                    "card1_value": card1.value,
                    "card1_operator": card1.operator,
                    "card2_value": card2.value,
                    "card2_operator": card2.operator
                }

                CURRENT_BATTLE["active"] = True
                CURRENT_BATTLE["winner"] = None
                CURRENT_BATTLE["answer"] = None
                CURRENT_BATTLE["players_answered"].clear()
                if card1_operator == '+':
                    CURRENT_BATTLE["answer"] = card1.value + card2.value
                elif card1_operator == '-':
                    CURRENT_BATTLE["answer"] = card1.value - card2.value
                elif card1_operator == '*':
                    CURRENT_BATTLE["answer"] = card1.value * card2.value
                elif card1_operator == '/':
                    CURRENT_BATTLE["answer"] = card1.value - card2.value

                # BROADCAST TO ALL PLAYERS
                await broadcast_game_state(game_id, battle_state)

            elif event == "NEXT":
                # 1. Notify current player that their turn is over
                await send_status_to_player(user_id, "Your turn has ended.")

                # 2. Determine next player
                next_player = get_next_player(user_id)
                # 3. Update turn tracker
                currentTurnPlayerID = next_player

                # 4. Notify next player
                await send_status_to_player(next_player, "It is now your turn.")

            return  # Stop further processing
        
        elif msg_type == "ANSWER":
            if not CURRENT_BATTLE["active"]:
                return await send_message(websocket, "STATUS", {"message": "No active battle."})

            # Prevent double answers
            if user_id in CURRENT_BATTLE["players_answered"]:
                return await send_message(websocket, "STATUS", {"message": "You already answered."})

            CURRENT_BATTLE["players_answered"].add(user_id)

            # If winner already exists → ignore
            if CURRENT_BATTLE["winner"] is not None:
                return await send_message(websocket, "STATUS", {
                    "message": f"Player {CURRENT_BATTLE['winner']} already won the battle."
                })

            user_answer = payload.get("answer")

            if user_answer == CURRENT_BATTLE["answer"]:
                if CURRENT_BATTLE["winner"] is None:
                    CURRENT_BATTLE["winner"] = user_id
                    CURRENT_BATTLE["active"] = False  # battle ends

                # Award point (example)
                playerPool[user_id]["points"] = playerPool[user_id].get("points", 0) + 1

                result_state = {
                    "type": "BATTLE_RESULT",
                    "winner_id": user_id,
                    "correct_answer": CURRENT_BATTLE["answer"],
                    "points": playerPool[user_id]["points"]
                }

            # 1. Notify current player that their turn is over
            await send_status_to_player(user_id, "Your turn has ended.")

            # 2. Determine next player
            next_player = get_next_player(user_id)

            # 3. Update turn tracker
            currentTurnPlayerID = next_player

            # 4. Notify next player
            await send_status_to_player(next_player, "It is now your turn.")

            return  # Stop further processing
                # ---------------------------------------------------------
        #   NEW: REQUEST_DATA  → return user_id + game_id by IP
        # ---------------------------------------------------------
        if msg_type == "REQUEST_DATA":
            client_ip, client_port = websocket.remote_address

            # Try to find an existing player by IP
            pid = await get_player_by_ip(client_ip)
            USERS[pid] = websocket
            if pid is None:
                return await send_message(websocket, "REQUEST_DATA", {
                    "status": "error",
                    "message": "Player not found for this IP.",
                    "ip": client_ip
                })

            # Game ID is currently static, but scalable later
            game_id = 1

            return await send_message(websocket, "REQUEST_DATA", {
                "status": "ok",
                "user_id": pid,
                "game_id": game_id,
                "ip": client_ip
            })


        else:
            return await send_message(websocket, "STATUS", {"message": "Incorrect answer!"})

                


    except json.JSONDecodeError:
        await send_message(websocket, "ERROR", {"message": "Invalid JSON format."})
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Error handling message: {e}")
        await send_message(websocket, "ERROR", {"message": "Server error."})


# FIX 1: Use WebSocketServerProtocol for type hinting
async def game_handler(websocket: ServerProtocol):
    """Main entry point for new WebSocket connections."""
    try:
        # Remove stale websocket for this IP if it exists
        client_ip = websocket.remote_address[0]
        old_player = await get_player_by_ip(client_ip)
        if old_player is not None:
            await unregister(old_player)

        # Now wait for client messages
        async for message in websocket:
            await handle_message(websocket, message)

    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError:
        pass
    finally:
        # Clean up on disconnect
        client_ip = websocket.remote_address[0]
        player_id = await get_player_by_ip(client_ip)

        if player_id is not None:
            await unregister(player_id)


async def checkCard(value, color, operator, player_id):

    logging.info("Player ID: " + str(player_id))

    # 1. Store the card for this player
    playerPool[player_id]["card"] = {
        "value": value,
        "color": color,
        "operator": operator
    }

    # 2. Compare against every other player
    for pid, player in playerPool.items():

        if pid == player_id:
            continue  # skip ourselves

        other = player.get("card")
        if not other:
            continue

        if value == other.get("value") and color == other.get("color"):
            # BATTLE detected!

            card1 = Card.Card()
            card1.value = value
            card1.operator = operator

            card2 = Card.Card()
            card2.value = other.get("value")
            card2.operator = other.get("operator")

            return "BATTLE", card1, card2
            

    # If no battle found, return next state
    return "NEXT", None, None

def get_next_player(current_id):
    ids = sorted(playerPool.keys())
    idx = ids.index(current_id)
    return ids[(idx + 1) % len(ids)]

async def send_status_to_player(player_id: int, message: str):
    if player_id in USERS:
        ws = USERS[player_id]
        client_ip, client_port = ws.remote_address
        await send_message(ws, "STATUS", {"message": message})



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