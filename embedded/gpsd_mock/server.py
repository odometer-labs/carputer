"""Mock gpsd TCP server that streams TPV data around city blocks."""

import json
import socketserver
import threading
import time as time_mod

from gpsd_mock.block_route import BlockRoute
from gpsd_mock.tpv_factory import make_tpv

_VERSION_MSG = {
    "class": "VERSION",
    "release": "3.25",
    "rev": "mock",
    "proto_major": 3,
    "proto_minor": 15,
}

_DEVICES_MSG = {
    "class": "DEVICES",
    "devices": [
        {
            "class": "DEVICE",
            "path": "/dev/ttyACM0",
            "driver": "u-blox",
            "activated": "2026-04-09T00:00:00.000Z",
        }
    ],
}


class _GpsdHandler(socketserver.StreamRequestHandler):
    """Handle a single gpsd client connection."""

    def handle(self):
        route: BlockRoute = self.server.route  # type: ignore[attr-defined]
        interval: float = self.server.interval  # type: ignore[attr-defined]

        # Send VERSION + DEVICES on connect
        self._send_json(_VERSION_MSG)
        self._send_json(_DEVICES_MSG)

        # Wait for ?WATCH command
        try:
            while True:
                line = self.rfile.readline()
                if not line:
                    return
                decoded = line.decode().strip().rstrip(";")
                if decoded.startswith("?WATCH"):
                    watch_echo = {"class": "WATCH", "enable": True, "json": True}
                    self._send_json(watch_echo)
                    break
        except (ConnectionError, OSError):
            return

        # Stream TPV at ~1 Hz
        t0 = time_mod.monotonic()
        while True:
            elapsed = time_mod.monotonic() - t0
            pos = route.position_at(elapsed)
            tpv = make_tpv(
                lat=pos["lat"],
                lon=pos["lon"],
                speed=pos["speed"],
                heading=pos["heading"],
            )
            try:
                self._send_json(tpv)
            except (ConnectionError, OSError, BrokenPipeError):
                return
            time_mod.sleep(interval)

    def _send_json(self, obj: dict):
        data = json.dumps(obj, separators=(",", ":")) + "\r\n"
        self.wfile.write(data.encode())
        self.wfile.flush()


class MockGpsdServer(socketserver.ThreadingTCPServer):
    """A mock gpsd server that streams city-block route TPV data."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 2947,
        speed_mps: float = 8.0,
        interval: float = 1.0,
    ):
        self.route = BlockRoute(speed_mps=speed_mps)
        self.interval = interval
        super().__init__((host, port), _GpsdHandler)
