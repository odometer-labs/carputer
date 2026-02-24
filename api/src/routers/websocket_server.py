from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws")

@router.websocket("/hello")
async def root(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text("Hello!")
    except WebSocketDisconnect as e:
        pass

@router.websocket("/embedded")
async def embedded(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text("PLACEHOLDER")
    except WebSocketDisconnect as e:
        pass
