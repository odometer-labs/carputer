from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/ws")

@router.websocket("/hello")
async def ws_root(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text("Hello!")