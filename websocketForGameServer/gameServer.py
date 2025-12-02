import asyncio
import websockets
import json
import logging
from websockets.server import ServerProtocol
from typing import Dict, Any, Optional, List
from Card import Card
import traceback

# --- Configuration & Initialization ---

playerID = 0
playerPool = {}
numPlayers = 0
username = ""
currentTurnPlayerID = 0
USERS = {}

CURRENT_BATTLE = {
    "active": False,
    "answer": None,
    "winner": None,
    "players_answered": set()
}


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


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
    """Handles new user registration and connection based on user_id."""
    global playerID, playerPool, numPlayers

    if user_id == 0:
        playerID += 1
        user_id = playerID
    logging.info(f"Registering user {username} with user_id={user_id}")

    # Add to USERS dictionary using user_id
    USERS[user_id] = websocket

    # Add player data to playerPool using user_id as key
    playerPool[user_id] = {
        "username": username,
        "points": 0,
        "card": {},  # Card data for the player
    }

    logging.info(f"User {username} with user_id={user_id} connected. Total users: {len(USERS)}")

    return user_id


async def unregister(user_id: str):
    """Unregister user by user_id."""
    if user_id in USERS:
        del USERS[user_id]
    if user_id in playerPool:
        del playerPool[user_id]
    
    logging.info(f"User {user_id} disconnected. Total users: {len(USERS)}")

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

        user_id = int(user_id_str)


        if msg_type == "CONNECT":
            username = payload.get("username")
            user_id = await register(websocket, user_id_str, username)
            initial_game_id = "1"
            
            USERS[user_id] = websocket

            # Send back CONNECTED message with user_id
            response = {
                "type": "CONNECTED",
                "data": {
                    "user_id": user_id
                }
            }
            await websocket.send(json.dumps(response))  # Send the response back to the client
            print(f"User {username} connected with user_id={user_id}")


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

                logging.info("Next Player ID: " + str(next_player))

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
            logging.info("Current Turn Player ID: " + str(currentTurnPlayerID))
            # 4. Notify next player
            await send_status_to_player(next_player, "It is now your turn.")

            return  # Stop further processing

                


    except json.JSONDecodeError:
        await send_message(websocket, "ERROR", {"message": "Invalid JSON format."})
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Error handling message: {e}")
        await send_message(websocket, "ERROR", {"message": "Server error."})


async def game_handler(websocket: ServerProtocol):
    """Main entry point for new WebSocket connections."""
    global USERS
    user_id = None
    try:
        # Wait for the client to send the user_id as part of the connection request
        async for message in websocket:
            data = json.loads(message)
            payload = data.get("payload")

            user_id_str = payload.get("user_id")

            logging.info(user_id_str)

            username = payload.get("username")
            
            user_id = int(user_id_str)

            if user_id in USERS:
                # If the user_id already exists, handle reconnect logic
                logging.info(f"Reconnecting existing user {user_id}")
                await unregister(user_id)  # Clean up old connection

                # Register the new user (or reconnecting)
                await register(websocket, user_id, username)

            # Now handle game messages after registration
            await handle_message(websocket, message)

    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError:
        pass
    finally:
        if user_id:
            await unregister(user_id)
            


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
    logging.info("Send status player ID: " + str(player_id))

    if player_id in USERS:
        ws = USERS[player_id]
        await send_message(ws, "STATUS", {"message": message})



async def main():
    
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