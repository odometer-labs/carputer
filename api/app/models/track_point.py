from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

<<<<<<< HEAD:api/app/models/track_point.py
=======
class Track(BaseModel):
    start_time: datetime
    end_time: datetime

>>>>>>> 9b0f077 (docker stuff):api/app/model/models.py
class TrackPoint(BaseModel):
    """
    The model representing the GPSD data
    """
    latitude: float
    longitude: float
    speed: float # speed over ground, m/s (double)
    heading: float # degrees