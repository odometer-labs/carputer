from datetime import datetime
from app.main import app
from fastapi.websockets import WebSocket
from fastapi.testclient import TestClient
from api.app.models.track import Track

client = TestClient(app)

test_track = Track(id=123, start_time=datetime.now(), end_time=datetime.now())

def test_websocket_hello():
    with client.websocket_connect("/ws/hello") as ws:
        ws.send_text("knock knock")
        greeting = ws.receive_text()
        assert greeting == "Hello!"

def test_websocket_embedded():
    with client.websocket_connect("/ws/embedded") as ws:
        # Send track as a serialized json string
        ws.send_text(test_track.model_dump_json())

        # Result should be a serialized json string
        result: str = ws.receive_text()
        assert result == test_track.model_dump_json()