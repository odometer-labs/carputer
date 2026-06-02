#!/usr/bin/env python3
"""
APRS Bridge - Connects Direwolf to Carputer Backend

Reads APRS packets from Direwolf's KISS TCP interface,
parses position data, and sends to the FastAPI backend.

Usage:
    python -m aprs_bridge.bridge
    
    # Or with custom settings:
    KISS_HOST=192.168.1.100 BACKEND_URL=http://api:8000 python -m aprs_bridge.bridge
"""

import os
import sys
import time
import json
import logging
import socket
import signal
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import requests

# Configure logging
LOG_FILE = os.environ.get("APRS_LOG_FILE", "/var/log/carputer/aprs-bridge.log")
LOG_LEVEL = os.environ.get("APRS_LOG_LEVEL", "INFO")

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Configuration from environment
KISS_HOST = os.environ.get("KISS_HOST", "localhost")
KISS_PORT = int(os.environ.get("KISS_PORT", "8003"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
RECONNECT_DELAY = float(os.environ.get("RECONNECT_DELAY", "5.0"))


# KISS protocol constants
FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD


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
    raw_packet: str = ""


class APRSParser:
    """APRS packet parser - simplified version for bridge"""
    
    BASE91_CHARS = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|"
    
    def parse(self, raw_packet: str) -> Optional[APRSPosition]:
        """Parse an APRS packet string"""
        try:
            raw_packet = raw_packet.strip()
            if not raw_packet or '>' not in raw_packet or ':' not in raw_packet:
                return None
            
            source, rest = raw_packet.split('>', 1)
            callsign = source.strip()
            path_dest, info = rest.split(':', 1)
            
            if not info:
                return None
            
            data_type = info[0]
            
            if data_type in ('!', '=', '/', '@'):
                return self._parse_position(callsign, info, raw_packet)
            elif data_type in ('`', "'"):
                return self._parse_mic_e(callsign, path_dest, info, raw_packet)
            
            return None
            
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def _parse_position(self, callsign: str, info: str, raw: str) -> Optional[APRSPosition]:
        """Parse standard position format"""
        try:
            data_type = info[0]
            payload = info[1:]
            
            # Skip timestamp if present
            if data_type in ('/', '@') and len(payload) >= 7:
                payload = payload[7:]
            
            if len(payload) < 19:
                return None
            
            # Check for compressed format
            if payload[0] in self.BASE91_CHARS and payload[0] not in '0123456789':
                return self._parse_compressed(callsign, payload, raw)
            
            # Uncompressed format
            lat_str = payload[0:8]
            symbol_table = payload[8]
            lon_str = payload[9:18]
            symbol_code = payload[18]
            comment = payload[19:].strip() if len(payload) > 19 else None
            
            # Parse latitude
            lat_deg = int(lat_str[0:2])
            lat_min = float(lat_str[2:7])
            latitude = lat_deg + (lat_min / 60.0)
            if lat_str[7].upper() == 'S':
                latitude = -latitude
            
            # Parse longitude
            lon_deg = int(lon_str[0:3])
            lon_min = float(lon_str[3:8])
            longitude = lon_deg + (lon_min / 60.0)
            if lon_str[8].upper() == 'W':
                longitude = -longitude
            
            # Extract altitude if present
            altitude_m = None
            if comment and '/A=' in comment:
                import re
                alt_match = re.search(r'/A=(\d{6})', comment)
                if alt_match:
                    altitude_m = int(alt_match.group(1)) * 0.3048
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                altitude_m=altitude_m,
                raw_packet=raw
            )
            
        except Exception as e:
            logger.debug(f"Position parse error: {e}")
            return None
    
    def _parse_compressed(self, callsign: str, payload: str, raw: str) -> Optional[APRSPosition]:
        """Parse compressed position format"""
        try:
            if len(payload) < 13:
                return None
            
            symbol_table = payload[0]
            lat_chars = payload[1:5]
            lon_chars = payload[5:9]
            symbol_code = payload[9]
            comment = payload[13:].strip() if len(payload) > 13 else None
            
            # Decode latitude
            lat_val = 0
            for c in lat_chars:
                lat_val = lat_val * 91 + self.BASE91_CHARS.index(c)
            latitude = 90.0 - (lat_val / 380926.0)
            
            # Decode longitude
            lon_val = 0
            for c in lon_chars:
                lon_val = lon_val * 91 + self.BASE91_CHARS.index(c)
            longitude = -180.0 + (lon_val / 190463.0)
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                raw_packet=raw
            )
            
        except Exception as e:
            logger.debug(f"Compressed parse error: {e}")
            return None
    
    def _parse_mic_e(self, callsign: str, path: str, info: str, raw: str) -> Optional[APRSPosition]:
        """Parse Mic-E encoded position"""
        try:
            # Extract destination from path
            dest = path.split(',')[0] if ',' in path else path
            dest = dest[:6].upper()
            
            if len(dest) < 6 or len(info) < 9:
                return None
            
            # Decode latitude from destination
            lat_digits = []
            lat_ns = 'N'
            lon_offset = 0
            lon_ew = 'W'
            
            for i, c in enumerate(dest):
                if c.isdigit():
                    lat_digits.append(int(c))
                elif c in 'KLMNOPQRSTUVWXYZ':
                    lat_digits.append(ord(c) - ord('K'))
                else:
                    lat_digits.append(0)
                
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
            
            # Decode longitude from info field
            d28 = ord(info[1]) - 28
            m28 = ord(info[2]) - 28
            h28 = ord(info[3]) - 28
            symbol_code = info[7]
            symbol_table = info[8]
            comment = info[9:].strip() if len(info) > 9 else None
            
            lon_deg = d28 + lon_offset
            if 180 <= lon_deg <= 189:
                lon_deg -= 80
            elif 190 <= lon_deg <= 199:
                lon_deg -= 190
            
            if m28 >= 60:
                m28 -= 60
            lon_min = m28 + h28 / 100.0
            
            longitude = lon_deg + lon_min / 60.0
            if lon_ew == 'W':
                longitude = -longitude
            
            return APRSPosition(
                callsign=callsign,
                latitude=latitude,
                longitude=longitude,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
                comment=comment,
                raw_packet=raw
            )
            
        except Exception as e:
            logger.debug(f"Mic-E parse error: {e}")
            return None


class APRSBridge:
    """Main APRS bridge class"""
    
    def __init__(self):
        self.parser = APRSParser()
        self.running = False
        self.socket: Optional[socket.socket] = None
        self.buffer = bytearray()
        self.packets_received = 0
        self.packets_parsed = 0
        self.packets_sent = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def connect_kiss(self) -> bool:
        """Connect to Direwolf KISS interface"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((KISS_HOST, KISS_PORT))
            self.socket.settimeout(1.0)
            logger.info(f"Connected to Direwolf at {KISS_HOST}:{KISS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Direwolf: {e}")
            return False
    
    def disconnect_kiss(self):
        """Disconnect from Direwolf"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def send_to_backend(self, position: APRSPosition) -> bool:
        """Send parsed position to backend API"""
        try:
            payload = {
                "callsign": position.callsign,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "symbol_table": position.symbol_table,
                "symbol_code": position.symbol_code,
                "comment": position.comment,
                "altitude_m": position.altitude_m,
                "speed_knots": position.speed_knots,
                "course_deg": position.course_deg,
                "raw_packet": position.raw_packet
            }
            
            response = requests.post(
                f"{BACKEND_URL}/v1/aprs/ingest",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                self.packets_sent += 1
                logger.info(f"Sent packet from {position.callsign} ({position.latitude:.4f}, {position.longitude:.4f})")
                return True
            else:
                logger.warning(f"Backend returned {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send to backend: {e}")
            return False
    
    def decode_kiss_frame(self, frame: bytes) -> Optional[str]:
        """Decode a KISS frame to an APRS packet string"""
        if not frame or frame[0] != 0x00:  # Not a data frame
            return None
        
        data = frame[1:]
        
        # Unescape special bytes
        unescaped = bytearray()
        i = 0
        while i < len(data):
            if data[i] == FESC:
                if i + 1 < len(data):
                    if data[i + 1] == TFEND:
                        unescaped.append(FEND)
                    elif data[i + 1] == TFESC:
                        unescaped.append(FESC)
                    else:
                        unescaped.append(data[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                unescaped.append(data[i])
                i += 1
        
        # Decode AX.25 frame
        return self.decode_ax25(bytes(unescaped))
    
    def decode_ax25(self, frame: bytes) -> Optional[str]:
        """Decode AX.25 frame to APRS packet string"""
        try:
            if len(frame) < 16:
                return None
            
            # Destination (7 bytes)
            dest = self.decode_ax25_addr(frame[0:7])
            # Source (7 bytes)
            source = self.decode_ax25_addr(frame[7:14])
            
            # Digipeater addresses
            path = []
            idx = 14
            while idx < len(frame) - 2 and (frame[idx - 1] & 0x01) == 0:
                if idx + 7 > len(frame):
                    break
                digi = self.decode_ax25_addr(frame[idx:idx + 7])
                if digi:
                    if frame[idx + 6] & 0x80:
                        digi += '*'
                    path.append(digi)
                idx += 7
            
            # Skip control + PID
            ctrl = frame[idx]
            idx += 1
            if (ctrl & 0x01) == 0 or (ctrl & 0xEF) == 0x03:
                idx += 1
            
            # Info field
            info = frame[idx:].decode('latin-1', errors='replace')
            
            path_str = dest + (',' + ','.join(path) if path else '')
            return f"{source}>{path_str}:{info}"
            
        except Exception as e:
            logger.debug(f"AX.25 decode error: {e}")
            return None
    
    def decode_ax25_addr(self, addr: bytes) -> Optional[str]:
        """Decode AX.25 address field"""
        try:
            callsign = ""
            for i in range(6):
                c = (addr[i] >> 1) & 0x7F
                if c != 0x20:
                    callsign += chr(c)
            ssid = (addr[6] >> 1) & 0x0F
            return f"{callsign}-{ssid}" if ssid > 0 else callsign
        except:
            return None
    
    def process_data(self, data: bytes):
        """Process received data and extract KISS frames"""
        self.buffer.extend(data)
        
        while True:
            start = self.buffer.find(bytes([FEND]))
            if start == -1:
                self.buffer.clear()
                break
            
            if start > 0:
                self.buffer = self.buffer[start:]
            
            end = self.buffer.find(bytes([FEND]), 1)
            if end == -1:
                break
            
            frame = bytes(self.buffer[1:end])
            self.buffer = self.buffer[end + 1:]
            
            packet_str = self.decode_kiss_frame(frame)
            if packet_str:
                self.packets_received += 1
                logger.debug(f"Received: {packet_str[:80]}")
                
                position = self.parser.parse(packet_str)
                if position:
                    self.packets_parsed += 1
                    self.send_to_backend(position)
    
    def run(self):
        """Main bridge loop"""
        logger.info("=" * 60)
        logger.info("APRS Bridge Starting")
        logger.info(f"  KISS: {KISS_HOST}:{KISS_PORT}")
        logger.info(f"  Backend: {BACKEND_URL}")
        logger.info("=" * 60)
        
        self.running = True
        
        while self.running:
            if not self.socket:
                if not self.connect_kiss():
                    time.sleep(RECONNECT_DELAY)
                    continue
            
            try:
                data = self.socket.recv(4096)
                if not data:
                    logger.warning("Connection closed by Direwolf")
                    self.disconnect_kiss()
                    continue
                
                self.process_data(data)
                
            except socket.timeout:
                continue
            except socket.error as e:
                logger.error(f"Socket error: {e}")
                self.disconnect_kiss()
                time.sleep(RECONNECT_DELAY)
        
        self.disconnect_kiss()
        logger.info("=" * 60)
        logger.info("APRS Bridge Stopped")
        logger.info(f"  Packets received: {self.packets_received}")
        logger.info(f"  Packets parsed:   {self.packets_parsed}")
        logger.info(f"  Packets sent:     {self.packets_sent}")
        logger.info("=" * 60)


def main():
    bridge = APRSBridge()
    bridge.run()


if __name__ == "__main__":
    main()
