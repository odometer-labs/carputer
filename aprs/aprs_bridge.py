#!/usr/bin/env python3
"""
APRS Bridge - Connects Direwolf to FastAPI Backend
Reads APRS packets from Direwolf KISS interface (TCP port 8003)
Sends to backend API for storage in PostgreSQL
"""

import socket
import json
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='/var/log/carputer/aprs-bridge.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
KISS_HOST = 'localhost'
KISS_PORT = 8003
BACKEND_URL = 'http://localhost:8000/v1/aprs/ingest'

# KISS protocol constants
FEND = 0xC0  # Frame End marker
FESC = 0xDB  # Frame Escape marker

def parse_kiss_frame(frame):
    """
    Parse KISS frame from Direwolf
    KISS frame format: <FEND><CMD><DATA><FEND>
    """
    try:
        # Strip FEND bytes
        if frame[0] == FEND:
            frame = frame[1:]
        if frame[-1] == FEND:
            frame = frame[:-1]
        
        # Remove KISS command byte (first byte after FEND)
        if len(frame) > 0 and frame[0] == 0x00:
            frame = frame[1:]
        
        # Decode AX.25 packet to string
        packet_str = frame.decode('latin-1', errors='ignore')
        
        return packet_str
        
    except Exception as e:
        logging.error(f"Failed to parse KISS frame: {e}")
        return None

def parse_aprs_packet(packet_str):
    """
    Parse APRS packet string
    Example: "N0CALL>APRS,WIDE1-1:!4903.50N/07201.75W-Test"
    Returns dict with callsign, raw packet, timestamp, and data
    """
    try:
        if '>' not in packet_str or ':' not in packet_str:
            return None
        
        # Extract callsign (everything before '>')
        callsign = packet_str.split('>')[0].strip()
        
        # Extract data (everything after ':')
        data = packet_str.split(':', 1)[1] if ':' in packet_str else ''
        
        return {
            'callsign': callsign,
            'raw_packet': packet_str,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
    except Exception as e:
        logging.error(f"Failed to parse APRS packet: {e}")
        return None

def send_to_backend(packet_data):
    """Send parsed APRS packet to backend API"""
    try:
        response = requests.post(
            BACKEND_URL,
            json=packet_data,
            timeout=5
        )
        
        if response.status_code == 200:
            logging.info(f"✓ Sent APRS packet from {packet_data.get('callsign', 'unknown')}")
            return True
        elif response.status_code == 201:
            logging.info(f"✓ Created APRS station {packet_data.get('callsign', 'unknown')}")
            return True
        else:
            logging.warning(f"Backend returned HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logging.error("Cannot connect to backend - is it running?")
        return False
    except requests.exceptions.Timeout:
        logging.error("Backend request timeout")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Backend request failed: {e}")
        return False

def main():
    """Main APRS bridge loop"""
    logging.info("=" * 60)
    logging.info("APRS Bridge starting...")
    logging.info(f"KISS server: {KISS_HOST}:{KISS_PORT}")
    logging.info(f"Backend API: {BACKEND_URL}")
    logging.info("=" * 60)
    
    retry_delay = 5  # Start with 5 second retry delay
    max_retry_delay = 60  # Cap at 60 seconds
    
    while True:
        try:
            logging.info(f"Connecting to Direwolf at {KISS_HOST}:{KISS_PORT}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second connection timeout
            sock.connect((KISS_HOST, KISS_PORT))
            sock.settimeout(None)  # Remove timeout for data reception
            
            logging.info("✓ Connected to Direwolf KISS interface")
            retry_delay = 5  # Reset retry delay on successful connection
            
            buffer = b''
            packet_count = 0
            
            while True:
                # Read data from KISS interface
                data = sock.recv(4096)
                if not data:
                    logging.warning("KISS connection closed by Direwolf")
                    break
                
                buffer += data
                
                # Look for complete KISS frames (FEND...FEND)
                while True:
                    start = buffer.find(bytes([FEND]))
                    if start == -1:
                        break
                    
                    end = buffer.find(bytes([FEND]), start + 1)
                    if end == -1:
                        break
                    
                    # Extract complete frame
                    frame = buffer[start:end+1]
                    buffer = buffer[end+1:]
                    
                    # Parse and send to backend
                    packet_str = parse_kiss_frame(frame)
                    if packet_str:
                        logging.debug(f"Raw APRS: {packet_str}")
                        packet_data = parse_aprs_packet(packet_str)
                        if packet_data:
                            if send_to_backend(packet_data):
                                packet_count += 1
                                if packet_count % 10 == 0:
                                    logging.info(f"Forwarded {packet_count} packets so far")
            
            sock.close()
            logging.info(f"Disconnected. Forwarded {packet_count} packets this session.")
            
        except ConnectionRefusedError:
            logging.error(f"Connection refused - Direwolf not listening on port {KISS_PORT}")
            logging.error(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff
            
        except socket.timeout:
            logging.error("Connection timeout - Direwolf not responding")
            time.sleep(retry_delay)
            
        except KeyboardInterrupt:
            logging.info("Received shutdown signal, exiting...")
            break
            
        except Exception as e:
            logging.error(f"Unexpected error: {type(e).__name__}: {e}")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

if __name__ == '__main__':
    main()
