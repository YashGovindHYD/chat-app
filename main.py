import uvicorn
from fastapi import FastAPI
from routers import auth, websocket_chat, user,conversation

app = FastAPI()

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(conversation.router)
app.include_router(
    websocket_chat.router
)  # this should be the last router to include in case of any routing errors  .include() method is used for including routers into FastAPI application instance..rou


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
