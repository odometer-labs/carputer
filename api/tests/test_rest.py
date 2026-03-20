import json
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.model.models import Track

test_track = Track(id=123, start_time=datetime.now(), end_time=datetime.now())

client = TestClient(app)

# def test_get_track():
#     response = client.get("/v1/track/123")
#     assert response.status_code == 200

# def test_put_track():
#     payload = test_track.model_dump(mode='json')
#     response = client.put("/v1/track/123", json=payload)
#     assert response.status_code == 200

# def test_post_track():
#     payload = test_track.model_dump(mode='json')
#     response = client.post("/v1/track", json=payload)
#     assert response.status_code == 200

# def test_delete_track():
#     response = client.delete("/v1/track/123")
#     assert response.status_code == 200
#     assert response.json()["result"] == "success"