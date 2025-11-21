// Connect to the Python WebSocket server running on localhost port 8001
const websocket = new WebSocket("0.0.0.0:8000"); //Whatever the ip in the docker is

websocket.onopen = () => {
    console.log("WebSocket connection established.");
    // Send a message
    websocket.send(JSON.stringify({type: "CONNECT", data: window.getCardById}));
};

websocket.onmessage = (event) => {
    const receivedMsg = JSON.parse(event.data);
    console.log("Received message:", receivedMsg);
};

websocket.onerror = (error) => {
    console.error("WebSocket error:", error);
};

websocket.onclose = () => {
    console.log("WebSocket connection closed.");
};
