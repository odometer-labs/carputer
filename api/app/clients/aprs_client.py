"""
APRS Database Client

Handles all APRS-related database operations.
"""

import logging
from typing import List, Optional, Dict, Any
from ..dependencies import get_connection
from ..models.aprs import (
    APRSPacketIn,
    APRSStation,
    APRSStationHistory,
    APRSStats
)

logger = logging.getLogger(__name__)


class APRSClient:
    """Client for APRS database operations"""
    
    def ingest_packet(self, packet: APRSPacketIn) -> Dict[str, Any]:
        """
        Ingest an APRS packet into the database.
        
        Args:
            packet: Parsed APRS packet data
            
        Returns:
            Dict with callsign and status
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT gps.upsert_aprs_station(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) AS callsign;
                    """,
                    (
                        packet.callsign,
                        packet.latitude,
                        packet.longitude,
                        packet.symbol_table,
                        packet.symbol_code,
                        packet.comment,
                        packet.altitude_m,
                        packet.speed_knots,
                        packet.course_deg,
                        packet.raw_packet
                    )
                )
                conn.commit()
                result = cursor.fetchone()
                
                return {
                    "callsign": result["callsign"] if result else packet.callsign,
                    "status": "ingested"
                }
    
    def log_raw_packet(
        self, 
        raw_packet: str, 
        parsed_ok: bool = False, 
        parse_error: Optional[str] = None
    ) -> None:
        """
        Log a raw APRS packet for debugging/replay.
        
        Args:
            raw_packet: The raw packet string
            parsed_ok: Whether parsing succeeded
            parse_error: Error message if parsing failed
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "CALL gps.log_aprs_raw_packet(%s, %s, %s);",
                    (raw_packet, parsed_ok, parse_error)
                )
                conn.commit()
    
    def get_stations_near(
        self, 
        meters: float = 50000
    ) -> List[APRSStation]:
        """
        Get APRS stations near current GPS position.
        
        Args:
            meters: Search radius in meters (default 50km)
            
        Returns:
            List of nearby APRS stations
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM gps.get_aprs_stations_near(%s);",
                    (meters,)
                )
                rows = cursor.fetchall()
                
                return [
                    APRSStation(
                        callsign=row["callsign"],
                        symbol_table=row["symbol_table"] or "/",
                        symbol_code=row["symbol_code"] or "k",
                        last_comment=row["last_comment"],
                        last_seen=row["last_seen"],
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        distance_m=row["distance_m"],
                        packet_count=row["packet_count"]
                    )
                    for row in rows
                ]
    
    def get_station_history(
        self, 
        callsign: str, 
        hours: int = 24
    ) -> List[APRSStationHistory]:
        """
        Get position history for a specific station.
        
        Args:
            callsign: Station callsign
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical positions
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM gps.get_aprs_station_history(%s, %s);",
                    (callsign, hours)
                )
                rows = cursor.fetchall()
                
                return [
                    APRSStationHistory(
                        time_stamp=row["time_stamp"],
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        altitude_m=row["altitude_m"],
                        speed_knots=row["speed_knots"],
                        course_deg=row["course_deg"],
                        comment=row["comment"]
                    )
                    for row in rows
                ]
    
    def get_stats(self) -> APRSStats:
        """
        Get APRS statistics for dashboard.
        
        Returns:
            APRS statistics
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM gps.get_aprs_stats();")
                row = cursor.fetchone()
                
                if row:
                    return APRSStats(
                        total_stations=row["total_stations"] or 0,
                        stations_24h=row["stations_24h"] or 0,
                        total_packets=row["total_packets"] or 0,
                        packets_24h=row["packets_24h"] or 0
                    )
                else:
                    return APRSStats(
                        total_stations=0,
                        stations_24h=0,
                        total_packets=0,
                        packets_24h=0
                    )
    
    def cleanup_old_data(
        self, 
        history_days: int = 30, 
        raw_days: int = 7
    ) -> None:
        """
        Cleanup old APRS data.
        
        Args:
            history_days: Delete history older than this
            raw_days: Delete raw packets older than this
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "CALL gps.cleanup_aprs_data(%s, %s);",
                    (history_days, raw_days)
                )
                conn.commit()
                logger.info(f"Cleaned up APRS data older than {history_days} days")


# Singleton instance
aprs_client = APRSClient()
