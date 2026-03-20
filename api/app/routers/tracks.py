from datetime import datetime, timezone
from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from psycopg import Cursor, Connection
from ..logging.handlers import logger
from ..dependencies import get_connection
from app.model.models import (
    Track,
    TrackPoint
)

router = APIRouter(prefix="/v1", tags=["Tracks"])

@router.get("/tracks")
async def list_track():
    """
    Lists all the tracks.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT * from gps.view_all_tracks();""")
            conn.commit()
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

@router.get("/tracks/{track_id}")
async def get_track(track_id: int):
    """
    Retrieves a track based on id.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT * FROM gps.retrieve_track(%s);""", (track_id,))
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

@router.put("/tracks/{track_id}")
async def update_track(track_id: int, track: Track):
    """
    Updates/modifies an existing track with the provided Track object
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""CALL gps.update_track(%s, %s, %s)""", (track_id, track.start_time, track.end_time))
            conn.commit()
            return {"result": "success"}
    finally:
        conn.close()

@router.delete("/tracks/{track_id}")
async def delete_track(track_id: int):
    """
    Deletes a track with the provided track id.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""CALL gps.delete_track(%s)""", (track_id,))
            conn.commit()
            return {"result": "success"}
    finally:
        conn.close()

@router.post("/tracks-start")
async def start_track():
    """
    Starts track for the trip
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT gps.create_track();""")
            conn.commit()
            result = cursor.fetchone()
            return result
    finally:
        conn.close()

@router.get("/tracks-end")
async def end_track():
    """
    Ends the track for the trip
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""CALL gps.end_track();""")
            conn.commit()
            return {"result": "success"}
    finally:
        conn.close()

@router.post("/tracks/point/{track_id}")
async def add_track_point(track_id: int, track_point: TrackPoint):
    """
    Adds a track point for the current track
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""CALL gps.add_track_point(%s, %s, %s, %s, %s, %s)""", 
                           (track_id, 
                            datetime.now(timezone.utc),
                            track_point.latitude, 
                            track_point.longitude, 
                            track_point.speed, 
                            track_point.heading))
            conn.commit()
            return {"result": "success"}
    finally:
        conn.close()

@router.get("/tracks-latest-point")
async def get_latest_track_point():
    """
    Gets the latest track point for the current track
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT * FROM gps.get_latest_track_point()""")
            conn.commit()
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

@router.get("/tracks-check-new-road")
async def check_new_road():
    """
    Checks if the latest point is a new road
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT gps.is_new_road();")
            conn.commit()
            result = cursor.fetchone()
            is_new_road = result[0]
            return {"is_new_road": is_new_road}
    finally:
        conn.close()