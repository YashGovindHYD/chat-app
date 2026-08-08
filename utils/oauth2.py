from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import Settings, get_settings
from db.database import get_db
from models.models import TokenData, User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-otp", auto_error=False)


def create_access_token(user_id: int) -> str:
    try:
        # create a dictionary with the user_id and expiration time
        # encode the dictionary to a jwt token
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        encoded = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(
            encoded,
            key=settings.secret_key,
            algorithm=settings.algorithm,
        )
        # print("Encrypted JWT token : ", token)
        return token

    except JWTError as e:
        print(str(e))


def create_refresh_token(user_id: int) -> str:
    try:
        # same shape as the access token, but longer-lived and tagged
        # with type "refresh" so it can't be used as an access token
        expire = datetime.utcnow() + timedelta(
            minutes=settings.refresh_token_expire_minutes
        )
        encoded = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }
        token = jwt.encode(
            encoded,
            key=settings.secret_key,
            algorithm=settings.algorithm,
        )
        return token

    except JWTError as e:
        print(str(e))


def verify_access_token(token: str) -> TokenData:
    # decode the jwt token
    # extract the user id.
    # send token.
    try:
        payload = jwt.decode(
            token, key=settings.secret_key, algorithms=[settings.algorithm]
        )
        # print("Payload is : ", payload)
        user_id = payload.get("sub")
        token_data = TokenData(user_id=int(user_id))
        # print("Decoded Token data is  : ", token_data)
        return token_data
    except JWTError as e:
        print(str(e))


def verify_refresh_token(token: str) -> TokenData:

    # same as verify_access_token, but also reject a token unless it's
    # actually tagged as a refresh token
    try:
        payload = jwt.decode(
            token, key=settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        token_data = TokenData(user_id=int(user_id))
        return token_data
    except JWTError as e:
        print(str(e))


# authroization or protected routes../ helper
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # get token data from headers
    # if there is no authorization token then we get the token from cookies
    # get user from db and match user id with token data id
    # return user if found else throw exception

    # credentials exception.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if token is None:
            token = request.cookies.get("access_token")
            
        token_data = verify_access_token(token)
        if not token_data:
            raise credentials_exception  # Invalid or expired Token, so throw exception here..

        user = await db.get(User, token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail="User Not Found"
            )  # User doesnt exist in the database.
        return user
    except AttributeError:
        # verify_access_token returned None (invalid/expired token)
        raise credentials_exception
