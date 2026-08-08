import uvicorn
from fastapi import FastAPI
from routers import auth,websocket,user

app = FastAPI()

app.include_router(auth.router)
app.include_router(user.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
