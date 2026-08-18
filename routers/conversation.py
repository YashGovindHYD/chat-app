from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
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
    GroupWithMessagesResponse,
    Message,
    MessageResponse,
    User,
)
from utils.oauth2 import get_current_user

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

    member_ids = {user.id, *payload.member_id}
    for member_id in member_ids:
        member = ConversationMember(
            role="owner" if member_id == user.id else "member",
            conversation_id=conversation.id,
            user_id=member_id,
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)

    return GroupChatCreateResponse(
        **conversation.model_dump(), members=list(member_ids)
    )


# get the  conversation groups the current user owns along with conversation members
@router.get("/my-groups", response_model=list[GroupChatCreateResponse])
async def get_my_conversations(
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # get all conversation where user is the owner
    # join with conversation members to get the member details
    # join with users to get the member details
    # # for every conversation, aggregate the member ids into an array
    # group by conversation parameters to get unique conversations
    # stmt = (
    #     select(Conversation,func.array_agg(User.id).label("member_ids"))
    #     .where(Conversation.owner==user.id)
    #     .join(ConversationMember,ConversationMember.conversation_id==Conversation.id)
    #     .join(User,User.id==ConversationMember.user_id)
    #     .group_by(Conversation.id,Conversation.owner,Conversation.type)
    #     .limit(limit)
    # )
    # result = await db.execute(stmt)
    # conversations = result.all()
    # return [
    #     GroupChatCreateResponse(**conversation.model_dump(),members=member_ids)
    #     for conversation,member_ids in conversations
    # ]
    #
    #
    stmt = (
        select(Conversation)
        .where(Conversation.owner==user.id)
        .options(selectinload(Conversation.members))
        .limit(limit)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    return [
        GroupChatCreateResponse(
            **conversation.model_dump(),
            members=[member.user_id for member in conversation.members],
        )
        for conversation in conversations
    ]

 # groups with messages for the current user
@router.get("/my-groups-with-messages", response_model=list[GroupWithMessagesResponse])
async def get_my_groups_with_messages(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 20,
):
    stmt = (
        select(Conversation, func.array_agg(Message.content).label("messages"))
        .join(Message, Conversation.id == Message.conversation_id)
        .where(Message.user_id == user.id)
        .group_by(Conversation.id)
        .limit(limit)
    )
    # check if conversation member is part of conversation.
    stmt_01 = (
        select(ConversationMember)
        .where(ConversationMember.conversation_id == Conversation.id,
            ConversationMember.user_id == user.id)
    )
    rs = await db.scalars(stmt_01)
    if not rs.first():
        raise HTTPException(status_code=403, detail="Forbidden")
    rs_01 = await db.execute(stmt)
    groups_with_messages = rs_01.all()

    result = []
    for conversation, messages in groups_with_messages:

        group = GroupWithMessagesResponse(
            id=conversation.id,
            name=conversation.name,
            type=conversation.type,
            owner=conversation.owner,
            messages = messages
        )
        result.append(group)
    return result


# get all messages of a particular conversation
@router.get("/{conversation_id}")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 20,
):
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    # check if conversation member is part of conversation.
    stmt_01 = (
        select(ConversationMember)
        .where(ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user.id)
    )
    rs = await db.scalars(stmt_01)
    if not rs.first():
        raise HTTPException(status_code=403, detail="Forbidden")
    rs_01 = await db.scalars(stmt)
    return rs_01.all()
