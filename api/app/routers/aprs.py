"""
APRS API Router

Endpoints for APRS data ingestion and retrieval.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..logging.handlers import logger
from ..models.aprs import (
    APRSPacketIn,
    APRSPacketOut,
    APRSStation,
    APRSStationHistory,
    APRSStats,
    APRSRawPacket
)
from ..clients.aprs_client import aprs_client
from ..aprs.parser import aprs_parser

router = APIRouter(prefix="/v1/aprs", tags=["APRS"])


@router.post("/ingest", response_model=APRSPacketOut)
async def ingest_aprs_packet(packet: APRSPacketIn):
    """
    Ingest a parsed APRS packet from the bridge.
    
    This endpoint receives pre-parsed APRS data from the aprs_bridge.py
    script that reads from Direwolf's KISS interface.
    """
    try:
        result = aprs_client.ingest_packet(packet)
        logger.info(f"Ingested APRS packet from {packet.callsign}")
        return APRSPacketOut(**result)
    except Exception as e:
        logger.error(f"Failed to ingest APRS packet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-raw", response_model=APRSPacketOut)
async def ingest_raw_aprs_packet(raw: APRSRawPacket):
    """
    Ingest a raw APRS packet string.
    
    Parses the packet using the built-in parser before storing.
    Useful for direct packet injection without the bridge.
    """
    try:
        # Log the raw packet
        position = aprs_parser.parse(raw.raw_packet)
        
        if position is None:
            # Log failed parse
            aprs_client.log_raw_packet(
                raw.raw_packet, 
                parsed_ok=False, 
                parse_error="Failed to parse position"
            )
            raise HTTPException(
                status_code=400, 
                detail="Could not parse APRS packet (not a position packet?)"
            )
        
        # Convert to API model
        packet = APRSPacketIn(
            callsign=position.callsign,
            latitude=position.latitude,
            longitude=position.longitude,
            symbol_table=position.symbol_table,
            symbol_code=position.symbol_code,
            comment=position.comment,
            altitude_m=position.altitude_m,
            speed_knots=position.speed_knots,
            course_deg=position.course_deg,
            raw_packet=position.raw_packet
        )
        
        # Ingest
        result = aprs_client.ingest_packet(packet)
        
        # Log successful parse
        aprs_client.log_raw_packet(raw.raw_packet, parsed_ok=True)
        
        logger.info(f"Parsed and ingested APRS packet from {packet.callsign}")
        return APRSPacketOut(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process raw APRS packet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stations", response_model=List[APRSStation])
async def get_nearby_stations(
    radius_m: float = Query(default=50000, ge=100, le=500000, description="Search radius in meters")
):
    """
    Get APRS stations near the current GPS position.
    
    Returns stations within the specified radius that have been
    seen in the last 24 hours, ordered by distance.
    """
    try:
        stations = aprs_client.get_stations_near(radius_m)
        return stations
    except Exception as e:
        logger.error(f"Failed to get nearby stations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stations/{callsign}", response_model=APRSStation)
async def get_station(callsign: str):
    """
    Get information about a specific APRS station.
    """
    try:
        stations = aprs_client.get_stations_near(500000)  # 500km max
        for station in stations:
            if station.callsign.upper() == callsign.upper():
                return station
        raise HTTPException(status_code=404, detail=f"Station {callsign} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get station {callsign}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stations/{callsign}/history", response_model=List[APRSStationHistory])
async def get_station_history(
    callsign: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve")
):
    """
    Get position history for a specific APRS station.
    
    Returns up to 7 days of historical positions.
    """
    try:
        history = aprs_client.get_station_history(callsign, hours)
        if not history:
            raise HTTPException(status_code=404, detail=f"No history found for {callsign}")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history for {callsign}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=APRSStats)
async def get_aprs_stats():
    """
    Get APRS statistics for the dashboard.
    
    Returns total station count, 24h activity, and packet counts.
    """
    try:
        return aprs_client.get_stats()
    except Exception as e:
        logger.error(f"Failed to get APRS stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_aprs_data(
    history_days: int = Query(default=30, ge=1, le=365),
    raw_days: int = Query(default=7, ge=1, le=30)
):
    """
    Trigger cleanup of old APRS data.
    
    This is typically called by a cron job, but can be triggered manually.
    """
    try:
        aprs_client.cleanup_old_data(history_days, raw_days)
        return {"status": "cleanup completed", "history_days": history_days, "raw_days": raw_days}
    except Exception as e:
        logger.error(f"Failed to cleanup APRS data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
