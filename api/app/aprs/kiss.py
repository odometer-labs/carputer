"""
KISS Protocol Client for Direwolf

Connects to Direwolf's KISS TCP interface and yields decoded APRS packets.
KISS (Keep It Simple, Stupid) is a framing protocol for TNC communication.

References:
- KISS TNC spec: http://www.ax25.net/kiss.aspx
"""

import socket
import logging
import threading
import time
from typing import Optional, Callable, Generator
from dataclasses import dataclass
from queue import Queue, Empty

logger = logging.getLogger(__name__)


# KISS special bytes
FEND = 0xC0   # Frame End
FESC = 0xDB   # Frame Escape
TFEND = 0xDC  # Transposed Frame End
TFESC = 0xDD  # Transposed Frame Escape

# KISS command codes
DATA_FRAME = 0x00
TX_DELAY = 0x01
PERSISTENCE = 0x02
SLOT_TIME = 0x03
TX_TAIL = 0x04
FULL_DUPLEX = 0x05
SET_HARDWARE = 0x06
RETURN = 0xFF


@dataclass
class KISSConfig:
    """Configuration for KISS connection"""
    host: str = "localhost"
    port: int = 8001
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = -1  # -1 = infinite
    recv_buffer_size: int = 4096


class KISSClient:
    """
    KISS protocol client for Direwolf TCP interface.
    
    Usage:
        client = KISSClient()
        client.connect()
        for packet in client.read_packets():
            print(f"Received: {packet}")
    """
    
    def __init__(self, config: Optional[KISSConfig] = None):
        self.config = config or KISSConfig()
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._running = False
        self._buffer = bytearray()
        self._packet_queue: Queue = Queue()
        self._read_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    def connect(self) -> bool:
        """
        Connect to Direwolf KISS TCP interface.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0)
            self._socket.connect((self.config.host, self.config.port))
            self._socket.settimeout(1.0)  # For non-blocking reads
            self._connected = True
            logger.info(f"Connected to Direwolf at {self.config.host}:{self.config.port}")
            return True
        except (socket.error, ConnectionRefusedError) as e:
            logger.error(f"Failed to connect to Direwolf: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Direwolf"""
        self._running = False
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        logger.info("Disconnected from Direwolf")
    
    def start_async(self, callback: Callable[[str], None]):
        """
        Start reading packets in a background thread.
        
        Args:
            callback: Function to call with each decoded packet string
        """
        if self._running:
            return
        
        self._running = True
        self._read_thread = threading.Thread(
            target=self._async_read_loop,
            args=(callback,),
            daemon=True
        )
        self._read_thread.start()
    
    def stop_async(self):
        """Stop the background read thread"""
        self._running = False
        if self._read_thread:
            self._read_thread.join(timeout=2.0)
            self._read_thread = None
    
    def _async_read_loop(self, callback: Callable[[str], None]):
        """Background thread for reading packets"""
        reconnect_attempts = 0
        
        while self._running:
            if not self._connected:
                if self.config.max_reconnect_attempts >= 0:
                    if reconnect_attempts >= self.config.max_reconnect_attempts:
                        logger.error("Max reconnect attempts reached")
                        break
                
                logger.info(f"Attempting to connect to Direwolf...")
                if self.connect():
                    reconnect_attempts = 0
                else:
                    reconnect_attempts += 1
                    time.sleep(self.config.reconnect_delay)
                    continue
            
            try:
                data = self._socket.recv(self.config.recv_buffer_size)
                if not data:
                    logger.warning("Connection closed by Direwolf")
                    self._connected = False
                    continue
                
                for packet in self._process_data(data):
                    try:
                        callback(packet)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                        
            except socket.timeout:
                continue
            except socket.error as e:
                logger.error(f"Socket error: {e}")
                self._connected = False
                time.sleep(self.config.reconnect_delay)
    
    def read_packets(self) -> Generator[str, None, None]:
        """
        Generator that yields decoded APRS packet strings.
        Blocks until a packet is available.
        
        Yields:
            Decoded APRS packet strings
        """
        while True:
            if not self._connected:
                if not self.connect():
                    time.sleep(self.config.reconnect_delay)
                    continue
            
            try:
                data = self._socket.recv(self.config.recv_buffer_size)
                if not data:
                    self._connected = False
                    continue
                
                for packet in self._process_data(data):
                    yield packet
                    
            except socket.timeout:
                continue
            except socket.error as e:
                logger.error(f"Socket error: {e}")
                self._connected = False
    
    def _process_data(self, data: bytes) -> Generator[str, None, None]:
        """
        Process received data and extract KISS frames.
        
        Args:
            data: Raw bytes from socket
            
        Yields:
            Decoded packet strings
        """
        self._buffer.extend(data)
        
        while True:
            # Look for FEND markers
            start = self._buffer.find(bytes([FEND]))
            if start == -1:
                self._buffer.clear()
                break
            
            # Remove any data before first FEND
            if start > 0:
                self._buffer = self._buffer[start:]
            
            # Look for end FEND
            end = self._buffer.find(bytes([FEND]), 1)
            if end == -1:
                break
            
            # Extract frame
            frame = bytes(self._buffer[1:end])
            self._buffer = self._buffer[end + 1:]
            
            # Decode frame
            packet = self._decode_kiss_frame(frame)
            if packet:
                yield packet
    
    def _decode_kiss_frame(self, frame: bytes) -> Optional[str]:
        """
        Decode a KISS frame to an AX.25/APRS packet string.
        
        Args:
            frame: Raw KISS frame (without FEND markers)
            
        Returns:
            Decoded packet string, or None if invalid
        """
        if not frame:
            return None
        
        # First byte is command (should be 0x00 for data)
        cmd = frame[0]
        if cmd != DATA_FRAME:
            return None
        
        # Rest is the packet data
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
        
        # Decode AX.25 frame to APRS packet string
        return self._decode_ax25(bytes(unescaped))
    
    def _decode_ax25(self, frame: bytes) -> Optional[str]:
        """
        Decode AX.25 frame to APRS packet string.
        
        Args:
            frame: AX.25 frame bytes
            
        Returns:
            APRS packet string (e.g., "W1ABC>APRS,WIDE1-1:!4903.50N/07201.75W-")
        """
        try:
            if len(frame) < 16:  # Minimum AX.25 header
                return None
            
            # Destination address (7 bytes)
            dest_bytes = frame[0:7]
            dest = self._decode_ax25_address(dest_bytes)
            
            # Source address (7 bytes)
            source_bytes = frame[7:14]
            source = self._decode_ax25_address(source_bytes)
            
            # Check for digipeater addresses
            path = []
            idx = 14
            
            # Check if address extension bit is set (bit 0 of last byte)
            while idx < len(frame) - 2 and (frame[idx - 1] & 0x01) == 0:
                if idx + 7 > len(frame):
                    break
                digi_bytes = frame[idx:idx + 7]
                digi = self._decode_ax25_address(digi_bytes)
                if digi:
                    # Check if digipeater has been used (H bit)
                    if digi_bytes[6] & 0x80:
                        digi += '*'
                    path.append(digi)
                idx += 7
            
            # Skip control and PID bytes
            if idx + 2 > len(frame):
                return None
            
            # Control field
            ctrl = frame[idx]
            idx += 1
            
            # PID field (only for I-frames and UI-frames)
            if (ctrl & 0x01) == 0 or (ctrl & 0xEF) == 0x03:
                if idx >= len(frame):
                    return None
                idx += 1
            
            # Rest is information field
            info = frame[idx:].decode('latin-1', errors='replace')
            
            # Build packet string
            path_str = dest
            if path:
                path_str += ',' + ','.join(path)
            
            packet = f"{source}>{path_str}:{info}"
            return packet
            
        except Exception as e:
            logger.debug(f"AX.25 decode error: {e}")
            return None
    
    def _decode_ax25_address(self, addr_bytes: bytes) -> Optional[str]:
        """
        Decode AX.25 address field.
        
        Args:
            addr_bytes: 7 bytes of address data
            
        Returns:
            Callsign-SSID string (e.g., "W1ABC-10")
        """
        try:
            # Callsign is 6 bytes, each shifted left 1 bit
            callsign = ""
            for i in range(6):
                c = (addr_bytes[i] >> 1) & 0x7F
                if c != 0x20:  # Space padding
                    callsign += chr(c)
            
            # SSID is in bits 1-4 of byte 7
            ssid = (addr_bytes[6] >> 1) & 0x0F
            
            if ssid > 0:
                return f"{callsign}-{ssid}"
            else:
                return callsign
                
        except Exception as e:
            logger.debug(f"Address decode error: {e}")
            return None


# Default client instance
kiss_client = KISSClient()
