from datetime import datetime
from fastapi import APIRouter
from src.model.models import (
    Track,
    TrackLine,
    TrackPoint
)

router = APIRouter(prefix="/v1")

@router.get("/")
async def root():
    return {"Hello": "World"}

@router.get("/track/{track_id}")
async def get_track(track_id: str) -> Track:
    """
    Retrieves a track based on id.

    Parameters:
        track_id (str): Track id.

    Returns:
        Track: A serializable Track object with the same track id.
    """
    track = Track(id=int(track_id), start_time=datetime.now(), end_time=datetime.now())
    return track

@router.post("/track")
async def add_track(track: Track) -> Track:
    """
    Adds a track with the provided Track object.

    Parameters:
        track (Track): Track object.

    Returns:
        Track: A serializable Track object we just added.
    """
    return track

@router.put("/track/{track_id}")
async def update_track(track_id: str, track: Track) -> Track:
    """
    Updates/modifies an existing track with the provided Track object

    Parameters:
        track_id (str): Track id.
        track (Track): Track object.

    Returns:
        Track: A serializable Track object we just updated.
    """
    return track

@router.delete("/track/{track_id}")
async def delete_track(track_id: str):
    """
    Deletes a track with the provided track id.

    Parameters:
        track_id (str): Track id.

    Returns:
        dict: A json body indicating success or failure.
    """
    return {"result": "success"}