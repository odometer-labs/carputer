from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

class TrackPoint(BaseModel):
    """
    The model representing the GPSD data
    """
    latitude: float
    longitude: float
    speed: float # speed over ground, m/s (double)
    heading: float # degrees