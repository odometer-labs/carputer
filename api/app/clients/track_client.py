from psycopg import Connection, Cursor
from datetime import datetime, timezone
from ..dependencies import get_connection
from ..models.track import Track
from ..models.track_point import TrackPoint
from ..beaconing import SmartBeacon, BeaconConfig
import json


class TrackClient:
    def __init__(self):
        self.latitude: float = 0.0
        self.longitude: float = 0.0
        self.speed: float = 0.0
        self.heading: float = 0.0
        self._smart_beacon: SmartBeacon = SmartBeacon()

    def get_lat_long(self):
        return {"latitude": self.latitude, "longitude": self.longitude}

    def list_track(self):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * from gps.view_all_tracks();""")
                conn.commit()
                result = cursor.fetchall()
                return result

    def list_tracks_mvt(
        self,
        z: int,
        x: int,
        y: int,
        mode: str = "all",
        track_id: int = None,
        within_meters: int = 500,
    ):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT gps.get_tracks_mvt(%s, %s, %s, %s, %s, %s);",
                    (
                        z,
                        x,
                        y,
                        mode,
                        track_id,
                        within_meters,
                    ),
                )
                row = cursor.fetchone()
                tile_data = None
                if row:
                    tile_data = (
                        row[0] if isinstance(row, tuple) else row.get("get_tracks_mvt")
                    )

                return tile_data if tile_data is not None else b""

    def get_track(self, track_id: int):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM gps.retrieve_track(%s);""", (track_id,))
                result = cursor.fetchall()
                return result

    def update_track(self, track_id: int, track: Track):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """CALL gps.update_track(%s, %s, %s, %s)""",
                    (track_id, track.start_time, track.end_time, track.track_name),
                )
                conn.commit()
                return {"result": "success"}

    def delete_track(self, track_id: int):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""CALL gps.delete_track(%s)""", (track_id,))
                conn.commit()
                return {"result": "success"}

    def start_track(self, name: str = None):
        # Reset smart beacon state for new track
        self._smart_beacon.reset()
        
        with get_connection() as conn:
            with conn.cursor() as cursor:

                final_name = name.strip() if name and name.strip() else None
                if final_name is None:
                    cursor.execute("""SELECT gps.create_track();""")
                else:
                    cursor.execute("""SELECT gps.create_track(%s)""", (final_name,))
                track_id = cursor.fetchone()
                conn.commit()
                return track_id

    def end_track(self):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""CALL gps.end_track();""")
                conn.commit()
                return {"result": "success"}

    def add_track_point(self, track_point: TrackPoint):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """CALL gps.add_track_point(%s, %s, %s, %s, %s)""",
                    (
                        datetime.now(timezone.utc),
                        track_point.latitude,
                        track_point.longitude,
                        track_point.speed,
                        track_point.heading,
                    ),
                )
                conn.commit()
                return {"result": "success"}

    def import_track_point(self, track_id: int, track_point: TrackPoint):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """CALL gps.add_track_point(%s, %s, %s, %s, %s, %s)""",
                    (
                        track_id,
                        datetime.now(timezone.utc),
                        track_point.latitude,
                        track_point.longitude,
                        track_point.speed,
                        track_point.heading,
                    ),
                )
                conn.commit()
                return {"result": "success"}

    def get_latest_track_point(self):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM gps.get_latest_track_point()""")
                conn.commit()
                result = cursor.fetchall()
                return result

    def check_new_road(self):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT gps.is_new_road();")
                conn.commit()
                result = cursor.fetchone()
                return result

    def import_track(self, geojson_data):

        if isinstance(geojson_data, dict):
            geojson_data = json.dumps(geojson_data)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT gps.import_track(%s) as track_id;", (geojson_data,)
                )
                result = cursor.fetchone()
                return {"track_id": result["track_id"], "status": "imported"}
    
    def get_track_lines_near_location(self, p_within_meters: float):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM gps.get_track_lines_near_location(%s);""", (p_within_meters,))
                result = cursor.fetchall()
                return result

    def is_tracking_active(self) -> bool:
        """Check if there is an active track (end_time IS NULL)."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM gps.tracks WHERE end_time IS NULL);"
                )
                result = cursor.fetchone()
                return result[0] if result else False

    def process_gps_update(
        self,
        lat: float,
        lon: float,
        speed_mps: float,
        heading: float
    ) -> dict:
        """Process a GPS update with smart beaconing.
        
        Updates the current position and, if tracking is active, uses the
        smart beaconing algorithm to decide whether to save a track point.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            speed_mps: Speed in meters per second (gpsd native unit)
            heading: Heading in degrees (0-360)
            
        Returns:
            dict with keys:
                - position_updated: always True
                - point_saved: True if a track point was saved
                - tracking_active: True if a track is currently recording
        """
        # Convert speed from m/s to km/h for smart beaconing
        speed_kmh = speed_mps * 3.6 if speed_mps else 0.0
        
        # Always update current position
        self.latitude = lat
        self.longitude = lon
        self.speed = speed_mps
        self.heading = heading
        
        result = {
            "position_updated": True,
            "point_saved": False,
            "tracking_active": False
        }
        
        # Check if tracking is active
        if not self.is_tracking_active():
            return result
        
        result["tracking_active"] = True
        
        # Use smart beaconing to decide if we should save this point
        if self._smart_beacon.should_beacon(lat, lon, speed_kmh, heading):
            track_point = TrackPoint(
                latitude=lat,
                longitude=lon,
                speed=speed_mps,
                heading=heading
            )
            self.add_track_point(track_point)
            result["point_saved"] = True
        
        return result

    def reset_beacon_state(self) -> None:
        """Reset smart beacon state (call when starting a new track)."""
        self._smart_beacon.reset()

    def get_beacon_stats(self) -> dict:
        """Get smart beacon statistics."""
        return self._smart_beacon.get_stats()


# singleton object
track_client: TrackClient = TrackClient()
