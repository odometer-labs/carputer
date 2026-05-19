"""
APRS Packet Parser

Parses APRS packets from Direwolf into structured data.
Supports position reports, compressed positions, and Mic-E encoding.

References:
- APRS Protocol Reference: http://www.aprs.org/doc/APRS101.PDF
- aprslib implementation patterns
"""

import re
import math
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class APRSPosition:
    """Parsed APRS position data"""
    callsign: str
    latitude: float
    longitude: float
    symbol_table: str = "/"
    symbol_code: str = "k"
    comment: Optional[str] = None
    altitude_m: Optional[float] = None
    speed_knots: Optional[float] = None
    course_deg: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_packet: str = ""
    path: Optional[str] = None
    

class APRSParser:
    """
    APRS packet parser supporting common position formats.
    
    Supported formats:
    - Uncompressed position (!/@)
    - Compressed position
    - Mic-E encoded position
    - Position with timestamp
    """
    
    # APRS data type identifiers
    POSITION_TYPES = {
        '!': 'position_no_ts',      # Position without timestamp (no APRS messaging)
        '=': 'position_no_ts_msg',  # Position without timestamp (with APRS messaging)
        '/': 'position_with_ts',    # Position with timestamp (no APRS messaging)
        '@': 'position_with_ts_msg', # Position with timestamp (with APRS messaging)
    }
    
    # Mic-E destination address encoding
    MIC_E_DEST_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Compressed position base91 characters
    BASE91_CHARS = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|"
    
    def __init__(self):
        self._mic_e_speed_table = self._build_mic_e_speed_table()
    
    def _build_mic_e_speed_table(self) -> Dict[int, tuple]:
        """Build Mic-E speed/course lookup table"""
        table = {}
        for i in range(0, 800):
            sp = i // 10
            dc = (i % 10) * 100
            table[i] = (sp, dc)
        return table

    def parse(self, raw_packet: str) -> Optional[APRSPosition]:
        """
        Parse an APRS packet string.
        
        Args:
            raw_packet: Raw APRS packet string (e.g., "W1ABC>APRS,WIDE1-1:!4903.50N/07201.75W-PHG2360")
            
        Returns:
            APRSPosition if successfully parsed, None otherwise
        """
        try:
            raw_packet = raw_packet.strip()
            if not raw_packet:
                return None
            
            # Split header from information field
            if '>' not in raw_packet:
                logger.debug(f"No '>' in packet: {raw_packet[:50]}")
                return None
                
            source, rest = raw_packet.split('>', 1)
            callsign = source.strip()
            
            if ':' not in rest:
                logger.debug(f"No ':' in packet: {raw_packet[:50]}")
                return None
                
            path_dest, info = rest.split(':', 1)
            path = path_dest.strip()
            
            if not info:
                return None
            
            # Check for position packet types
            data_type = info[0]
            
            if data_type in ('!', '=', '/', '@'):
                return self._parse_position(callsign, path, info, raw_packet)
            elif data_type in ('`', "'"):
                # Mic-E format (destination contains position)
                return self._parse_mic_e(callsign, path, info, raw_packet)
            else:
                # Not a position packet (status, message, telemetry, etc.)
                logger.debug(f"Non-position packet type: {data_type}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to parse APRS packet: {e} - {raw_packet[:80]}")
            return None

    def _parse_position(self, callsign: str, path: str, info: str, raw: str) -> Optional[APRSPosition]:
        """Parse standard APRS position format"""
        try:
            data_type = info[0]
            payload = info[1:]
            
            # Check if timestamp present
            if data_type in ('/', '@'):
                # Timestamp is 7 characters (e.g., "092345z" or "092345/")
                if len(payload) < 7:
                    return None
                # Skip timestamp for now, extract position
                payload = payload[7:]
            
            if len(payload) < 19:
                return None
            
            # Check for compressed vs uncompressed
            if payload[0] in self.BASE91_CHARS and payload[0] not in '0123456789':
                return self._parse_compressed_position(callsign, path, payload, raw)
            else:
                return self._parse_uncompressed_position(callsign, path, payload, raw)
                
        except Exception as e:
            logger.debug(f"Position parse error: {e}")
            return None

    def _parse_uncompressed_position(self, callsign: str, path: str, payload: str, raw: str) -> Optional[APRSPosition]:
        """
        Parse uncompressed APRS position.
        Format: DDMM.MMN/DDDMM.MMW$ (19 chars minimum)
        """
        try:
            # Latitude: DDMM.MMN (8 chars)
            lat_str = payload[0:8]
            # Symbol table (1 char)
            symbol_table = payload[8]
            # Longitude: DDDMM.MMW (9 chars)
            lon_str = payload[9:18]
            # Symbol code (1 char)
            symbol_code = payload[18]
            # Comment (rest)
            comment = payload[19:].strip() if len(payload) > 19 else None
            
            # Parse latitude
            lat_deg = int(lat_str[0:2])
            lat_min = float(lat_str[2:7])
            lat_dir = lat_str[7].upper()
            
            latitude = lat_deg + (lat_min / 60.0)
            if lat_dir == 'S':
                latitude = -latitude
            
            # Parse longitude
            lon_deg = int(lon_str[0:3])
            lon_min = float(lon_str[3:8])
            lon_dir = lon_str[8].upper()
            
            longitude = lon_deg + (lon_min / 60.0)
            if lon_dir == 'W':
                longitude = -longitude
            
            # Extract altitude from comment if present (/A=NNNNNN)
            altitude_m = None
            if comment and '/A=' in comment:
                alt_match = re.search(r'/A=(\d{6})', comment)
                if alt_match:
                    altitude_ft = int(alt_match.group(1))
                    altitude_m = altitude_ft * 0.3048
            
            # Extract course/speed from comment if present
            speed_knots = None
            course_deg = None
            if comment:
                cs_match = re.match(r'^(\d{3})/(\d{3})', comment)
                if cs_match:
                    course_deg = float(cs_match.group(1))
                    speed_knots = float(cs_match.group(2))
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                altitude_m=altitude_m,
                speed_knots=speed_knots,
                course_deg=course_deg,
                raw_packet=raw,
                path=path
            )
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Uncompressed position parse error: {e}")
            return None

    def _parse_compressed_position(self, callsign: str, path: str, payload: str, raw: str) -> Optional[APRSPosition]:
        """
        Parse compressed APRS position.
        Format: /YYYYXXXX$csT (13 chars)
        """
        try:
            if len(payload) < 13:
                return None
            
            symbol_table = payload[0]
            # YYYY = latitude (4 base91 chars)
            lat_chars = payload[1:5]
            # XXXX = longitude (4 base91 chars)
            lon_chars = payload[5:9]
            symbol_code = payload[9]
            # cs = course/speed or altitude (2 chars)
            cs_chars = payload[10:12]
            # T = compression type (1 char)
            comp_type = payload[12] if len(payload) > 12 else ' '
            
            comment = payload[13:].strip() if len(payload) > 13 else None
            
            # Decode latitude (90 - lat/380926) 
            lat_val = 0
            for i, c in enumerate(lat_chars):
                lat_val = lat_val * 91 + self.BASE91_CHARS.index(c)
            latitude = 90.0 - (lat_val / 380926.0)
            
            # Decode longitude (-180 + lon/190463)
            lon_val = 0
            for i, c in enumerate(lon_chars):
                lon_val = lon_val * 91 + self.BASE91_CHARS.index(c)
            longitude = -180.0 + (lon_val / 190463.0)
            
            # Decode course/speed or altitude
            speed_knots = None
            course_deg = None
            altitude_m = None
            
            if cs_chars != '  ':
                c_idx = self.BASE91_CHARS.index(cs_chars[0]) if cs_chars[0] in self.BASE91_CHARS else 0
                s_idx = self.BASE91_CHARS.index(cs_chars[1]) if cs_chars[1] in self.BASE91_CHARS else 0
                
                # Check compression type for altitude vs course/speed
                t_idx = self.BASE91_CHARS.index(comp_type) if comp_type in self.BASE91_CHARS else 0
                
                if t_idx & 0x18 == 0x10:  # GPS fix, altitude
                    alt_val = (c_idx * 91 + s_idx)
                    altitude_m = (1.002 ** alt_val) * 0.3048  # Convert feet to meters
                else:  # Course/speed
                    course_deg = c_idx * 4.0
                    speed_knots = (1.08 ** s_idx) - 1
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                altitude_m=altitude_m,
                speed_knots=speed_knots,
                course_deg=course_deg,
                raw_packet=raw,
                path=path
            )
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Compressed position parse error: {e}")
            return None

    def _parse_mic_e(self, callsign: str, path: str, info: str, raw: str) -> Optional[APRSPosition]:
        """
        Parse Mic-E encoded position.
        Position is encoded in destination address + info field.
        """
        try:
            # Extract destination from path (first element before ',')
            if ',' in path:
                dest = path.split(',')[0]
            else:
                dest = path
            
            # Destination must be 6 characters for Mic-E
            if len(dest) < 6:
                return None
            
            dest = dest[:6].upper()
            
            # Decode latitude from destination
            lat_digits = []
            lat_ns = 'N'
            lon_offset = 0
            lon_ew = 'W'
            
            for i, c in enumerate(dest):
                if c.isdigit():
                    lat_digits.append(int(c))
                elif c in 'ABCDEFGHIJ':
                    lat_digits.append(ord(c) - ord('A'))
                elif c in 'KLMNOPQRSTUVWXYZ':
                    lat_digits.append(ord(c) - ord('K'))
                    if i < 3:
                        # Custom ambiguity
                        pass
                elif c == ' ':
                    lat_digits.append(0)
                else:
                    lat_digits.append(0)
                
                # Check for N/S, lon offset, E/W bits
                if i == 3 and c in 'PQRSTUVWXYZ':
                    lat_ns = 'N'
                elif i == 3:
                    lat_ns = 'S'
                
                if i == 4 and c in 'LMNOPQRSTUVWXYZ':
                    lon_offset = 100
                
                if i == 5 and c in 'PQRSTUVWXYZ':
                    lon_ew = 'E'
            
            if len(lat_digits) < 6:
                return None
            
            lat_deg = lat_digits[0] * 10 + lat_digits[1]
            lat_min = lat_digits[2] * 10 + lat_digits[3] + lat_digits[4] / 10.0 + lat_digits[5] / 100.0
            latitude = lat_deg + lat_min / 60.0
            if lat_ns == 'S':
                latitude = -latitude
            
            # Decode longitude and speed/course from info field
            if len(info) < 9:
                return None
            
            data_type = info[0]  # ` or '
            d28 = ord(info[1]) - 28
            m28 = ord(info[2]) - 28
            h28 = ord(info[3]) - 28
            sp28 = ord(info[4]) - 28
            dc28 = ord(info[5]) - 28
            se28 = ord(info[6]) - 28
            symbol_code = info[7]
            symbol_table = info[8]
            
            comment = info[9:].strip() if len(info) > 9 else None
            
            # Longitude degrees
            lon_deg = d28 + lon_offset
            if lon_deg >= 180 and lon_deg <= 189:
                lon_deg -= 80
            elif lon_deg >= 190 and lon_deg <= 199:
                lon_deg -= 190
            
            # Longitude minutes
            if m28 >= 60:
                m28 -= 60
            lon_min = m28 + h28 / 100.0
            
            longitude = lon_deg + lon_min / 60.0
            if lon_ew == 'W':
                longitude = -longitude
            
            # Speed and course
            speed_knots = (sp28 * 10) + (dc28 // 10)
            course_deg = ((dc28 % 10) * 100) + se28
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                speed_knots=float(speed_knots),
                course_deg=float(course_deg) if course_deg > 0 else None,
                raw_packet=raw,
                path=path
            )
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Mic-E parse error: {e}")
            return None


# Singleton instance
aprs_parser = APRSParser()
