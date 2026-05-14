"""
APRS Pydantic Models for API
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APRSPacketIn(BaseModel):
    """Incoming APRS packet from bridge"""
    callsign: str = Field(..., min_length=1, max_length=20)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    symbol_table: str = Field(default="/", max_length=1)
    symbol_code: str = Field(default="k", max_length=1)
    comment: Optional[str] = Field(default=None, max_length=500)
    altitude_m: Optional[float] = Field(default=None)
    speed_knots: Optional[float] = Field(default=None, ge=0)
    course_deg: Optional[float] = Field(default=None, ge=0, le=360)
    raw_packet: Optional[str] = Field(default=None, max_length=2000)
    

class APRSPacketOut(BaseModel):
    """APRS packet response"""
    callsign: str
    status: str = "ingested"


class APRSStation(BaseModel):
    """APRS station information"""
    callsign: str
    symbol_table: str
    symbol_code: str
    last_comment: Optional[str]
    last_seen: datetime
    latitude: float
    longitude: float
    distance_m: Optional[float] = None
    packet_count: int


class APRSStationHistory(BaseModel):
    """APRS station position history entry"""
    time_stamp: datetime
    latitude: float
    longitude: float
    altitude_m: Optional[float]
    speed_knots: Optional[float]
    course_deg: Optional[float]
    comment: Optional[str]


class APRSStats(BaseModel):
    """APRS statistics for dashboard"""
    total_stations: int
    stations_24h: int
    total_packets: int
    packets_24h: int


class APRSRawPacket(BaseModel):
    """Raw APRS packet for debugging"""
    raw_packet: str = Field(..., max_length=2000)
