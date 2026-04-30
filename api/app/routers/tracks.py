from datetime import datetime, timezone
from fastapi import APIRouter
from psycopg import Connection
from ..logging.handlers import logger
from ..dependencies import get_connection
from app.models.track import Track
from app.models.track_point import TrackPoint
from app.clients.track_client import track_client
from typing import Dict, Any, Optional
import json
import Response
import status

router = APIRouter(prefix="/v1", tags=["Tracks"])


@router.get("/tracks")
async def list_track():
    """
    Lists all the tracks.
    """

    return track_client.list_track()


@router.get("/tracks/{z}/{x}/{y}/{mode}/{track_id}/{within_meters}.mvt")
async def list_track_mvt(
    z: int,
    x: int,
    y: int,
    mode: str = "All",
    track_id: int = 0,
    within_meters: int = 500,
):
    """
    Returns mapbox vector tiles for a specific tile containing track(s) according
    to specified mode.
    """
    tile_data = track_client.list_tracks_mvt(z, x, y, mode, track_id, within_meters)
    if not tile_data or len(tile_data) == 0:

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return Response(
        content=tile_data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/tracks/{track_id}")
async def get_track(track_id: int):
    """
    Retrieves a track based on id.
    """

    return track_client.get_track(track_id)


@router.put("/tracks/{track_id}")
async def update_track(track_id: int, track: Track):
    """
    Updates/modifies an existing track with the provided Track object
    """

    return track_client.update_track(track_id, track)


@router.delete("/tracks/{track_id}")
async def delete_track(track_id: int):
    """
    Deletes a track with the provided track id.
    """

    return track_client.delete_track(track_id)


@router.post("/tracks-start")
async def start_track(name: Optional[str] = None):
    """
    Starts track for the trip. If no name is provided, it defaults to NULL.
    """

    return track_client.start_track(name)


@router.get("/tracks-end")
async def end_track():
    """
    Ends the track for the trip
    """

    return track_client.end_track()


@router.post("/tracks/point/import/{track_id}")
async def import_track_point(track_id: int, track_point: TrackPoint):
    """
    Imports a track point for the specified track id
    """

    return track_client.import_track_point(track_id, track_point)


@router.post("/tracks/point")
async def add_track_point(track_point: TrackPoint):
    """
    Adds a track point for the current track
    """

    return track_client.add_track_point(track_point)


@router.get("/tracks-latest-point")
async def get_latest_track_point():
    """
    Gets the latest track point for the current track
    """

    return track_client.get_latest_track_point()


@router.get("/tracks-check-new-road")
async def check_new_road():
    """
    Checks if the latest point is a new road
    """

    return track_client.check_new_road()


@router.post("/tracks/import")
async def import_track(geojson_data: Dict[str, Any]):
    """
    Imports a track from GeoJSON data.
    """
    geojson_str = json.dumps(geojson_data)
    return track_client.import_track(geojson_str)
