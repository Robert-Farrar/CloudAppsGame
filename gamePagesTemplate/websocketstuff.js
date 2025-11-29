
// Connect to the Python WebSocket server running on localhost port 8001
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsHost = window.location.hostname;
const wsPath = '/ws/';
const websocket = new WebSocket('${wsProtocol}://${wshost}${wsPath}'); //Whatever the ip in the docker is

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
