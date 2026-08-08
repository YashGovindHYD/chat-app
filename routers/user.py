from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from config.config import get_settings
from db.database import get_db
from models.models import User , UserResponse
from utils.oauth2 import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

router = APIRouter(prefix="/users")

@router.get("/me" , tags = ["users"] , response_model=UserResponse)
async def get_auth_user(current_user:User=Depends(get_current_user))->User:
    return current_user