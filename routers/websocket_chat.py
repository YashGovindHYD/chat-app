import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageResponse,
    User,
)
from routers.message import save_message
from utils.oauth2 import get_current_user_ws
from utils.websocket import ConnectionManager

router = APIRouter(prefix="/chat")
manager = ConnectionManager()


# for managing websocket connection. Websocket Endpoint and Handling Messages   .websocket() decorator is used for defining a new websocket endpoint. The path parameter in the URL corresponds to this function's
@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: int,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db)
):

    # connect to websocket, grouped by conversation so all members of the conversation share a broadcast group
    # # get data from client
    # save message to database
    # # add a check to ensure the sender is a member of the conversation
    # broadcast message to all connected sockets in the conversation

    await manager.connect(websocket, conversation_id)
    print("Connected to Websocket on Server")
    try:
        while True:
            # get the message from client or payload.
            data = await websocket.receive_json()
            message = await save_message(
                websocket,
                content=data["message"] ,
                conversation_id=conversation_id,
                db=db,
                current_user=current_user,
            )

            print(f"Data Recieved : {data['conversation_id']}:{data['message']}")
            # only members of this conversation may send messages
            # if the sender is not the current user, raise a policy violation exception
            stmt = (
                select(ConversationMember)
                .where(
                    ConversationMember.user_id == current_user.id,
                    ConversationMember.conversation_id == conversation_id,
                )
            )
            rs = await db.scalars(stmt)
            is_member = rs.first()
            if not is_member:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="You are not a member of this conversation",
                )


            # # broadcast to every socket connected to this conversation, not just the sender's own sockets
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
