from datetime import datetime
import json
from app.main import app
from fastapi.websockets import WebSocket
from fastapi.testclient import TestClient
from app.models.track import Track
from app.clients.track_client import TrackClient

client = TestClient(app)

test_track = Track(id=123, start_time=datetime.now(), end_time=datetime.now())

# def test_websocket_position_recv():
#     with client.websocket_connect("/ws/get-position") as ws:
#         greeting = ws.receive_text()
#         assert len(greeting) != 0

# def test_websocket_embedded():
#     # Update position
#     with client.websocket_connect("/ws/update-position") as ws:
#         # Send test gpsd data
#         data = {
#             "lat": 45.523064,
#             "lon": -122.676483,
#             "speed": 2.34,
#             "track": 270.5
#         }

#         ws.send_text(json.dumps(data))

#         # track client test obj
#         track_client: TrackClient = TrackClient()
#         track_client.latitude = data["lat"]
#         track_client.longitude = data["lon"]
#         track_client.speed = data["speed"]
#         track_client.heading = data["track"]
    
#     # Validate
#     with client.websocket_connect("/ws/get-position") as ws:
#         greeting = ws.receive_text()
#         assert greeting == json.dumps(track_client.__dict__)

# def test_gpsd_client():
#     with GPSDClient(host="127.0.0.1") as client:
#         for result in client.json_stream():
#             print(result)