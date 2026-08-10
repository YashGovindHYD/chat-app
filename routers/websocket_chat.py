
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
from utils.websocket import ConnectionManager

router = APIRouter(prefix="/chat")
manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # connect to websocket
    await manager.connect(websocket,user_id)
    print("Connected to Websocket on Server")
    try:
        # get the message from client  , you want to send
        data = await websocket.receive_text()
        await manager.broadcast(
            user_id,data
        )  # send it back on server side for all connected clients to receive this msg .
        print(f'Client {user_id} received message : {data}')
    except WebSocketDisconnect:
        # Client closed the connection
        manager.disconnect(websocket,user_id) # remove client from connections list after disconnecting or error occurred during connect establishment, etc
        print("Client disconnected")
        await websocket.close()   # close WebSocket Connection when done with it to free up resources and prevent memory leakage on the server side 
