import asyncio
import json
import logging
import os
import socket
import traceback
import urllib.request
from typing import Dict, Any, Optional, List

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.server import ServerProtocol
from Card import Card

# --- Configuration & Initialization ---

playerID = 0
playerPool = {}
numPlayers = 0
username = ""
currentTurnPlayerID = 0
USERS = {}
game_timer_started = False
game_timer_task = None

CURRENT_BATTLE = {
    "active": False,
    "answer": None,
    "winner": None,
    "players_answered": set()
}


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
DEFAULT_WORKER_CAPACITY = 5


def register_with_router():
    """
    Registers this worker with the router so it can be assigned games.
    Skips registration when ROUTER_URL is not provided (backwards compatible).
    """
    router_url = os.getenv("ROUTER_URL")
    if not router_url:
        logging.info("ROUTER_URL not set; skipping router registration.")
        return

    worker_id = os.getenv("WORKER_ID") or socket.gethostname()
    worker_host = os.getenv("WORKER_HOST", worker_id)
    worker_port = int(os.getenv("WORKER_PORT", os.getenv("PORT", "8000")))
    capacity = int(os.getenv("WORKER_CAPACITY", str(DEFAULT_WORKER_CAPACITY)))

    payload = {
        "worker_id": worker_id,
        "host": worker_host,
        "port": worker_port,
        "capacity": capacity,
    }

    url = f"{router_url.rstrip('/')}/workers/register"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            logging.info("Registered worker %s with router (%s): %s", worker_id, url, response.status)
    except Exception as exc:
        logging.warning("Could not register worker %s with router at %s: %s", worker_id, url, exc)


# --- WebSocket & Broadcast Logic ---
async def send_message(websocket: ServerProtocol, type: str, data: Dict):
    """Utility function to send structured JSON message, handling closed connections gracefully."""
    message = json.dumps({"type": type, "data": data})
    try:
        await websocket.send(message)
    except ConnectionClosed:
        # Log a warning if the connection is already closed when trying to send
        logging.warning(f"Connection closed while attempting to send message.")
    except Exception as e:
        # Catch other potential connection-related send errors
        logging.error(f"Unexpected error while sending message: {e}")


# NEW FUNCTION: Broadcast game state to all connected users
async def broadcast_game_state(game_id: str, state: Dict):
    
    websockets_to_send = list(USERS.values())
    if not websockets_to_send:
        logging.info("No connected users to broadcast to.")
        return
        
    logging.info(f"Broadcasting STATE_UPDATE for game {game_id} to {len(websockets_to_send)} users.")
    
    # We create a list of send tasks and run them concurrently
    messages = [send_message(ws, "STATE_UPDATE", state) for ws in websockets_to_send]
    await asyncio.gather(*messages, return_exceptions=True)


async def register(websocket: ServerProtocol, user_id: int, username: str):
    global game_timer_started
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

    if len(USERS) == 4 and not game_timer_started:
        game_timer_started = True
        game_timer_task = asyncio.create_task(start_game_timer())
        logging.info("4 players connected — game countdown triggered.")

    logging.info(f"User {username} with user_id={user_id} connected. Total users: {len(USERS)}")

    return user_id


async def unregister(user_id: int):
    """Unregister user by user_id."""
    if user_id in USERS:
        del USERS[user_id]
    if user_id in playerPool:
        # del playerPool[user_id]
        pass
    
    logging.info(f"User {user_id} disconnected. Total users: {len(USERS)}")

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
            user_id = await register(websocket, user_id, username)
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
            
            if currentTurnPlayerID == 0:
                currentTurnPlayerID = 1

            if int(payload.get("user_id")) == currentTurnPlayerID:
                card_value = payload.get("value")
                card_color = payload.get("color")
                card_operator = payload.get("operator")
                user_id = int(payload.get("user_id"))

                logging.info("Checking card")
                send_message(USERS[user_id], "STATUS", {"message": f"This is a test message"})
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

                    # Calculate the correct answer based on the operators
                    val1 = card1.value
                    val2 = card2.value
                    op = card1.operator

                    if op == '+':
                        CURRENT_BATTLE["answer"] = val1 + val2
                    elif op == '-':
                        CURRENT_BATTLE["answer"] = val1 - val2
                    elif op == '*':
                        CURRENT_BATTLE["answer"] = val1 * val2
                    elif op == '/':
                        if val2 != 0:
                            CURRENT_BATTLE["answer"] = val1 / val2
                        else:
                             CURRENT_BATTLE["answer"] = 0 # Handle div by zero gracefully

                    logging.info(f"BATTLE STARTED. Answer is: {CURRENT_BATTLE['answer']}")

                    # BROADCAST TO ALL PLAYERS
                    await send_message_to_all({
                        "type": "BATTLE",
                        "data": battle_state
                    })
                    # stops preccessing message whence a battle is started
                    return
                
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
            else:
                return await send_message(websocket, "STATUS", {"message": f"Not your turn. Current player: {currentTurnPlayerID}"})

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
            logging.info(f"Player {user_id} guessed: {user_answer}. Correct is: {CURRENT_BATTLE['answer']}")

            is_correct = False
            if user_answer is not None:
                if abs(float(user_answer) - float(CURRENT_BATTLE["answer"])) < 0.01:
                    is_correct = True

            if is_correct:
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
                
                # broadcast to all players here
                await broadcast_game_state(game_id, result_state)


                # Move turn logic
                next_player = get_next_player(user_id)
                currentTurnPlayerID = next_player
                await send_status_to_player(next_player, "It is now your turn.")

            return  # Stop further processing

    except json.JSONDecodeError:
        await send_message(websocket, "ERROR", {"message": "Invalid JSON format."})
    except Exception as e:
        # Note: The ConnectionClosed exception is now handled inside send_message
        traceback.print_exc()
        logging.error(f"Error handling message: {e}")
        if websocket:
            await send_message(websocket, "ERROR", {"message": "Server error."})
        
# Helper to broadcast raw dict to all
async def send_message_to_all(data: Dict):
    message = json.dumps(data)
    websockets_to_send = list(USERS.values())
    if websockets_to_send:
        # Create tasks for all sends
        await asyncio.gather(*[ws.send(message) for ws in websockets_to_send], return_exceptions=True)

#####GAME HANDLER#####
async def game_handler(websocket: ServerProtocol):
    """Main entry point for new WebSocket connections."""
    global USERS
    user_id = None
    try:
        # Wait for the client to send the user_id as part of the connection request
        async for message in websocket:
            data = json.loads(message)
            payload = data.get("payload")

            user_id = int(payload.get("user_id"))

            username = payload.get("username")

            if user_id in USERS:
                # If the user_id already exists, handle reconnect logic
                logging.info(f"Reconnecting existing user {user_id}")
                #await unregister(user_id)  # Clean up old connection

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
    global playerPool

  
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

        if operator == other.get("operator") and color == other.get("color"):
            # BATTLE detected!

            # FIX: Change Card.Card() to Card() because the class was imported directly
            card1 = Card() 
            card1.value = value
            card1.operator = operator

            # FIX: Change Card.Card() to Card()
            card2 = Card()
            card2.value = other.get("value")
            card2.operator = other.get("operator")

            return "BATTLE", card1, card2
            

    # If no battle found, return next state
    return "NEXT", None, None

def get_next_player(current_id):
    ids = sorted(playerPool.keys())
    # Safely handle the case where the player pool is empty or current_id is missing
    if not ids or current_id not in ids:
        return 0 # Return a default/safe ID or handle error appropriately
        
    idx = ids.index(current_id)
    return ids[(idx + 1) % len(ids)]

async def send_status_to_player(player_id: int, message: str):
    logging.info("Send status player ID: " + str(player_id))

    if player_id in USERS:
        ws = USERS[player_id]
        await send_message(ws, "STATUS", {"message": message})

async def start_game_timer():
    global game_timer_started
    logging.info("Countdown started (120 seconds).")
    
    await asyncio.sleep(15)

    # Broadcast START to all players
    message = {
        "type": "START",
        "data": {}
    }

    for ws in USERS.values():
        await send_message(ws, "START", {})
    logging.info("Game START message sent to all players.")


async def main():
    await asyncio.to_thread(register_with_router)
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
