from models.models import GroupChatCreate
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.database import get_db
from sqlalchemy import func

from models.models import (
    User,
    Conversation,
    Message,
    ConversationMember,
    MessageResponse,
    GroupChatCreateResponse,
)
from config.config import get_settings
from utils.oauth2 import get_current_user
from fastapi import Query

settings = get_settings()
router = APIRouter(prefix="/conversation")


# instance of the router from fastapi import FastAPI and then we can use it to add our endpoints in application level or at a specific endpoint like /users,/messages etc...
# for group conversations
@router.post("/create-group", response_model=GroupChatCreateResponse)
async def create_group_chat(
    payload: GroupChatCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # add conversation to db
    # for each conversation_member_id in payload , create and add in db
    # here user is the current logged in users and db will be our session to interact with database...
    conversation = Conversation(
        name=payload.name, type="group-chat", owner=user.id
    )  # here we are initializing the data to be stored in our database...  and then storing it into db session.........     user_id=user.id)   # creating a new instance of Conversations model. This represents one chat room for group conversations..
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    for member_id in list(payload.member_id):
        member = ConversationMember(
            role="member", conversation_id=conversation.id, user_id=member_id
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)

    return GroupChatCreateResponse(
        **conversation.model_dump(), members=list(payload.member_id)
    )


# get the  conversation groups the current user owns along with conversation members
@router.get("/my-groups", response_model=list[GroupChatCreateResponse])
async def get_my_conversations(
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # get all conversation where user is the owner
   pass 
