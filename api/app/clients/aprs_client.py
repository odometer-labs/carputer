from psycopg import Connection, Cursor
from ..dependencies import get_connection
from ..models.aprs_packet import APRSPacket

class APRSClient:
    def __init__(self):
        self.packet_count: int = 0

    def ingest_packet(self, packet: APRSPacket):
        """
        Ingest an APRS packet and store in database
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """CALL aprs.ingest_packet(%s, %s, %s, %s)""",
                    (packet.callsign, packet.raw_packet, packet.timestamp, packet.data)
                )
                conn.commit()
                self.packet_count += 1
                return {"result": "success", "callsign": packet.callsign}

    def list_stations(self):
        """
        List all received APRS stations
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM aprs.view_all_stations();""")
                conn.commit()
                result = cursor.fetchall()
                return result

    def get_station(self, callsign_id: str):
        """
        Get details for a specific APRS station
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM aprs.get_station(%s);""", (callsign_id,))
                conn.commit()
                result = cursor.fetchall()
                return result
    
    def get_station_history(self, callsign: str, limit: int):
        """
        Get recent packet history for a station
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM aprs.get_station_history(%s, %s);""", (callsign, limit))
                conn.commit()
                result = cursor.fetchall()
                return result

# singleton object
aprs_client: APRSClient = APRSClient()
