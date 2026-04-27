from fastapi import APIRouter
from ..logging.handlers import logger
from app.models.aprs_packet import APRSPacket
from app.clients.aprs_client import aprs_client

router = APIRouter(prefix="/v1", tags=["APRS"])

@router.post("/aprs/ingest")
async def ingest_aprs_packet(packet: APRSPacket):
    """
    Ingests an APRS packet from the Direwolf bridge
    """
    logger.info(f"Received APRS packet from {packet.callsign}")
    return aprs_client.ingest_packet(packet)

@router.get("/aprs/stations")
async def list_aprs_stations():
    """
    Lists all received APRS stations
    """
    return aprs_client.list_stations()

@router.get("/aprs/stations/{callsign}")
async def get_aprs_station(callsign: str):
    """
    Retrieves details for a specific APRS station
    """
    return aprs_client.get_station(callsign)
