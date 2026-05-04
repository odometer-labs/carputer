from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

class Track(BaseModel):
    start_time: datetime
    end_time: datetime
    track_name: str
