import pytest
import json
from datetime import datetime
import mapbox_vector_tile


def test_db_connection(db_conn):
    """
    Verify that db_conn fixture actually works.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT 1 as connected;")
        result = cur.fetchone()
        assert result["connected"] == 1


def test_create_and_end_track(db_conn):
    """
    Test track creation and end and auto generated name.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]
        assert track_id is not None

        cur.execute("SELECT count(*) from gps.tracks as id;")
        assert cur.fetchone()["count"] == 1

        cur.execute("CALL gps.end_track();")

        cur.execute("SELECT end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()["end_time"] is not None
        cur.execute(
            "SELECT track_name FROM gps.tracks WHERE track_id = %s;", (track_id,)
        )
        generated_name = cur.fetchone()["track_name"]
        assert generated_name.startswith("Track ")

        # Check that it contains today's date (YYYY-MM-DD)
        cur.execute("SELECT TO_CHAR(NOW(), 'YYYY-MM-DD') as time;")
        today_str = cur.fetchone()["time"]
        assert today_str in generated_name

        # Verify length (Track + Space + YYYY-MM-DD + Space + HH:MM = 22 characters)
        assert len(generated_name) == 22


def test_track_name(db_conn):
    """
    Test track creation with name parameter.
    """

    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track(%s) as id", ("Hello",))
        track_id = cur.fetchone()["id"]
        assert track_id is not None

        cur.execute("SELECT count(*) from gps.tracks as id;")
        assert cur.fetchone()["count"] == 1

        cur.execute("CALL gps.end_track();")

        cur.execute("SELECT end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()["end_time"] is not None

        cur.execute(
            "SELECT track_name FROM gps.tracks WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["track_name"] == "Hello"


def test_add_track_point(db_conn, sample_track_points):
    """
    Test point insertion.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        point = sample_track_points[0]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], point["lat"], point["lon"], 0.0, 0.0),
        )

        # Check if the point exists in the points table
        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 1


def test_gps_latest_track_point(db_conn, sample_track_points):
    """
    Test gps latest track point function.
    """
    with db_conn.cursor() as cur:

        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        point = sample_track_points[0]
        point2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], point["lat"], point["lon"], 5.0, 0.0),
        )

        cur.execute("SELECT count(*) from gps.track_points WHERE speed_mps = 5.0;")
        # Checks if point exists
        assert cur.fetchone()["count"] == 1
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], point2["lat"], point2["lon"], 10.0, 0.0),
        )

        cur.execute("SELECT (gps.get_latest_track_point()).point_id as point_id;")
        latest_point_id = cur.fetchone()["point_id"]
        # Checks if point exists
        assert int(latest_point_id) > 0

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], point2["lat"], point2["lon"], 10.0, 0.0),
        )

        cur.execute("SELECT * FROM gps.get_latest_track_point();")
        result = cur.fetchone()

        # Checks if speed matches
        assert (result["speed_mps"]) == 10.0
        assert (result["point_id"]) > 0


def test_track_line_creation(db_conn, sample_track_points):
    """
    Test creation of a track line.
    """

    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        point = sample_track_points[0]
        point2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], point["lat"], point["lon"], 5.0, 0.0),
        )

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], point2["lat"], point2["lon"], 10.0, 0.0),
        )

        cur.execute(
            "SELECT count(*) as total FROM gps.track_lines WHERE track_id = %s;",
            (track_id,),
        )

        result = cur.fetchone()

        assert result["total"] == 1


def test_line_creation_one_point(db_conn, sample_track_points):
    """
    Tests track line creation with one point and two points.
    """
    with db_conn.cursor() as cur:

        # Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]
        p = sample_track_points[0]
        p2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, p["timestamp"], p["lat"], p["lon"], 10.0, 0.0),
        )

        # Line should not exist
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 0

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, p2["timestamp"], p2["lat"], p2["lon"], 10.0, 0.0),
        )

        # With two points, line should be created
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 1


def test_is_new_road(db_conn, sample_track_points):
    """
    Checks whether a new road alert is made.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        point = sample_track_points[0]
        point2 = sample_track_points[1]

        # Create line
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], point["lat"], point["lon"], 5.0, 0.0),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], point2["lat"], point2["lon"], 10.0, 0.0),
        )

        cur.execute("CALL gps.end_track();")

        # Create second line
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], 2, 2, 5.0, 0.0),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], 5, 5, 10.0, 0.0),
        )

        cur.execute("SELECT gps.is_new_road() as id;")
        # Should be a new road
        assert cur.fetchone()["id"] == True


def test_is_new_road_false1(db_conn):
    """Negative case where the second track line is not a new road."""
    with db_conn.cursor() as cur:

        # 1. Create track 1
        cur.execute("SELECT gps.create_track(%s) as id;", ("Hello",))
        tid1 = cur.fetchone()["id"]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (tid1, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.0, 0, 0);",
            (tid1, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 2. Create very close track
        cur.execute("SELECT gps.create_track() as id;")
        tid2 = cur.fetchone()["id"]
        # 0.0001 degrees latitude is roughly 11 meters
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0001, 0, 0);",
            (tid2, "2024-02-01 10:00:00+00"),
        )

        cur.execute("SELECT gps.is_new_road();")
        # Should be False because 11m < 30m
        assert cur.fetchone()["is_new_road"] is False


def test_is_new_road_false2(db_conn, sample_track_points):
    """Second negative case testing is new road function with two same exact track lines."""
    with db_conn.cursor() as cur:

        # Track 1
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        point = sample_track_points[0]
        point2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point["timestamp"], point["lat"], point["lon"], 5.0, 0.0),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2["timestamp"], point2["lat"], point2["lon"], 10.0, 0.0),
        )
        cur.execute("CALL gps.end_track();")

        # Track 2
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        # Adding same two points as before, just different timestamp.
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, "2025-01-01 10:00:00+00", point["lat"], point["lon"], 5.0, 0.0),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (
                track_id,
                "2026-01-01 10:00:00+00",
                point["lat"],
                point2["lon"],
                10.0,
                0.0,
            ),
        )

        cur.execute("SELECT gps.is_new_road() as id;")
        assert cur.fetchone()["id"] == False


def test_is_new_road_empty_database(db_conn):
    """
    If no previous tracks exist, is_new_road should return True.
    """
    with db_conn.cursor() as cur:

        # Track 1
        cur.execute("SELECT gps.create_track() as id;")
        tid = cur.fetchone()["id"]
        cur.execute("CALL gps.add_track_point(%s, NOW(), 45.0, -122.0, 0, 0);", (tid,))

        cur.execute("SELECT gps.is_new_road();")
        # Assert: No other lines exist, so nearest_distance is NULL -> returns True
        assert cur.fetchone()["is_new_road"] is True


def test_delete_track_cascades(db_conn, sample_track_points):
    """
    Verify that deleting a track removes all points and lines.
    """
    with db_conn.cursor() as cur:
        # Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]
        p = sample_track_points[0]
        p2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, p["timestamp"], p["lat"], p["lon"], 10.0, 0.0),
        )

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, p2["timestamp"], p2["lat"], p2["lon"], 10.0, 0.0),
        )

        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 2  # 2 TRACK POINTS
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 1  # 1 TRACK LINE

        # Delete the track
        cur.execute("CALL gps.delete_track(%s);", (track_id,))

        # Everything should be gone
        cur.execute("SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()["count"] == 0
        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 0
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 0


def test_delete_track_cascades_multiple_lines(db_conn, sample_track_points):
    """
    Verify that deleting a track removes all points and lines when there are more than one line.
    """
    with db_conn.cursor() as cur:
        # Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        for p in sample_track_points:
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, p["timestamp"], p["lat"], p["lon"], 10.0, 0.0),
            )

        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 4  # 4 TRACK POINTS
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 1  # 1 TRACK LINE

        # Act: End track
        cur.execute("CALL gps.end_track();")

        ########## SECOND LINE (TO BE DELETED)
        cur.execute("SELECT gps.create_track() as id;")
        delete_id = cur.fetchone()["id"]

        for p in sample_track_points:
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (delete_id, p["timestamp"], p["lat"], p["lon"], 10.0, 0.0),
            )

        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (delete_id,)
        )
        assert cur.fetchone()["count"] == 4  # 4 TRACK POINTS
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (delete_id,)
        )
        assert cur.fetchone()["count"] == 1  # 1 TRACK LINE

        # Act: End track
        cur.execute("CALL gps.delete_track(%s);", (delete_id,))

        # Assert: Everything with that id should be gone
        cur.execute(
            "SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (delete_id,)
        )
        assert cur.fetchone()["count"] == 0
        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (delete_id,)
        )
        assert cur.fetchone()["count"] == 0
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (delete_id,)
        )
        assert cur.fetchone()["count"] == 0

        # Assert: Everything with old id should be there still
        cur.execute("SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()["count"] == 1
        cur.execute(
            "SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 4
        cur.execute(
            "SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,)
        )
        assert cur.fetchone()["count"] == 1


def test_view_all_tracks(db_conn, sample_track_points):
    """
    Verify we can retrieve all tracks via the view function.
    Also verifies that the geom attribute is return as GEO JSON
    """
    with db_conn.cursor() as cur:
        # Create separate tracks
        for _ in range(4):
            cur.execute("SELECT gps.create_track() as id;")
            tid = cur.fetchone()["id"]

            for pt in sample_track_points:
                cur.execute(
                    "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (tid, pt["timestamp"], pt["lat"], pt["lon"], 0, 0),
                )
            cur.execute("CALL gps.end_track();")

        # Fetch all
        cur.execute("SELECT * FROM gps.view_all_tracks();")
        results = cur.fetchall()

        assert len(results) >= 4
        for row in results:
            assert "geom" in row
            assert isinstance(row["geom"], dict)
            assert row["geom"]["type"] == "LineString"


def test_prevent_multiple_active_tracks(db_conn):
    """
    Verify that create_track doesn't create a new record if one is already active.
    """
    with db_conn.cursor() as cur:
        # Create first track
        cur.execute("SELECT gps.create_track() as id;")
        id1 = cur.fetchone()["id"]

        # Try to create another without ending the first
        cur.execute("SELECT gps.create_track() as id;")
        id2 = cur.fetchone()["id"]

        # They should be the same ID
        assert id1 == id2

        # Verify only one row exists in the table
        cur.execute("SELECT count(*) as total FROM gps.tracks WHERE end_time IS NULL;")
        assert cur.fetchone()["total"] == 1


def test_latest_point_empty_db(db_conn):
    """
    Verify the function returns nothing when no points exist.
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM gps.get_latest_track_point();")
        result = cur.fetchone()
        assert result is None


def test_retrieve_track_not_found(db_conn):
    """
    Verify that retrieving a non-existent track returns an empty result set.
    """
    with db_conn.cursor() as cur:
        # Use an ID that definitely doesn't exist
        cur.execute("SELECT * FROM gps.retrieve_track(999999);")
        result = cur.fetchone()

        assert result is None


def test_retrieve_tracks(db_conn, sample_track_points):
    """
    Verify we can retrieve tracks via the view function.
    Also verifies whether the function returns a geom GEOJSON attribute.
    """
    with db_conn.cursor() as cur:

        track_ids = []
        cur.execute("SELECT * FROM gps.retrieve_track(999999);")
        result = cur.fetchone()
        assert result is None

        for _ in range(4):
            cur.execute("SELECT gps.create_track(%s) as id;", ("Hello",))
            tid = cur.fetchone()["id"]
            track_ids.append(tid)

            for pt in sample_track_points:
                cur.execute(
                    "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (tid, pt["timestamp"], pt["lat"], pt["lon"], 0, 0),
                )
            cur.execute("CALL gps.end_track();")

        cur.execute("SELECT * FROM gps.retrieve_track(%s);", (track_ids[0],))
        result = cur.fetchone()
        assert len(result) == 5
        assert result["geom"] is not None
        assert result["track_id"] == track_ids[0]
        assert result["track_name"] == "Hello"

        # NOW VERIFY GEOJSON
        # Extract the geom column
        geojson = result["geom"]

        # VERIFY
        # Check if it's a dictionary (JSONB is auto-parsed by the driver)
        assert isinstance(geojson, dict), "The geom column should be a dictionary"

        # Check for standard GeoJSON keys
        assert geojson["type"] == "LineString", "GeoJSON type should be LineString"
        assert "coordinates" in geojson, "GeoJSON must contain a 'coordinates' key"

        # Check if coordinates are a list of points
        assert isinstance(geojson["coordinates"], list)
        assert len(geojson["coordinates"]) >= 2

        # Verify the coordinate structure [longitude, latitude]
        # GeoJSON is ALWAYS [Long, Lat], whereas PostGIS functions often use [Lat, Long]
        first_coord = geojson["coordinates"][0]
        assert len(first_coord) == 2
        assert isinstance(first_coord[0], float)  # Longitude
        assert isinstance(first_coord[1], float)  # Latitude


def test_import_track(db_conn, sample_track_points):
    """
    Verify that import_track can receive a GEOJSON string and imports it into
    tracks and track lines. Also verifies that data retrieved can be imported back.
    """
    with db_conn.cursor() as cur:
        track_ids = []
        cur.execute("SELECT * FROM gps.retrieve_track(999999);")
        result = cur.fetchone()
        assert result is None

        for _ in range(2):
            cur.execute("SELECT gps.create_track() as id;")
            tid = cur.fetchone()["id"]
            track_ids.append(tid)

            for pt in sample_track_points:
                cur.execute(
                    "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (tid, pt["timestamp"], pt["lat"], pt["lon"], 0, 0),
                )
            cur.execute("CALL gps.end_track();")

        # Retrieve a track to import
        cur.execute("SELECT * FROM gps.retrieve_track(%s);", (track_ids[0],))
        result = cur.fetchone()

        # --Optional-- delete the track before importing
        cur.execute("CALL gps.delete_track(%s);", (track_ids[0],))
        track_to_import = result["geom"]
        geojson_string = json.dumps(track_to_import)

        cur.execute("SELECT gps.import_track(%s) as id;", (geojson_string,))
        new_track_id = cur.fetchone()["id"]

        # Check that it exists and end_time is NOT NULL
        cur.execute("SELECT * FROM gps.tracks WHERE track_id = %s;", (new_track_id,))
        result = cur.fetchone()

        assert result is not None
        assert result["start_time"] is not None
        assert (
            result["end_time"] is not None
        )  # Unlike create_track(), this should be filled
        assert result["start_time"] == result["end_time"]

        cur.execute("SELECT * FROM gps.retrieve_track(%s);", (new_track_id,))
        result = cur.fetchone()

        assert result is not None
        assert "geom" in result
        assert result["geom"]["type"] == "LineString"
        assert isinstance(result["geom"], dict)


def test_import_track_timing_and_geom(db_conn):
    """
    Verifies that imported tracks have matching start/end times
    and valid geometry parsing.
    """
    with db_conn.cursor() as cur:

        mock_geojson1 = (
            '{"type": "LineString", "coordinates": [[-122.6, 45.5], [-122.61, 45.51]]}'
        )
        mock_geojson2 = (
            '{"type": "LineString", "coordinates": [[-12.6, 45.5], [-12.61, 45.51]]}'
        )
        geojson_list = [mock_geojson1, mock_geojson2]

        for mock_geojson in geojson_list:
            cur.execute("SELECT gps.import_track(%s) as id;", (mock_geojson,))
            new_id = cur.fetchone()["id"]

            cur.execute(
                "SELECT start_time, end_time FROM gps.tracks WHERE track_id = %s;",
                (new_id,),
            )
            meta = cur.fetchone()

            assert meta["start_time"] is not None
            assert meta["end_time"] is not None
            assert (
                meta["start_time"] == meta["end_time"]
            ), "Start and End times must match for imported tracks"

            cur.execute("SELECT * FROM gps.retrieve_track(%s);", (new_id,))
            result = cur.fetchone()
            assert result["geom"]["type"] == "LineString"
            assert isinstance(result["geom"], dict)


def test_update_track_metadata(db_conn):
    """
    Verify we can manually update the start and end times of a track.
    """
    with db_conn.cursor() as cur:

        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        new_start = "2026-01-01 08:00:00+00"
        new_end = "2026-01-01 09:00:00+00"
        new_track_name = "Hello"

        cur.execute(
            "CALL gps.update_track(%s, %s, %s, %s);",
            (track_id, new_start, new_end, new_track_name),
        )

        cur.execute(
            "SELECT start_time, end_time, track_name FROM gps.tracks WHERE track_id = %s;",
            (track_id,),
        )
        updated = cur.fetchone()

        assert str(updated["start_time"]).startswith("2026-01-01 08:00:00")
        assert str(updated["end_time"]).startswith("2026-01-01 09:00:00")
        assert str(updated["track_name"]) == "Hello"


def test_get_tracks_near_location(db_conn):
    """
    Verify spatial filtering: find nearby tracks but ignore the current one.
    Also verifies that the geom attribute returned is GEO JSON
    """
    with db_conn.cursor() as cur:
        # 1. SETUP: Create "Old Track A" (Nearby)
        # Location: roughly (0,0)
        cur.execute("SELECT gps.create_track() as id;")
        id_near = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (id_near, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.001, 0, 0);",
            (id_near, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 2. SETUP: Create "Old Track B" (Far away)
        # Location: roughly (1,1) -> which is ~150km away
        cur.execute("SELECT gps.create_track() as id;")
        id_far = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.0, 1.0, 0, 0);",
            (id_far, "2024-02-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.001, 1.001, 0, 0);",
            (id_far, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 3. SETUP: Create "Current Track" (The search origin)
        # Place a point right next to Track A (approx 10m away)
        cur.execute("SELECT gps.create_track() as id;")
        current_id = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0, 0, 0);",
            (current_id, "2024-03-01 10:00:00+00"),
        )

        # 4. ACT: Search for tracks within 500 meters
        cur.execute("SELECT * FROM gps.get_track_lines_near_location(500);")
        results = cur.fetchall()

        # 5. ASSERT
        # We expect exactly 1 result (Track A).
        # Track B is too far, and Current Track is excluded by the SQL (t.track_id <> p.track_id).
        assert len(results) == 1
        assert results[0]["track_id"] == id_near

        # 6. Search with a huge radius (200km)
        cur.execute("SELECT * FROM gps.get_track_lines_near_location(200000);")
        results_large = cur.fetchall()

        # Now both Old Track A and Old Track B should be retrieved
        assert len(results_large) == 2

        cur.execute("SELECT * FROM gps.get_track_lines_near_location(0);")
        results_zero = cur.fetchall()
        assert len(results_zero) == 0

        # VERIFY GEOJSON
        for row in results_large:
            assert "geom" in row
            assert isinstance(row["geom"], dict)
            assert row["geom"]["type"] == "LineString"


def test_get_tracks_using_road(db_conn):
    """
    Verify spatial filtering: find nearby tracks using the current road.
    Also verifies whether the geom attribute is returned as GEOJSON.
    """
    with db_conn.cursor() as cur:
        # 1. SETUP: Create "Old Track A" (Nearby)
        # Location: roughly (0,0)
        cur.execute("SELECT gps.create_track() as id;")
        id_near = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (id_near, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.001, 0, 0);",
            (id_near, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # Another nearby track
        cur.execute("SELECT gps.create_track() as id;")
        id_near2 = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (id_near2, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.001, 0, 0);",
            (id_near2, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 2. SETUP: Create "Old Track B" (Far away)
        # Location: roughly (1,1) -> which is ~150km away
        cur.execute("SELECT gps.create_track() as id;")
        id_far = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.0, 1.0, 0, 0);",
            (id_far, "2024-02-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.001, 1.001, 0, 0);",
            (id_far, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # Another far away track
        cur.execute("SELECT gps.create_track() as id;")
        id_far = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.0, 1.0, 0, 0);",
            (id_far, "2024-02-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.001, 1.001, 0, 0);",
            (id_far, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 3. SETUP: Create "Current Track" (The search origin)
        # Place a point right next to Track A (approx 10m away)
        cur.execute("SELECT gps.create_track() as id;")
        current_id = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0, 0, 0);",
            (current_id, "2024-03-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0, 0, 0);",
            (current_id, "2024-03-01 10:00:50+00"),
        )

        # 4. Search for tracks within 500 meters
        cur.execute("SELECT * FROM gps.get_track_lines_using_road();")
        results = cur.fetchall()

        assert len(results) == 2
        assert results[0]["track_id"] == id_near
        assert results[0]["end_time"] is not None

        # NOW VERIFY GEOJSON
        for row in results:
            assert "geom" in row
            assert isinstance(row["geom"], dict)
            assert row["geom"]["type"] == "LineString"

        # NOW VERIFY GEOJSON
        for row in results:
            assert "geom" in row
            assert isinstance(row["geom"], dict)
            assert row["geom"]["type"] == "LineString"


def test_get_tracks_using_no_road(db_conn):
    """
    Verify spatial filtering: find nearby tracks using the current road.
    This test should fail due to only having one point in the current track,
    thus no road is created to compare with.
    """

    with db_conn.cursor() as cur:
        # 1. SETUP: Create "Old Track A" (Nearby)
        # Location: roughly (0,0)
        cur.execute("SELECT gps.create_track() as id;")
        id_near = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (id_near, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.001, 0, 0);",
            (id_near, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 2. SETUP: Create "Old Track B" (Far away)
        # Location: roughly (1,1) -> which is ~150km away
        cur.execute("SELECT gps.create_track() as id;")
        id_far = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.0, 1.0, 0, 0);",
            (id_far, "2024-02-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.001, 1.001, 0, 0);",
            (id_far, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # 3. SETUP: Create "Current Track" (The search origin)
        # Place a point right next to Track A (approx 10m away)
        cur.execute("SELECT gps.create_track() as id;")
        current_id = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0, 0, 0);",
            (current_id, "2024-03-01 10:00:00+00"),
        )

        # 4. Search for tracks within 500 meters
        cur.execute("SELECT * FROM gps.get_track_lines_using_road();")
        results = cur.fetchall()

        assert len(results) == 0


def test_validate_geometry_repairs_invalid_line(db_conn):
    """
    Tests whether linestring is repaired by validate_geometry.
    Note: Current linestring creation doesn't allow polygons,
    thus testing if validate_geometry does something.
    """
    with db_conn.cursor() as cur:

        cur.execute("SELECT gps.create_track() AS track_id;")
        track_id = cur.fetchone()["track_id"]

        # Insert an "Invalid" LineString.
        # A 'figure-8' LineString is technically valid in PostGIS but NOT simple.
        invalid_wkt = "LINESTRING(0 0, 1 1, 0 1, 1 0, 0 0)"

        cur.execute(
            """
            INSERT INTO gps.track_lines (track_id, geom) 
            VALUES (%s, ST_GeomFromText(%s, 4326)::geography)
            ON CONFLICT (track_id) DO UPDATE SET geom = EXCLUDED.geom;
        """,
            (track_id, invalid_wkt),
        )

        cur.execute(
            """
            SELECT 
                ST_IsValid(geom::geometry) as was_valid, 
                ST_IsSimple(geom::geometry) as was_simple 
            FROM gps.track_lines WHERE track_id = %s
        """,
            (track_id,),
        )

        before = cur.fetchone()

        cur.execute("CALL gps.validate_geometry(%s)", (track_id,))

        cur.execute(
            """
            SELECT 
                ST_IsValid(geom::geometry) as is_valid_now, 
                ST_IsSimple(geom::geometry) as is_simple_now, 
                ST_AsText(geom) as current_wkt
            FROM gps.track_lines WHERE track_id = %s
        """,
            (track_id,),
        )

        after = cur.fetchone()

        # Note: Simplicity and Validity didn't change.
        assert before["was_simple"] is False
        assert after["is_valid_now"] is True

        # PostGIS added nodes
        assert after["current_wkt"] != invalid_wkt

        assert "LINESTRING" in after["current_wkt"].upper()


def test_geometry_structure_after_validation(db_conn, sample_track_points):
    """
    Tests whether validating a track leaves the track line as a line string
    """
    with db_conn.cursor() as cur:
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()["id"]

        for p in sample_track_points:
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, p["timestamp"], p["lat"], p["lon"], 10.0, 0.0),
            )

        cur.execute("CALL gps.validate_geometry(%s)", (track_id,))

        cur.execute(
            "SELECT ST_GeometryType(geom::geometry) as geom FROM gps.track_lines WHERE track_id = %s",
            (track_id,),
        )
        geom_type = cur.fetchone()["geom"]

        assert "LineString" in geom_type


# ---------------------------
# 1. ALL MODE
# ---------------------------
def test_get_tracks_mvt_all_mode(db_conn):
    """
    Verify retrieving all tracks as a mapbox vector tile.
    """
    with db_conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gps.tracks (track_id, start_time, end_time)
            VALUES (1001, NOW(), NOW());

            INSERT INTO gps.track_lines (track_id, geom, geom_wm)
            VALUES (
                1001,
                ST_GeogFromText('LINESTRING(0 0, 1 1)'),
                ST_Transform(ST_GeomFromText('LINESTRING(0 0, 1 1)', 4326), 3857)
            );
        """)

        cur.execute("SELECT gps.get_tracks_mvt(0,0,0,'all') AS tile;")
        tile_binary = cur.fetchone()["tile"]

    assert tile_binary is not None
    assert len(tile_binary) > 0

    decoded = mapbox_vector_tile.decode(tile_binary)
    assert "tracks_layer" in decoded

    features = decoded["tracks_layer"]["features"]
    assert len(features) > 0

    assert int(features[0]["properties"]["track_id"]) == 1001


# ---------------------------
# 2. SINGLE MODE
# ---------------------------
def test_get_tracks_mvt_single_mode(db_conn):
    """
    Verify retrieving a single track with a specified track id as a mapbox vector tile.
    """
    with db_conn.cursor() as cur:
        cur.execute("""
            INSERT INTO gps.tracks (track_id, start_time, end_time)
            VALUES (2001, NOW(), NOW());

            INSERT INTO gps.track_lines (track_id, geom, geom_wm)
            VALUES (
                2001,
                ST_GeogFromText('LINESTRING(0 0, 1 1)'),
                ST_Transform(ST_GeomFromText('LINESTRING(0 0, 1 1)', 4326), 3857)
            );
        """)

        cur.execute("""
            SELECT gps.get_tracks_mvt(0,0,0,'single', 2001) AS tile;
        """)
        tile_binary = cur.fetchone()["tile"]

    assert tile_binary is not None
    assert len(tile_binary) > 0

    decoded = mapbox_vector_tile.decode(tile_binary)
    features = decoded["tracks_layer"]["features"]

    assert len(features) == 1
    assert int(features[0]["properties"]["track_id"]) == 2001


def test_get_tracks_mvt_nearby_mode(db_conn):
    """
    Verify spatial filtering: find nearby tracks but ignore the current one as
    a mapbox vector tile.
    """
    with db_conn.cursor() as cur:

        # Create "Old Track A" (Nearby)
        # Location: roughly (0,0)
        cur.execute("SELECT gps.create_track() as id;")
        id_near = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);",
            (id_near, "2024-01-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.001, 0.001, 0, 0);",
            (id_near, "2024-01-01 10:00:50+00"),
        )
        cur.execute("CALL gps.end_track();")

        # Create "Old Track B" (Far away)
        # Location: roughly (1,1) -> which is ~150km away
        cur.execute("SELECT gps.create_track() as id;")
        id_far = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.0, 1.0, 0, 0);",
            (id_far, "2024-02-01 10:00:00+00"),
        )
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 1.001, 1.001, 0, 0);",
            (id_far, "2024-01-01 10:00:50+00"),
        )

        cur.execute("CALL gps.end_track();")

        # Create "Current Track" (The search origin)
        # Place a point right next to Track A (approx 10m away)
        cur.execute("SELECT gps.create_track() as id;")
        current_id = cur.fetchone()["id"]
        cur.execute(
            "CALL gps.add_track_point(%s, %s, 0.0001, 0.0, 0, 0);",
            (current_id, "2024-03-01 10:00:00+00"),
        )

        # Search for tracks within 5000 meters
        cur.execute(
            # Specific tile specification (z,x,y) parameters are needed (i.e. 14, 8192, 8192)
            # Singular gps track point from gps.get_latest_track_point() will be erased
            # by the bounding box if it is too large (i.e. z,x,y = 0,0,0 (whole world))
            "SELECT gps.get_tracks_mvt(14, 8192, 8192, 'nearby', NULL, 5000) AS tile;"
        )
        tile_binary = cur.fetchone()["tile"]

        # ASSERT
        # We expect exactly 1 result (Track A).
        # Track B is too far, and Current Track is excluded by the SQL (t.track_id <> p.track_id).
        # Assertions
        assert tile_binary is not None
        assert len(tile_binary) > 0

        decoded = mapbox_vector_tile.decode(tile_binary)
        assert "tracks_layer" in decoded

        features = decoded["tracks_layer"]["features"]
        assert len(features) > 0

        found_ids = [int(f["properties"]["track_id"]) for f in features]
        assert id_near in found_ids
        assert id_far not in found_ids


# ---------------------------
# 4. ROAD MODE
# ---------------------------


def test_get_tracks_mvt_road_mode(db_conn):
    """
    Verify spatial filtering: retrieve all tracks that use the same road as the
    current track (excluding current track) a mapbox vector tile.
    """
    with db_conn.cursor() as cur:
        # Active track (reference)
        cur.execute("""
            INSERT INTO gps.tracks (track_id, start_time, end_time)
            VALUES (4001, NOW(), NULL);

            INSERT INTO gps.track_lines (track_id, geom, geom_wm)
            VALUES (
                4001,
                ST_GeogFromText('LINESTRING(0 0, 1 1)'),
                ST_Transform(ST_GeomFromText('LINESTRING(0 0, 1 1)', 4326), 3857)
            );
        """)

        # Nearby completed track (should be returned)
        cur.execute("""
            INSERT INTO gps.tracks (track_id, start_time, end_time)
            VALUES (4002, NOW(), NOW());

            INSERT INTO gps.track_lines (track_id, geom, geom_wm)
            VALUES (
                4002,
                ST_GeogFromText('LINESTRING(0 0, 1 1)'),
                ST_Transform(ST_GeomFromText('LINESTRING(0 0, 1 1)', 4326), 3857)
            );
        """)

        # Far completed track (should NOT be returned)
        cur.execute("""
            INSERT INTO gps.tracks (track_id, start_time, end_time)
            VALUES (4003, NOW(), NOW());

            INSERT INTO gps.track_lines (track_id, geom, geom_wm)
            VALUES (
                4003,
                ST_GeogFromText('LINESTRING(10 10, 11 11)'),
                ST_Transform(ST_GeomFromText('LINESTRING(10 10, 11 11)', 4326), 3857)
            );
        """)

        # Execute track retrieval
        cur.execute("""
            SELECT gps.get_tracks_mvt(0,0,0,'road') AS tile;
        """)
        tile_binary = cur.fetchone()["tile"]

    # Assertions
    assert tile_binary is not None
    assert len(tile_binary) > 0

    decoded = mapbox_vector_tile.decode(tile_binary)
    assert "tracks_layer" in decoded

    features = decoded["tracks_layer"]["features"]
    assert len(features) > 0

    found_ids = [int(f["properties"]["track_id"]) for f in features]

    assert 4002 in found_ids  # nearby completed track
    assert 4001 not in found_ids  # active track excluded
    assert 4003 not in found_ids  # far track excluded
