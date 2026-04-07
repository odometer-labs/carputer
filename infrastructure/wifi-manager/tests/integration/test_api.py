from uuid import UUID
from time import sleep


TEST_CONNECTION = {
    "hotspot": False,
    "connection_id": "test connection",
    "ssid": "test123",
    "password": "password123",
    "static_config": None,
}

TEST_HOTSPOT = {
    "hotspot": True,
    "connection_id": "test hotspot",
    "ssid": "oof",
    "password": "assword123",
    "static_config": None,
}


def test_create_and_get_connection(client):

    response = client.put("/wifi/connection", json=TEST_CONNECTION)
    assert response.status_code == 200

    response = client.get("/wifi/connection")
    assert response.status_code == 200
    body = response.json()
    for key in TEST_CONNECTION.keys():
        if key == "password":
            # Password should be redacted
            assert body[key] == "*" * 10
        elif key == "uuid":
            UUID(body[key])  # check if valid uuid
        else:
            assert body[key] == TEST_CONNECTION[key]

    response = client.get("/wifi/connection/saved")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1, "Created connection should be the only saved connection"
    body = body[0]
    for key in TEST_CONNECTION.keys():
        if key == "password":
            assert body[key] == "*" * 10
        elif key == "uuid":
            UUID(body[key])
        else:
            assert body[key] == TEST_CONNECTION[key]

    response = client.delete(f"/wifi/connection?uuid={body['uuid']}")
    assert response.status_code == 200


def test_delete_connection(client):
    put_response = client.put("/wifi/connection", json=TEST_CONNECTION)
    assert put_response.status_code == 200

    get_response = client.get("/wifi/connection")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["connection_id"] == TEST_CONNECTION["connection_id"]

    delete_response = client.delete(f"/wifi/connection/clear")
    assert delete_response.status_code == 200

    sleep(3)

    get_response = client.get("/wifi/connection")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body == None


def test_get_access_points(client):
    response = client.get("/wifi/access-points")
    body = response.json()
    assert len(body) == 0

    put_response = client.put("/wifi/connection", json=TEST_HOTSPOT)
    assert put_response.status_code == 200

    response = client.get("/wifi/access-points")
    body = response.json()
    assert len(body) == 1
    body = body[0]
    assert body["ssid"] == TEST_HOTSPOT["ssid"]
    assert body["security"] == "wpa-psk"

    delete_response = client.delete(f"/wifi/connection/clear")
    assert delete_response.status_code == 200

    sleep(1)

    response = client.get("/wifi/access-points")
    body = response.json()
    assert len(body) == 0


def test_activate_deactivate_connection(client):
    response = client.put("/wifi/connection", json=TEST_HOTSPOT)
    assert response.status_code == 200

    response = client.get("/wifi/connection")
    assert response.status_code == 200
    body = response.json()
    assert body != None
    assert body["connection_id"] == TEST_HOTSPOT["connection_id"]
    connection_uuid = body["uuid"]

    response = client.put(f"/wifi/connection/deactivate")
    assert response.status_code == 200

    sleep(1)

    response = client.get("/wifi/connection")
    assert response.status_code == 200
    body = response.json()
    assert body == None

    response = client.get("wifi/connection/saved")
    body = response.json()
    assert len(body) == 1

    response = client.put(f"/wifi/connection/activate?uuid={connection_uuid}")
    assert response.status_code == 200

    sleep(1)

    response = client.get("/wifi/connection")
    assert response.status_code == 200
    body = response.json()
    assert body != None
    assert body["connection_id"] == TEST_HOTSPOT["connection_id"]
