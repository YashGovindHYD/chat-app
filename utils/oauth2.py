from datetime import datetime, timedelta
from fastapi import (
    Depends,
    HTTPException,
    status,
    Request,
    WebSocket,
    WebSocketException,
)
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


# get current user in websocket
async def get_current_user_ws(
    websocket: WebSocket, db: AsyncSession = Depends(get_db)
) -> User:
    # type hinting for async session and websockets.
    """
    1) extract the authorization header.
    2) get the token from the header (token containing the cookie)
    2.5) if token doesnt exist . get the token from cookie, if that doesnt exist,  get the token as query parameter
    3) verify the validity
    4) find the user with that token id in db and return them
    """

    websocket_exception = WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Could not validate credentials",
    )

    token = websocket.headers["Authorization"]

    if token:
        token = token.split()[1]

    if token is None:
        # fallback to cookies
        # access the cookie named 'access_token' in this case, you can change it as per your requirement (you need a way of storing tokens somewhere). If not found then raise an exception or return None  depending on
        token = websocket.cookies["access_token"]

    if token is None:
        # fallback to query parameters.
        token = websocket.query_params["token"]

    # throw exception if still not found
    if token is None:
        raise websocket_exception

    token_data = verify_access_token(token)
    if not token_data:
        raise websocket_exception

    user = await db.get(User, token_data.user_id)
    if not user:
        raise websocket_exception

    return user
