from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.config import get_settings
from db.database import get_db
from models.models import (
    Conversation,
    ConversationMember,
    GroupChatCreate,
    GroupChatCreateResponse,
    Message,
    MessageResponse,
    User,
)
from utils.oauth2 import get_current_user
from utils.websocket import ConnectionManager

settings = get_settings()
router = APIRouter(prefix="/messages")

# save message to database
@router.post("/")
async def save_message(
    websocket:WebSocket,
    content:str,
    conversation_id:int,
    db:AsyncSession = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    message = Message(
        content=content,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return {
        "id": message.id,
        "content": message.content,
        "sender_id": message.user_id,
    }
