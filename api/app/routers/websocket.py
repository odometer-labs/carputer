import asyncio
import json
from gpsdclient import GPSDClient
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..logging.handlers import logger
from ..clients.track_client import track_client

router = APIRouter(prefix="/ws")

@router.get("/get-current-pos")
async def get_pos():
    return track_client

@router.websocket("/get-position")
async def send_position(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = {
                "latitude": track_client.latitude,
                "longitude": track_client.longitude,
                "speed": track_client.speed,
                "heading": track_client.heading
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.25)
    except WebSocketDisconnect as e:
        pass

@router.websocket("/update-position")
async def recv_position(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data: str = await websocket.receive_text() # gpsd data should be a json string
            gpsd: dict = json.loads(data)

            # Real gpsd TPV packets omit lat/lon/speed/track when there is no fix
            if "lat" not in gpsd or "lon" not in gpsd:
                continue

            track_client.latitude = gpsd.get("lat", track_client.latitude)
            track_client.longitude = gpsd.get("lon", track_client.longitude)
            track_client.speed = gpsd.get("speed", track_client.speed)
            track_client.heading = gpsd.get("track", track_client.heading)
    except WebSocketDisconnect as e:
        pass