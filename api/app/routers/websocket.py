import asyncio
import json
from gpsdclient import GPSDClient
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..logging.handlers import logger
from ..clients.track_client import track_client

router = APIRouter(prefix="/ws")

@router.websocket("/get-position")
async def send_position(websocket: WebSocket):
    await websocket.accept()
    with GPSDClient() as gpsd_client:
        try:
            while True:
                await websocket.send_text(gpsd_client.dict_stream(convert_datetime=True, filter=["TPV", "SKY"])[-1])
                await asyncio.sleep(0.25)
        except WebSocketDisconnect as e:
            pass

# @router.websocket("/update-position")
# async def recv_position(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data: str = await websocket.receive_text() # gpsd data should be a json string
#             gpsd = json.loads(data)

#             track_client.latitude = gpsd["lat"]
#             track_client.longitude = gpsd["lon"]
#             track_client.speed = gpsd["speed"]
#             track_client.heading = gpsd["track"]
#     except WebSocketDisconnect as e:
#         pass