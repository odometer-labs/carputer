"""Integration tests for the mock gpsd TCP server."""

import json
import socket
import threading
import time

import pytest

from gpsd_mock.server import MockGpsdServer


@pytest.fixture
def server():
    """Start mock gpsd server on an ephemeral port."""
    srv = MockGpsdServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)  # let server bind
    yield srv
    srv.shutdown()


def _connect(server: MockGpsdServer) -> socket.socket:
    """Helper: connect to the running mock server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(server.server_address)
    return sock


def _read_line(sock: socket.socket) -> dict:
    """Read one newline-terminated JSON object."""
    buf = b""
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Server closed")
        buf += chunk
        if buf.endswith(b"\n"):
            return json.loads(buf.decode())


class TestServerProtocol:
    def test_version_sent_on_connect(self, server):
        """gpsd sends VERSION as the first message on connect."""
        sock = _connect(server)
        msg = _read_line(sock)
        assert msg["class"] == "VERSION"
        sock.close()

    def test_devices_sent_after_version(self, server):
        """gpsd sends DEVICES as the second message on connect."""
        sock = _connect(server)
        _read_line(sock)  # VERSION
        msg = _read_line(sock)
        assert msg["class"] == "DEVICES"
        sock.close()

    def test_watch_command_echoed(self, server):
        """After ?WATCH, server echoes a WATCH response."""
        sock = _connect(server)
        _read_line(sock)  # VERSION
        _read_line(sock)  # DEVICES
        sock.sendall(b'?WATCH={"enable":true,"json":true};\r\n')
        msg = _read_line(sock)
        assert msg["class"] == "WATCH"
        sock.close()

    def test_tpv_stream_after_watch(self, server):
        """After WATCH, server should start streaming TPV messages."""
        sock = _connect(server)
        _read_line(sock)  # VERSION
        _read_line(sock)  # DEVICES
        sock.sendall(b'?WATCH={"enable":true,"json":true};\r\n')
        _read_line(sock)  # WATCH echo
        tpv = _read_line(sock)
        assert tpv["class"] == "TPV"
        assert "lat" in tpv
        assert "lon" in tpv
        assert "speed" in tpv
        assert "track" in tpv
        sock.close()

    def test_receives_multiple_tpv(self, server):
        """Should receive at least 2 distinct TPV messages."""
        sock = _connect(server)
        _read_line(sock)  # VERSION
        _read_line(sock)  # DEVICES
        sock.sendall(b'?WATCH={"enable":true,"json":true};\r\n')
        _read_line(sock)  # WATCH echo
        tpv1 = _read_line(sock)
        tpv2 = _read_line(sock)
        assert tpv1["class"] == "TPV"
        assert tpv2["class"] == "TPV"
        # Positions should differ slightly (moving in circle)
        assert not (tpv1["lat"] == tpv2["lat"] and tpv1["lon"] == tpv2["lon"])
        sock.close()
