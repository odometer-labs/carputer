import pytest
from datetime import datetime

def test_db_connection(db_conn):
    """Verify that our db_conn fixture actually works."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT 1 as connected;")
        result = cur.fetchone()
        assert result['connected'] == 1

def test_create_and_delete_track(db_conn):
    """Test the lifecycle of a track (Start -> End -> Delete)."""
    with db_conn.cursor() as cur:
        # 1. Create a track using your SQL function
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        assert track_id is not None
        
        # 1.5. Check the gps tracks table
        cur.execute("SELECT count(*) from gps.tracks as id;")
        assert cur.fetchone()['count'] == 1

        # 2. End the track
        cur.execute("CALL gps.end_track();")
        
        # 3. Verify it's closed (end_time should no longer be NULL)
        cur.execute("SELECT end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['end_time'] is not None

def test_add_track_point(db_conn, sample_track_points):
    """Test inserting a point into a track."""
    with db_conn.cursor() as cur:
        # Setup: Need a track first
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        
        # Data from your fixture
        point = sample_track_points[0]
        
        # Act: Call your stored procedure
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point['timestamp'], point['lat'], point['lon'], 0.0, 0.0)
        )
        
        # Assert: Check if the point exists in the points table
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1


def test_gps_latest_track_point(db_conn, sample_track_points):
     with db_conn.cursor() as cur:
        # Setup: Need a track first
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        
        # Data from your fixture
        point = sample_track_points[0]
        point2 = sample_track_points[1]
        # Act: Call your stored procedure
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point['timestamp'], point['lat'], point['lon'], 5.0, 0.0)
        )

        cur.execute("SELECT count(*) from gps.track_points WHERE speed_mph = 5.0;")
        assert cur.fetchone()['count'] == 1
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2['timestamp'], point2['lat'], point2['lon'], 10.0, 0.0)
        )
        # Instead of selecting the composite as id, fetch a specific field
        cur.execute("SELECT (gps.get_latest_track_point()).point_id as point_id;")
        latest_point_id = cur.fetchone()['point_id']
        assert int(latest_point_id) > 0

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2['timestamp'], point2['lat'], point2['lon'], 10.0, 0.0)
        )
        # Verify the latest point's speed
        # cur.execute("SELECT (gps.get_latest_track_point()).speed_mph as speed;")
        # latest_speed = cur.fetchone()['speed']
        # assert float(latest_speed) == 10.0

        cur.execute("SELECT * FROM gps.get_latest_track_point();")
        result = cur.fetchone()

        assert (result['speed_mph']) == 10.0

        # 4. If you really want to check the ID, just check that it's a number
        assert (result['point_id']) > 0
def test_track_line_creation(db_conn, sample_track_points):
   
     with db_conn.cursor() as cur:
        # Setup: Need a track first
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        
        # Data from your fixture
        point = sample_track_points[0]
        point2 = sample_track_points[1]
        # Act: Call your stored procedure
        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point['timestamp'], point['lat'], point['lon'], 5.0, 0.0)
        )

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, point2['timestamp'], point2['lat'], point2['lon'], 10.0, 0.0)
        )

        cur.execute("SELECT count(*) as total FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        
        result = cur.fetchone()
        
        # 3. Assert using the new key 'total'
        assert result['total'] == 1

def test_is_new_road(db_conn, sample_track_points):
    with db_conn.cursor() as cur:
            # Setup: Need a track first
            cur.execute("SELECT gps.create_track() as id;")
            track_id = cur.fetchone()['id']
            
            # Data from your fixture
            point = sample_track_points[0]
            point2 = sample_track_points[1]
            # Act: Call your stored procedure
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point['timestamp'], point['lat'], point['lon'], 5.0, 0.0)
            )
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point2['timestamp'], point2['lat'], point2['lon'], 10.0, 0.0)
            )

            cur.execute("CALL gps.end_track();")
   
            cur.execute("SELECT gps.create_track() as id;")
            track_id = cur.fetchone()['id']
            
            # Act: Call your stored procedure
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point['timestamp'], 2, 2, 5.0, 0.0)
            )
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point2['timestamp'], 5, 5, 10.0, 0.0)
            )

            cur.execute(
                "SELECT gps.is_new_road() as id;"
            )
            assert cur.fetchone()['id'] == True


def test_is_new_road_false(db_conn, sample_track_points):
    with db_conn.cursor() as cur:
            # Setup: Need a track first
            cur.execute("SELECT gps.create_track() as id;")
            track_id = cur.fetchone()['id']
            
            # Data from your fixture
            point = sample_track_points[0]
            point2 = sample_track_points[1]
            # Act: Call your stored procedure
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point['timestamp'], point['lat'], point['lon'], 5.0, 0.0)
            )
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, point2['timestamp'], point2['lat'], point2['lon'], 10.0, 0.0)
            )

            cur.execute("CALL gps.end_track();")
   
            cur.execute("SELECT gps.create_track() as id;")
            track_id = cur.fetchone()['id']
            
            #Adding same two points as before, just different timestamp.
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, "2025-01-01 10:00:00+00", point['lat'], point['lon'], 5.0, 0.0)
            )
            cur.execute(
                "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                (track_id, "2026-01-01 10:00:00+00", point['lat'], point2['lon'], 10.0, 0.0)
            )
            

            cur.execute(
                "SELECT gps.is_new_road() as id;"
            )
            assert cur.fetchone()['id'] == False



def test_gps_latest_track_point2(db_conn, sample_track_points):
     with db_conn.cursor() as cur:

        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        
        point = sample_track_points[0]
        point2 = sample_track_points[1]

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, "2025-01-01 10:00:00+00", point['lat'], point['lon'], 5.0, 0.0)
        )

        cur.execute(
            "CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
            (track_id, "2025-01-01 10:00:50+00", point2['lat'], point2['lon'], 10.0, 0.0)
        )

        cur.execute("SELECT gps.get_latest_track_point() as id;")
        assert float(cur.fetchone()['id'][4]) == 10.0 
