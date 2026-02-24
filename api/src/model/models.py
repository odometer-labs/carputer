from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

class Track(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime

class TrackPoint(BaseModel):
    track_id: int
    timestamp: datetime
    # geom GEOGRAPHY
    speed: int
    heading: str

class TrackLine(BaseModel):
    track_id: int
    # geom GEOGRAPHY