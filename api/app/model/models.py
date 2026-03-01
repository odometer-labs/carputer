from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

class Track(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime

class TrackPoint(BaseModel):
    """
    The model representing the GPSD data
    """
    track_id: int
    timestamp: datetime
    speed: float # speed over ground, m/s (double)
    heading: str

class TrackLine(BaseModel):
    track_id: int