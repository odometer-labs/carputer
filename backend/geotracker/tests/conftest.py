import pytest
import os

from backend.database import get_connection


@pytest.fixture(scope="function")
def db_conn():
    """Provides a psycopg connection that rolls back after every test."""
    conn = get_connection()

    yield conn

    conn.rollback()
    conn.close()


@pytest.fixture
def sample_track_points():
    """Standardized GPS data for testing."""
    return [
        {"lat": 37.7749, "lon": -122.4194, "timestamp": "2024-01-01 10:00:00+00"},
        {"lat": 37.7750, "lon": -122.4195, "timestamp": "2024-01-01 10:00:05+00"},
        {"lat": 37.7751, "lon": -122.4195, "timestamp": "2024-01-01 10:00:010+00"},
        {"lat": 37.7752, "lon": -122.4195, "timestamp": "2024-01-01 10:00:15+00"},
    ]
