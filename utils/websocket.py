from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import os 
import uvicorn
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        
        async def connect(self,websocket:WebSocket):
            pass 
        
        def disconnect(self,websocket:WebSocket):
            pass 
        
        async def broadcast(self,websocket:WebSocket,message:str):
            pass