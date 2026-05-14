from pydantic import BaseModel

class APRSPacket(BaseModel):
    """
    The model representing an APRS packet from Direwolf
    """
    callsign: str
    raw_packet: str
    timestamp: str
    data: str
