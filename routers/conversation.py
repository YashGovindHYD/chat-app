from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from models.models import User , Conversation , Message , ConversationMember , MessageResponse
from config.config import get_settings
from utils.oauth2 import get_current_user
settings = get_settings()
router = APIRouter(prefix="/conversation") 
# instance of the router from fastapi import FastAPI and then we can use it to add our endpoints in application level or at a specific endpoint like /users,/messages etc...   
# for group conversations 
@router.post("/create-group" , response_model=Conversation)
async def create_group_chat(request:Request,db:AsyncSession = Depends(get_db) , user : User = Depends(get_current_user),):   
    pass# here user is the current logged in users and db will be our session to interact with database...   
