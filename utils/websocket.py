from fastapi import FastAPI, WebSocket

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = (
            {}
        )  # key is user id and value list of websockets connected to that particular User.

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        # if user is not connected yet , we create a connection list for storing users
        # if user exists , accept the client connection and then we add the websocket to the connection list
        if not user_id in self.connections:
            self.connections[user_id] = []
        await websocket.accept()
        self.connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        # if user doesnt exist and if the connection list is empty , we wont remove
        # else we remove the websocket from our list active connection.
        if not user_id in self.connections:
            return None
        if len(self.connections[user_id]) == 0:
            return None
        self.connections[user_id].remove(
            websocket
        )  # remove user from connections list after disconnection or error occurred during connection establishment, etc...    .remove() method is used to delete the specific item present at that particular index in our self.]

    async def broadcast(self, user_id: str, message: str):
        # if the connection list is empty  we wont send a broadcast to all users
        # else we loop through the active connections and send a message to each one of them .
        if len(self.connections[user_id]) == 0:
            return None
        for conn in self.connections[user_id]:
            await conn.send_text(message)
