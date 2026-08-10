from fastapi import (
    APIRouter,
    WebSocket,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    WebSocketDisconnect,
)
import json
from utils.websocket import ConnectionManager
from models.models import User
from utils.oauth2 import get_current_user_ws

router = APIRouter(prefix="/chat")
manager = ConnectionManager()


# for managing websocket connection. Websocket Endpoint and Handling Messages   .websocket() decorator is used for defining a new websocket endpoint. The path parameter in the URL corresponds to this function's
@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    current_user: User = Depends(get_current_user_ws),
):
    # connect to websocket, grouped by conversation so all members of the conversation share a broadcast group
    await manager.connect(websocket, conversation_id)
    print("Connected to Websocket on Server")
    try:
        while True:
            # get the message from client or payload.
            data = await websocket.receive_json()

            print(f"Data Recieved : {data['user_id']}:{data['message']}")
            # data is a dictionary containing user_id & message from client
            message = {
                "sender_id": data["user_id"],
                "content": data["message"],
            }
            # broadcast to every socket connected to this conversation, not just the sender's own sockets
            await manager.broadcast(conversation_id, message)

            print(f"Message sent: {message['content']} By : {message['sender_id']}")
            # send it back on server side for all connected clients to receive this msg .
    except WebSocketDisconnect:
        # Client closed the connection
        print("Client disconnected")

    # always close the connection
    finally:
        manager.disconnect(
            websocket, conversation_id
        )  # remove client from connections list after disconnecting or error occurred during connect establishment, etc




