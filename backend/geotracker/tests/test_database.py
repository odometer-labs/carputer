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

def test_line_creation_one_point(db_conn, sample_track_points):
    with db_conn.cursor() as cur:
        # Setup: Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        p = sample_track_points[0]
        p2 = sample_track_points[1]
        
        
        cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (track_id, p['timestamp'], p['lat'], p['lon'], 10.0, 0.0))
        
        #Line should not exist
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 0

        cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (track_id, p2['timestamp'], p2['lat'], p2['lon'], 10.0, 0.0))

        #With two points, line should be created
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1

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

def test_is_new_road_false1(db_conn):
    with db_conn.cursor() as cur:
        # 1. Create an old track (A straight line)
        cur.execute("SELECT gps.create_track() as id;")
        tid1 = cur.fetchone()['id']
        # Point A (0,0) and Point B (0, 0.001)
        cur.execute("CALL gps.add_track_point(%s, %s, 0.0, 0.0, 0, 0);", (tid1, "2024-01-01 10:00:00+00"))
        cur.execute("CALL gps.add_track_point(%s, %s, 0.001, 0.0, 0, 0);", (tid1,"2024-01-01 10:00:50+00"))
        cur.execute("CALL gps.end_track();")

        # 2. Start a new track very close by (approx 11 meters away)
        cur.execute("SELECT gps.create_track() as id;")
        tid2 = cur.fetchone()['id']
        # 0.0001 degrees latitude is roughly 11 meters
        cur.execute("CALL gps.add_track_point(%s, %s, 0.0001, 0.0001, 0, 0);", (tid2, "2024-02-01 10:00:00+00"))

        cur.execute("SELECT gps.is_new_road();")
        # Should be False because 11m < 30m
        assert cur.fetchone()['is_new_road'] is False
        
def test_is_new_road_false2(db_conn, sample_track_points):
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

def test_is_new_road_empty_database(db_conn):
    """If no previous tracks exist, is_new_road should return True."""
    with db_conn.cursor() as cur:
        # Setup: Create just one track and one point
        cur.execute("SELECT gps.create_track() as id;")
        tid = cur.fetchone()['id']
        cur.execute("CALL gps.add_track_point(%s, NOW(), 45.0, -122.0, 0, 0);", (tid,))

        # Act
        cur.execute("SELECT gps.is_new_road();")
        # Assert: No other lines exist, so nearest_distance is NULL -> returns True
        assert cur.fetchone()['is_new_road'] is True

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




def test_delete_track_cascades(db_conn, sample_track_points):
    """Verify that deleting a track removes all points and lines."""
    with db_conn.cursor() as cur:
        # Setup: Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        p = sample_track_points[0]
        p2 = sample_track_points[1]
        
        
        cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (track_id, p['timestamp'], p['lat'], p['lon'], 10.0, 0.0))

        cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                    (track_id, p2['timestamp'], p2['lat'], p2['lon'], 10.0, 0.0))

      
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 2 #2 TRACK POINTS
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1 #1 TRACK LINE

        # Act: Delete the track
        cur.execute("CALL gps.delete_track(%s);", (track_id,))

        # Assert: Everything should be gone
        cur.execute("SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 0
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 0
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 0


def test_delete_track_cascades_multiple_lines(db_conn, sample_track_points):
    """Verify that deleting a track removes all points and lines when there are more than one line."""
    with db_conn.cursor() as cur:
        # Setup: Create track and add points (which triggers line creation)
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']

        
        for p in sample_track_points:
            cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                        (track_id, p['timestamp'], p['lat'], p['lon'], 10.0, 0.0))

      
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 4 #4 TRACK POINTS
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1 #1 TRACK LINE

        # Act: End track
        cur.execute("CALL gps.end_track();")

        ########## SECOND LINE (TO BE DELETED)
        cur.execute("SELECT gps.create_track() as id;")
        delete_id = cur.fetchone()['id']
        
        for p in sample_track_points:
            cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                        (delete_id, p['timestamp'], p['lat'], p['lon'], 10.0, 0.0))
      
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (delete_id,))
        assert cur.fetchone()['count'] == 4 #4 TRACK POINTS
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (delete_id,))
        assert cur.fetchone()['count'] == 1 #1 TRACK LINE

        # Act: End track
        cur.execute("CALL gps.delete_track(%s);", (delete_id,))

        # Assert: Everything with that id should be gone
        cur.execute("SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (delete_id,))
        assert cur.fetchone()['count'] == 0
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (delete_id,))
        assert cur.fetchone()['count'] == 0
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (delete_id,))
        assert cur.fetchone()['count'] == 0

        # Assert: Everything with old id should be there still
        cur.execute("SELECT count(*) FROM gps.tracks WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1
        cur.execute("SELECT count(*) FROM gps.track_points WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 4
        cur.execute("SELECT count(*) FROM gps.track_lines WHERE track_id = %s;", (track_id,))
        assert cur.fetchone()['count'] == 1

def test_view_all_tracks(db_conn, sample_track_points):
    """Verify we can retrieve all tracks via the view function."""
    with db_conn.cursor() as cur:
        # Create two separate tracks
        for _ in range(4):
            cur.execute("SELECT gps.create_track() as id;")
            tid = cur.fetchone()['id']
            # Add 2 points to each to ensure a line is generated
            for pt in sample_track_points[:2]:
                cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                            (tid, pt['timestamp'], pt['lat'], pt['lon'], 0, 0))
            cur.execute("CALL gps.end_track();")

        # Act: Fetch all
        cur.execute("SELECT * FROM gps.view_all_tracks();")
        results = cur.fetchall()

        # Assert
        assert len(results) >= 4
        for row in results:
            assert row['geom'] is not None
            assert row['start_time'] is not None

def test_prevent_multiple_active_tracks(db_conn):
    """Verify that create_track doesn't create a new record if one is already active."""
    with db_conn.cursor() as cur:
        # Create first track
        cur.execute("SELECT gps.create_track() as id;")
        id1 = cur.fetchone()['id']

        # Try to create another without ending the first
        cur.execute("SELECT gps.create_track() as id;")
        id2 = cur.fetchone()['id']

        # Assert: They should be the same ID
        assert id1 == id2
        
        # Verify only one row exists in the table
        cur.execute("SELECT count(*) as total FROM gps.tracks WHERE end_time IS NULL;")
        assert cur.fetchone()['total'] == 1

def test_latest_point_empty_db(db_conn):
    """Verify the function returns nothing gracefully when no points exist."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM gps.get_latest_track_point();")
        result = cur.fetchone()
        assert result is None


def test_retrieve_track_not_found(db_conn):
    """Verify that retrieving a non-existent track returns an empty result set."""
    with db_conn.cursor() as cur:
        # Use an ID that definitely doesn't exist
        cur.execute("SELECT * FROM gps.retrieve_track(999999);")
        result = cur.fetchone()
        
        assert result is None


def test_retrieve_tracks(db_conn, sample_track_points):
    """Verify we can retrieve all tracks via the view function."""
    with db_conn.cursor() as cur:
        # Create two separate tracks
        list = []
        cur.execute("SELECT * FROM gps.retrieve_track(999999);")
        result = cur.fetchone()
        
        assert result is None
        for _ in range(4):
            cur.execute("SELECT gps.create_track() as id;")
            tid = cur.fetchone()['id']
            list.append(tid)
            # Add 2 points to each to ensure a line is generated
            for pt in sample_track_points[:2]:
                cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                            (tid, pt['timestamp'], pt['lat'], pt['lon'], 0, 0))
            cur.execute("CALL gps.end_track();")
        
        cur.execute("SELECT * FROM gps.retrieve_track(%s);", (list[0],))
        result = cur.fetchone()
        assert len(result) == 4
        assert result['geom'] is not None
        assert result['track_id'] == list[0]


def test_import_track(db_conn):
    """Verify that import_track creates a track that is already 'closed'."""
    with db_conn.cursor() as cur:
        # Act: Call the import function
        cur.execute("SELECT gps.import_track() as id;")
        track_id = cur.fetchone()['id']
        
        # Assert: Check that it exists and end_time is NOT NULL
        cur.execute("SELECT start_time, end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        result = cur.fetchone()
        
        assert result is not None
        assert result['start_time'] is not None
        assert result['end_time'] is not None  # Unlike create_track(), this should be filled
        assert result['start_time'] == result['end_time']


def test_import_with_existing_tracks(db_conn, sample_track_points):
    """Verify we can retrieve all tracks via the view function."""
    with db_conn.cursor() as cur:
        for _ in range(4):
            cur.execute("SELECT gps.create_track() as id;")
            tid = cur.fetchone()['id']
            # Add 2 points to each to ensure a line is generated
            for pt in sample_track_points[:2]:
                cur.execute("CALL gps.add_track_point(%s, %s, %s, %s, %s, %s);",
                            (tid, pt['timestamp'], pt['lat'], pt['lon'], 0, 0))
            cur.execute("CALL gps.end_track();")
        
        cur.execute("SELECT gps.import_track() as id;")    
        track_id = cur.fetchone()['id']
        
        # Assert: Check that it exists and end_time is NOT NULL
        cur.execute("SELECT start_time, end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        result = cur.fetchone()
        
        assert result is not None
        assert result['start_time'] is not None
        assert result['end_time'] is not None  # Unlike create_track(), this should be filled
        assert result['start_time'] == result['end_time']

        cur.execute("SELECT count(*) from gps.tracks as count;")
        assert cur.fetchone()['count'] == 5
        
def test_update_track_metadata(db_conn):
    """Verify we can manually update the start and end times of a track."""
    with db_conn.cursor() as cur:
        # 1. Setup: Create a standard track
        cur.execute("SELECT gps.create_track() as id;")
        track_id = cur.fetchone()['id']
        
        # 2. Define new custom timestamps
        new_start = "2026-01-01 08:00:00+00"
        new_end = "2026-01-01 09:00:00+00"
        
        # 3. Act: Update the track
        cur.execute("CALL gps.update_track(%s, %s, %s);", (track_id, new_start, new_end))
        
        # 4. Assert: Verify the changes stuck
        cur.execute("SELECT start_time, end_time FROM gps.tracks WHERE track_id = %s;", (track_id,))
        updated = cur.fetchone()
        
        # We compare as strings or datetime objects depending on your driver settings
        assert str(updated['start_time']).startswith("2026-01-01 08:00:00")
        assert str(updated['end_time']).startswith("2026-01-01 09:00:00")