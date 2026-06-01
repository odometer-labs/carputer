import pytest
from backend.database import get_connection


def test_create_travel_history(db_conn):
    """Verify create_travel_history inserts one row with the provided bounds."""
    with db_conn.cursor() as cur:
        cur.execute(
            "CALL gps.create_travel_history(%s, %s, %s, %s, %s);",
            (-122.7, -122.6, 45.5, 45.6, 1),
        )
        cur.execute("SELECT count(*) FROM gps.travel_history WHERE track_id = 1;")
        assert cur.fetchone()["count"] == 1


def test_list_travel_history_empty(db_conn):
    """Verify list_travel_history returns no rows on an empty table."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM gps.list_travel_history();")
        results = cur.fetchall()
        assert len(results) == 0


def test_list_travel_history_ordered_desc(db_conn):
    """Verify list_travel_history returns rows in descending id order."""
    with db_conn.cursor() as cur:
        entries = [
            (-122.7, -122.6, 45.5, 45.6, 10),
            (-123.0, -122.9, 45.4, 45.5, 11),
            (-121.5, -121.4, 45.8, 45.9, 12),
        ]
        for e in entries:
            cur.execute(
                "CALL gps.create_travel_history(%s, %s, %s, %s, %s);", e
            )

        cur.execute("SELECT * FROM gps.list_travel_history();")
        rows = cur.fetchall()
        assert len(rows) == 3

        # ids should be strictly descending
        ids = [row["id"] for row in rows]
        assert ids == sorted(ids, reverse=True)


def test_travel_history_fields_roundtrip(db_conn):
    """Verify all columns are stored and returned correctly."""
    with db_conn.cursor() as cur:
        cur.execute(
            "CALL gps.create_travel_history(%s, %s, %s, %s, %s);",
            (-122.71, -122.61, 45.51, 45.61, 42),
        )
        cur.execute("SELECT * FROM gps.list_travel_history();")
        row = cur.fetchone()

        assert row["min_x"] == pytest.approx(-122.71)
        assert row["max_x"] == pytest.approx(-122.61)
        assert row["min_y"] == pytest.approx(45.51)
        assert row["max_y"] == pytest.approx(45.61)
        assert row["track_id"] == 42
        assert row["created_at"] is not None
        assert row["id"] > 0


def test_create_travel_history_multiple_entries_same_track(db_conn):
    """Multiple entries can share the same track_id (no unique constraint)."""
    with db_conn.cursor() as cur:
        for _ in range(3):
            cur.execute(
                "CALL gps.create_travel_history(%s, %s, %s, %s, %s);",
                (-122.7, -122.6, 45.5, 45.6, 99),
            )
        cur.execute(
            "SELECT count(*) FROM gps.travel_history WHERE track_id = 99;"
        )
        assert cur.fetchone()["count"] == 3
