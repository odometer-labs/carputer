from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..logging.handlers import logger

router = APIRouter(prefix="/ws")

@router.websocket("/hello")
async def root(websocket: WebSocket):
    await websocket.accept()
    logger.info("Got hello!")
    try:
        while True:
            data: str = await websocket.receive_text()
            await websocket.send_text("Hello!")
    except WebSocketDisconnect as e:
        pass

@router.websocket("/embedded")
async def embedded(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data: str = await websocket.receive_text() # data should be a json string
            await websocket.send_text(data)
    except WebSocketDisconnect as e:
        pass