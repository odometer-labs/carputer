import os
import sys
import logging

from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException

import wifi_manager as wm
from wifi_manager import WifiConnectionSettings, WifiAccessPoint


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

log = logging.getLogger(__name__)


_env_wifi_interface = os.environ.get("WIFI_INTERFACE")
if not _env_wifi_interface:
    WIFI_INTERFACE: str = "wlan0"
else:
    WIFI_INTERFACE: str = _env_wifi_interface


app = FastAPI()


def open_system_bus():
    yield wm.setup_system_bus()


@app.get("/wifi/version")
def get_version_info() -> dict:
    return {"version": "0.1.0", "service": "wifi-manager"}


@app.put("/wifi/connection")
def create_and_activate_connection(
    settings: WifiConnectionSettings, _=Depends(open_system_bus)
):
    log.info(
        f"Creating new connection: hotspot={settings.hotspot} id={settings.connection_id}, ssid={settings.ssid}"
    )
    wm.add_and_activate_connection(settings, WIFI_INTERFACE)


@app.get("/wifi/connection")
def get_current_active_connection(
    _=Depends(open_system_bus),
) -> Optional[WifiConnectionSettings]:
    return wm.get_primary_connection_settings(WIFI_INTERFACE)


@app.delete("/wifi/connection")
def delete_connection_by_id(uuid: UUID, _=Depends(open_system_bus)):
    log.info(f"Deleting connection with uuid={uuid}")
    wm.delete_connection(uuid)


@app.put("/wifi/connection/activate")
def activate_existing_connection_by_uuid(uuid: UUID, _=Depends(open_system_bus)):
    log.info(f"Activating connection uuid = {uuid}")
    if not wm.activate_existing_connection(uuid, WIFI_INTERFACE):
        raise HTTPException(
            status_code=404, detail=f"No connection exists with uuid: {uuid}"
        )


@app.put("/wifi/connection/deactivate")
def deactivate_current_connection(_=Depends(open_system_bus)):
    settings = wm.get_primary_connection_settings(WIFI_INTERFACE)
    if settings and settings.uuid:
        wm.deactivate_connection(settings.uuid)


@app.get("/wifi/connection/saved")
def get_saved_connections(_=Depends(open_system_bus)) -> list[WifiConnectionSettings]:
    return wm.get_wifi_connections()


@app.delete("/wifi/connection/clear")
def delete_all_saved_connections(_=Depends(open_system_bus)):
    log.info("Deleting all saved connections")
    wm.delete_all_wifi_connections()


@app.get("/wifi/connectivity")
def get_internet_connectivity(_=Depends(open_system_bus)) -> bool:
    return wm.connectivity_check(WIFI_INTERFACE)


@app.get("/wifi/access-points")
def get_access_points(_=Depends(open_system_bus)) -> list[WifiAccessPoint]:
    return wm.get_access_points(WIFI_INTERFACE)
