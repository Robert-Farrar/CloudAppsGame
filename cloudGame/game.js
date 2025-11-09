 const WS_URL = "ws://localhost:8000"; // IMPORTANT: Change this to your Load Balancer URL in production
        let ws;
        let myUserId = crypto.randomUUID(); // Unique ID for this client session
        let currentGameId = "game_123"; // Mock game ID
        let gameState = {};
        
        // --- DOM Elements ---
        const connectionStatusEl = document.getElementById('connection-status');
        const userInfoEl = document.getElementById('user-info');
        const turnStatusEl = document.getElementById('turn-status');
        const lastCardDisplayEl = document.getElementById('last-card-display');
        const playerHandEl = document.getElementById('player-hand');
        const playerTurnStatusEl = document.getElementById('player-turn-status');
        const messageBoxEl = document.getElementById('message-box');

        // Helper to show temporary messages (not using alert())
        function showMessage(text, isError = false) {
            messageBoxEl.textContent = text;
            messageBoxEl.classList.remove('hidden');
            messageBoxEl.style.display = 'block';

            // Reset classes and apply new ones
            messageBoxEl.classList.remove('message-error', 'message-success');
            if (isError) {
                messageBoxEl.classList.add('message-error');
            } else {
                messageBoxEl.classList.add('message-success');
            }
            
            setTimeout(() => {
                messageBoxEl.style.display = 'none';
            }, 5000);
        }

        // --- WebSocket Connection ---

        function connectWebSocket() {
            if (ws && ws.readyState === WebSocket.OPEN) return;

            ws = new WebSocket(WS_URL);
            connectionStatusEl.textContent = "WebSocket: Connecting...";
            connectionStatusEl.style.color = 'var(--color-gray-500)';
            
            ws.onopen = () => {
                connectionStatusEl.textContent = "WebSocket: Connected";
                connectionStatusEl.style.color = 'var(--color-green-500)';
                
                // 1. Send initial CONNECT message to the server
                sendMessage("CONNECT", { user_id: myUserId, game_id: currentGameId });
                userInfoEl.textContent = `Your ID: ${myUserId.substring(0, 8)} | Game: ${currentGameId}`;
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                handleIncomingMessage(message);
            };

            ws.onclose = () => {
                connectionStatusEl.textContent = "WebSocket: Disconnected";
                connectionStatusEl.style.color = 'var(--color-red-600)';
                // Attempt to reconnect after a delay
                setTimeout(connectWebSocket, 5000); 
            };

            ws.onerror = (error) => {
                console.error("WebSocket Error:", error);
                connectionStatusEl.textContent = "WebSocket: Error";
                connectionStatusEl.style.color = 'var(--color-red-600)';
                // Display user-friendly error message in the UI
                showMessage(`Connection failed. Check if the backend server and load balancer are running and reachable at ${WS_URL}`, true);
            };
        }

        function sendMessage(type, payload) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                const message = JSON.stringify({ type, payload });
                ws.send(message);
            } else {
                showMessage("Connection not open. Cannot send message.", true);
            }
        }

        // --- Message Handling ---
        function handleIncomingMessage(message) {
            console.log("Received:", message);
            const { type, data } = message;

            if (type === "STATE_UPDATE") {
                gameState = data;
                renderGameState(gameState);
            } else if (type === "ERROR") {
                showMessage(`Server Error: ${data.message}`, true);
            } else {
                console.warn(`Unknown message type: ${type}`);
            }
        }
        
        // --- Game Actions ---
        function playCard(cardValue) {
            // Check if it's the player's turn (basic client-side check)
            if (gameState.current_turn !== myUserId) {
                return showMessage("It is not your turn to play!", true);
            }
            
            // Send the PLAY_CARD message to the server
            sendMessage("PLAY_CARD", { 
                user_id: myUserId, 
                game_id: currentGameId, 
                card: cardValue 
            });
            showMessage(`Attempting to play card: ${cardValue}`);
        }

        // --- Rendering ---
        
        // Mock hand data for initial render
        let playerHandData = [1, 5, 8, 3, 10]; 

        function renderGameState(state) {
            const isMyTurn = state.current_turn === myUserId;
            
            // Update Turn Status
            if (state.status === 'new') {
                turnStatusEl.textContent = "Game waiting for players...";
                turnStatusEl.style.color = 'var(--color-gray-700)';
            } else if (isMyTurn) {
                turnStatusEl.textContent = "YOUR TURN! Choose a card to play.";
                turnStatusEl.style.color = 'var(--color-secondary)';
                playerTurnStatusEl.textContent = "PLAY";
                playerTurnStatusEl.style.color = 'var(--color-green-500)';
            } else {
                turnStatusEl.textContent = `Waiting for ${state.current_turn.substring(0, 8)} to play...`;
                turnStatusEl.style.color = 'var(--color-gray-700)';
                playerTurnStatusEl.textContent = "WAIT";
                playerTurnStatusEl.style.color = 'var(--color-red-600)';
            }
            
            // Update Last Card Played
            const lastCardValue = state.last_card !== undefined ? state.last_card : '?';
            lastCardDisplayEl.innerHTML = `<span style="font-size: 1.875rem; font-weight: 700; color: white;">${lastCardValue}</span>`;
            
            // Use style property for background toggle
            if (lastCardValue !== '?') {
                lastCardDisplayEl.style.backgroundColor = 'var(--color-secondary)';
            } else {
                lastCardDisplayEl.style.backgroundColor = 'var(--color-gray-300)';
            }
            
            // Update Player Hand (simple redrawing)
            playerHandEl.innerHTML = '';
            playerHandData.forEach(card => {
                const cardEl = document.createElement('div');
                cardEl.className = `card card-main card-border-active ${isMyTurn ? '' : 'card-inactive'}`;
                cardEl.textContent = card;
                
                if (isMyTurn) {
                    cardEl.onclick = () => playCard(card);
                }
                playerHandEl.appendChild(cardEl);
            });
        }


        // --- Initialization ---
        window.onload = () => {
            // Start the WebSocket connection
            connectWebSocket();
            
            // Render the initial mocked state
            renderGameState({ status: 'new', players: [myUserId, 'opponent_id'], current_turn: myUserId });
        };