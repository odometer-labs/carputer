from psycopg import Connection, Cursor
from datetime import datetime, timezone
from ..dependencies import get_connection
from ..models.track import Track
from ..models.track_point import TrackPoint
import json


class TrackClient:
    def __init__(self):
        self.latitude: float = 0.0
        self.longitude: float = 0.0
        self.speed: float = 0.0
        self.heading: float = 0.0

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


# singleton object
track_client: TrackClient = TrackClient()
