from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from models.models import OTP, OTPRequest, User, UserResponse, VerifyOtp, TokenResponse
from utils.hash import generate_otp, hash_otp, verify_otp_hash
from utils.oauth2 import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)  # importing oauth2 functions for handling tokens, refresh token etc..
from utils import send_email
from utils.send_email import send_otp_email
from utils.validators import is_valid_email
from config.config import get_settings


settings = get_settings()
router = APIRouter(prefix="/auth")


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Look up a user by their email address.

    Args:
        email (str): Email address to search for.
        db (AsyncSession): Active database session.

    Returns:
        User | None: The matching user if one exists, otherwise None.
    """
    stmt = select(User).where(User.email == email)
    result = await db.scalars(stmt)
    return result.first()


async def find_or_create_user(
    email: str, name: str, db: AsyncSession
) -> (
    User
):  # TODO replace with actual function and handle exceptions properly in real app scenario .name:strdb:AsyncSession):
    """Find an existing user by email, or create one if none exists.

    Args:
        email (str): Email address to look up or register.
        name (str): Display name to use if a new user needs to be created.
        db (AsyncSession): Active database session.

    Returns:
        User: The existing user if found, otherwise the newly created one.
    """
    # TODO : get the name and email from placeholder
    # TODO : if user is not found , create a new user.
    stmt = select(User).where(User.email == email)
    result = await db.scalars(stmt)
    user = result.first()
    if not user:
        new_user = User(email=email, name=name)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    return user


async def save_otp(email: str, db: AsyncSession, otp: str) -> OTP:
    """Hash a plaintext OTP code and persist it for later verification.

    Args:
        email (str): Email address the OTP belongs to.
        db (AsyncSession): Active database session.
        otp (str): Plaintext one-time-password code to hash and store.

    Returns:
        OTP: The newly created OTP row.
    """
    # hash the otp and save it in database.
    if not otp:
        raise HTTPException(
            status_code=401, detail="OTP not generated"
        )  # TODO replace with actual exception and detail in real app scenario .

    hashed_otp = hash_otp(otp)
    otp_row = OTP(email=email, hash=hashed_otp)
    db.add(otp_row)
    await db.commit()
    return otp_row


async def find_latest_otp_by_email(email: str, db: AsyncSession) -> OTP | None:
    """Fetch the most recently created OTP row for a given email.

    Args:
        email (str): Email address to look up OTP records for.
        db (AsyncSession): Active database session.

    Returns:
        OTP | None: The latest OTP row for this email, or None if none exist.
    """
    stmt = select(OTP).where(OTP.email == email).order_by(OTP.created_at.desc())
    result = await db.scalars(stmt)
    otp = result.first()
    return otp


@router.post("/get-otp", tags=["authentication"])
async def get_otp(payload: OTPRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Request a login OTP for the given email.

    Finds or creates the user for the given email, generates a new OTP,
    saves its hash, and emails the plaintext code to the user.

    Args:
        payload (OTPRequest): Request body containing the user's email and name.
        db (AsyncSession): Injected database session dependency.

    Returns:
        dict: Confirmation message indicating the OTP was sent.
    """
    # find user by their email and name and match the one given in payload
    # if user not found , create a new one in users table db
    # if user found  , generate otp , hash the otp and save it in otp's table db
    # send the otp via the mail only if email structure is valid.

    user = await find_or_create_user(payload.email, payload.name, db)
    otp = generate_otp()
    await save_otp(payload.email, db, otp)

    email = await send_otp_email(payload.email, otp)
    if not is_valid_email:
        raise HTTPException(status_code=403, detail="Invalid Email")

    return {"message": f"OTP {otp} SENT  to email {payload.email} SUCCESSFULLY"}


@router.post("/verify-otp", tags=["authentication"])
async def verify_otp(
    payload: VerifyOtp, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:  # type hinting for async session
    """Verify an OTP code and log the user in.

    Confirms the submitted OTP matches the latest stored hash for that
    email and hasn't expired, then issues access and refresh tokens as
    both httponly cookies and a response body.

    Args:
        payload (VerifyOtp): Request body containing the email and OTP code.
        response (Response): Injected response object, used to set auth cookies.
        db (AsyncSession): Injected database session dependency.

    Returns:
        TokenResponse: The newly issued access and refresh tokens.
    """
    # find user by their email as matched with the payload email given
    # find the latest otp by that email in otp's table and compare it with the one given in payload
    # if the otp is expired or doesnt match , raise exceptions
    # if the otp is found , generate access and refresh tokens and set them as cookies
    # alternatively we return these tokens in a TokenData object as well as a fallback.

    user = await get_user_by_email(payload.email, db)

    if not user:
        raise HTTPException(status_code=401, detail="user not found")

    otp_row = await find_latest_otp_by_email(payload.email, db)

    if otp_row is None or otp_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Invalid or Expired otp Code")

    is_found = verify_otp_hash(payload.otp_code, otp_row.hash)

    if not is_found:
        raise HTTPException(status_code=403, detail="Invalid or Expired otp Code ")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(
        user.id
    )  # generate refresh token for future use if needed by client
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
    )

    print(
        f"Access token created {refresh_token}, and refresh cookie set"
    )  # send back both tokens as response cookies for future reference by client
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )  # return TokenData object with all the data required by client to use in subsequent requests.


@router.post("/refresh", tags=["authentication"])
async def refresh(response: Response, request: Request) -> TokenResponse:
    """Issue a new access token using a valid refresh token.

    Reads the refresh token from the request cookies, validates it, and
    if valid, mints a fresh access token and sets it as a cookie.

    Args:
        response (Response): Injected response object, used to set the new access-token cookie.
        request (Request): Injected request object, used to read the refresh-token cookie.

    Returns:
        TokenResponse: The new access token alongside the still-valid refresh token.
    """
    # get token from cookie and send back new access_tokens if needed by client to use in subsequent requests .
    # get the refresh token cookie and validate them
    # if validated, then return new access_tokens else send error message to client

    # print('Refreshing tokens')
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=401, detail="Couldn't validate credentials"
        )  # raise error when no refresh cookie is present in request headers
    token_data = verify_refresh_token(refresh_token)

    if not token_data:
        raise HTTPException(
            status_code=401, detail="Invalid credentials"
        )  # raise error when refresh token is invalid or expired in request header

    # generate new tokens if needed by client to use for subsequent requests . (TODO: implement this)
    access_token = create_access_token(token_data.user_id)
    print(f"New Access Token is : {access_token}")

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )
    print(f"Access Token Cookie Set'")
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )  # send the access token in response header (TODO: implement this too). The client should include it for subsequent requests to identify itself as a valid user and not an unaut


# just delete the tokens stored in response header.
@router.delete("/logout", tags=["authentication"])
async def logout(response: Response) -> dict:
    """Log the user out by clearing their auth cookies.

    Args:
        response (Response): Injected response object, used to clear the auth cookies.

    Returns:
        dict: Confirmation message indicating logout succeeded.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Successfully Logged Out"}
