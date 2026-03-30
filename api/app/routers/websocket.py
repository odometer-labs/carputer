import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..logging.handlers import logger
from ..clients.track_client import track_client

router = APIRouter(prefix="/ws")

@router.websocket("/get-position")
async def send_position(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text("Position")
            await asyncio.sleep(0.25)
    except WebSocketDisconnect as e:
        pass

@router.websocket("/update-position")
async def recv_position(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data: str = await websocket.receive_text() # data should be a json string
            await websocket.send_text(data)
    except WebSocketDisconnect as e:
        pass