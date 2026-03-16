-- gps_functions.sql
---------------------------
-- 1. EXTENSIONS & SCHEMA
---------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SCHEMA IF NOT EXISTS gps;
---------------------------
-- 2. TABLES
---------------------------
CREATE TABLE gps.tracks (
    track_id BIGSERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ
);
CREATE TABLE gps.track_points (
    point_id BIGSERIAL PRIMARY KEY,
    track_id BIGINT NOT NULL REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
    time_stamp TIMESTAMPTZ NOT NULL,
    geom GEOGRAPHY(Point, 4326) NOT NULL,
    -- WGS84 Standard
    speed_mph DOUBLE PRECISION,
    -- Units: Miles per Hour
    heading_deg DOUBLE PRECISION -- Units: 0-360 Degrees (0 = North)
);
CREATE TABLE gps.track_lines (
    track_id BIGINT PRIMARY KEY REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
    geom GEOGRAPHY(LINESTRING, 4326) NOT NULL
);
---------------------------
-- 3. INDEXES & CONSTRAINTS
---------------------------
-- Ensures only one recording session is active at a time per database instance
CREATE UNIQUE INDEX one_active_track ON gps.tracks ((end_time IS NULL))
WHERE end_time IS NULL;
-- Spatial GIST indexes for fast proximity searches (ST_DWithin, ST_Distance)
CREATE INDEX IF NOT EXISTS idx_track_points_geom ON gps.track_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_track_points_track_time ON gps.track_points(track_id, time_stamp);
CREATE INDEX IF NOT EXISTS idx_track_points_geom_track ON gps.track_points USING GIST(geom, track_id);
CREATE INDEX IF NOT EXISTS idx_track_points_timestamp ON gps.track_points(time_stamp DESC);
CREATE INDEX IF NOT EXISTS idx_track_lines_geom ON gps.track_lines USING GIST (geom);
---------------------------
-- 4. CRUD OPERATIONS
---------------------------
-- Handles logic to either start a new track or return the currently active one
CREATE OR REPLACE FUNCTION gps.create_track() RETURNS BIGINT LANGUAGE plpgsql AS $$
DECLARE new_track_id BIGINT;
BEGIN
SELECT track_id INTO new_track_id
FROM gps.tracks
WHERE end_time IS NULL
LIMIT 1;
IF new_track_id IS NOT NULL THEN RETURN new_track_id;
END IF;
INSERT INTO gps.tracks(start_time)
VALUES (NOW())
RETURNING track_id INTO new_track_id;
RETURN new_track_id;
END;
$$;
--- Standard entry point for raw GPS telemetry
-- Units: Lat/Long (Decimal), Speed (MPH), Heading (0-360 deg)
CREATE OR REPLACE PROCEDURE gps.add_track_point(
        p_track_id BIGINT,
        p_time_stamp TIMESTAMPTZ,
        p_latitude DOUBLE PRECISION,
        p_longitude DOUBLE PRECISION,
        p_speed_mph DOUBLE PRECISION,
        p_heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$ BEGIN
INSERT INTO gps.track_points (
        track_id,
        time_stamp,
        geom,
        speed_mph,
        heading_deg
    )
VALUES (
        p_track_id,
        p_time_stamp,
        ST_Point(p_longitude, p_latitude, 4326)::GEOGRAPHY,
        p_speed_mph,
        p_heading_deg
    );
END;
$$;
-- Marks the current active track as finished
CREATE OR REPLACE PROCEDURE gps.end_track() LANGUAGE plpgsql AS $$ BEGIN
UPDATE gps.tracks
SET end_time = NOW()
WHERE end_time IS NULL;
END;
$$;
-- Fetches a single track as a spatial LineString
CREATE OR REPLACE FUNCTION gps.retrieve_track(retrieve_track_id INTEGER) RETURNS TABLE (
        track_id BIGINT,
        geom GEOGRAPHY(LINESTRING, 4326),
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    tl.geom,
    t.start_time,
    t.end_time
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id
WHERE retrieve_track_id = t.track_id;
END;
$$;
-- Fetches all completed and active tracks for map visualization
CREATE OR REPLACE FUNCTION gps.view_all_tracks() RETURNS TABLE (
        track_id BIGINT,
        geom GEOGRAPHY(LINESTRING, 4326),
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    tl.geom,
    t.start_time,
    t.end_time
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id;
END;
$$;
-- Allows manual correction of track start/end timestamps
CREATE OR REPLACE PROCEDURE gps.update_track(
        update_track_id BIGINT,
        p_start_time TIMESTAMPTZ,
        p_end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN
UPDATE gps.tracks
SET start_time = p_start_time,
    end_time = p_end_time
WHERE track_id = update_track_id;
END;
$$;
-- Cascading delete: removing a track removes all associated points and lines
CREATE OR REPLACE PROCEDURE gps.delete_track(p_track_id BIGINT) LANGUAGE plpgsql AS $$ BEGIN IF EXISTS (
        SELECT 1
        FROM gps.tracks
        WHERE track_id = p_track_id
    ) THEN
DELETE FROM gps.tracks
WHERE track_id = p_track_id;
END IF;
END;
$$;
---------------------------
-- 5. SPATIAL LOGIC & UTILITIES
---------------------------
-- Helper to find the most recent telemetry point for real-time tracking
CREATE OR REPLACE FUNCTION gps.get_latest_track_point() RETURNS TABLE (
        point_id BIGINT,
        track_id BIGINT,
        time_stamp TIMESTAMPTZ,
        geom GEOGRAPHY(Point, 4326),
        speed_mph DOUBLE PRECISION,
        heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT point_id,
    track_id,
    time_stamp,
    geom,
    speed_mph,
    heading_deg
FROM gps.track_points
ORDER BY time_stamp DESC
LIMIT 1;
END;
$$;
-- 30-meter proximity check to determine if the user is exploring new territory
CREATE OR REPLACE FUNCTION gps.is_new_road() RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE latest_geom GEOGRAPHY(Point, 4326);
latest_track_id BIGINT;
nearest_distance DOUBLE PRECISION;
BEGIN
SELECT geom,
    track_id INTO latest_geom,
    latest_track_id
FROM gps.get_latest_track_point();
SELECT ST_Distance(latest_geom, tl.geom) INTO nearest_distance
FROM gps.track_lines AS tl
WHERE tl.track_id <> latest_track_id
    AND ST_DWithin(latest_geom, tl.geom, 500)
ORDER BY latest_geom <->tl.geom
LIMIT 1;
IF nearest_distance IS NULL THEN RETURN TRUE;
END IF;
RETURN nearest_distance > 30;
END;
$$;
-- Proximity search: returns historical tracks that pass through the current area
CREATE OR REPLACE FUNCTION gps.get_track_lines_near_location(p_within_meters DOUBLE PRECISION) RETURNS TABLE (
        track_id BIGINT,
        geom GEOGRAPHY(LINESTRING, 4326),
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    tl.geom,
    t.start_time,
    t.end_time
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id
    CROSS JOIN gps.get_latest_track_point() AS p
WHERE t.track_id <> p.track_id
    AND ST_DWithin(tl.geom, p.geom, p_within_meters);
END;
$$;
-- Identifies historical tracks that overlap with the current active recording
CREATE OR REPLACE FUNCTION gps.get_track_lines_using_road() RETURNS TABLE (
        track_id BIGINT,
        geom GEOGRAPHY(LINESTRING, 4326),
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$
DECLARE current_track_id BIGINT;
current_track_geom GEOGRAPHY;
BEGIN
SELECT t.track_id,
    tl.geom INTO current_track_id,
    current_track_geom
FROM gps.tracks AS t
    JOIN gps.track_lines AS tl ON t.track_id = tl.track_id
WHERE t.end_time IS NULL
ORDER BY t.start_time DESC
LIMIT 1;
IF current_track_id IS NULL THEN RETURN;
END IF;
RETURN QUERY
SELECT t.track_id,
    tl.geom,
    t.start_time,
    t.end_time
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id
WHERE t.track_id <> current_track_id
    AND t.end_time IS NOT NULL
    AND ST_DWithin(tl.geom, current_track_geom, 30);
END;
$$;
-- Utility for batch-importing external data sets as completed tracks
CREATE OR REPLACE FUNCTION gps.import_track() RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE new_track_id INTEGER;
BEGIN
INSERT INTO gps.tracks(start_time, end_time)
VALUES (NOW(), NOW())
RETURNING track_id INTO new_track_id;
RETURN new_track_id;
END;
$$;
-- Fixes common GPS topology errors (self-intersections) to ensure spatial validity
CREATE OR REPLACE PROCEDURE gps.validate_geometry(finished_track_id BIGINT) LANGUAGE plpgsql AS $$ BEGIN
UPDATE gps.track_lines
SET geom = ST_LineMerge(ST_MakeValid(geom::GEOMETRY))::GEOGRAPHY
WHERE track_id = finished_track_id
    AND NOT ST_IsValid(geom::GEOMETRY);
END;
$$;
---------------------------
-- 6. TRIGGER SYSTEM
---------------------------
-- Automation: Dynamically builds LineStrings as points are inserted. 
-- Avoids expensive recalculations of the entire track during read operations.\
CREATE OR REPLACE FUNCTION gps.update_track_line_trigger() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE point_count INTEGER;
line_exists BOOLEAN;
BEGIN
SELECT EXISTS(
        SELECT 1
        FROM gps.track_lines
        WHERE track_id = NEW.track_id
    ) INTO line_exists;
IF line_exists THEN
UPDATE gps.track_lines
SET geom = ST_AddPoint(geom::GEOMETRY, NEW.geom::GEOMETRY, -1)::GEOGRAPHY
WHERE track_id = NEW.track_id;
-- Line is created if there are at least two track points.
ELSE
INSERT INTO gps.track_lines (track_id, geom)
SELECT NEW.track_id,
    ST_MakeLine(
        geom::geometry
        ORDER BY time_stamp ASC
    )::geography
FROM gps.track_points
WHERE track_id = NEW.track_id
HAVING COUNT(*) >= 2 ON CONFLICT (track_id) DO NOTHING;
END IF;
RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_update_track_line ON gps.track_points;
CREATE TRIGGER trg_update_track_line
AFTER
INSERT ON gps.track_points FOR EACH ROW EXECUTE FUNCTION gps.update_track_line_trigger();