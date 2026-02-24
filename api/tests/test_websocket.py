from src.main import app
from fastapi.websockets import WebSocket
from fastapi.testclient import TestClient

client = TestClient(app)

def test_websocket_hello():
    with client.websocket_connect("/ws/hello") as ws:
        ws.send_text("knock knock")
        greeting = ws.receive_text()
        assert greeting == "Hello!"

def test_websocket_embedded():
    with client.websocket_connect("/ws/embedded") as ws:
        ws.send_text("knock knock")
        result = ws.receive_text()
        assert result == "PLACEHOLDER"