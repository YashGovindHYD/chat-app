from fastapi import FastAPI, WebSocket

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = (
            {}
        )  # key is conversation id and value list of websockets connected to that particular conversation.

    async def connect(self, websocket: WebSocket, conversation_id: str) -> None:
        # if conversation has no connections yet , we create a connection list for storing sockets
        # then accept the client connection and add the websocket to the connection list
        if not conversation_id in self.connections:
            self.connections[conversation_id] = []
        await websocket.accept()
        self.connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        # if conversation doesnt exist and if the connection list is empty , we wont remove
        # else we remove the websocket from our list active connection.
        if not conversation_id in self.connections:
            return None
        if len(self.connections[conversation_id]) == 0:
            return None
        self.connections[conversation_id].remove(
            websocket
        )  # remove socket from connections list after disconnection or error occurred during connection establishment, etc...    .remove() method is used to delete the specific item present at that particular index in our self.]

    async def broadcast(self, conversation_id: str, message: str):
        # if the connection list is empty  we wont send a broadcast to all clients in the conversation
        # else we loop through the active connections and send a message to each one of them .
        if len(self.connections[conversation_id]) == 0:
            return None
        for conn in self.connections[conversation_id]:
            await conn.send_json(message)
