import pytest
from datetime import datetime
from backend.database import get_connection

def test_get_latest_version(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("select * from gps.get_latest_version();")
        result = cur.fetchone()

        assert result["version_number"] == "1.0.0"

def test_create_new_version(db_conn):
    with db_conn.cursor() as cur:
        new_version = "2.0.0"
        git_hash = "abc123"
        release_date = datetime.now()

        cur.execute("call gps.create_new_version(%s, %s, %s);", new_version, git_hash, release_date)
        result = cur.fetchone()

        assert result["version_number"] == new_version
        assert result["git_hash"] == git_hash
        assert result["release_date"] == release_date

def test_get_version_history(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("select * from gps.get_version_history()")
        result = cur.fetchall()

        assert len(result) > 0 # There should always be at least one row from this call.