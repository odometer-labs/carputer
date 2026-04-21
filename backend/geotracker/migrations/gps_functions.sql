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
    end_time TIMESTAMPTZ,
    track_name VARCHAR(50)
);
CREATE TABLE gps.track_points (
    point_id BIGSERIAL PRIMARY KEY,
    track_id BIGINT NOT NULL REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
    time_stamp TIMESTAMPTZ NOT NULL,
    geom GEOGRAPHY(Point, 4326) NOT NULL,
    -- WGS84 Standard
    speed_mps DOUBLE PRECISION,
    -- Units: Miles per Hour
    heading_deg DOUBLE PRECISION -- Units: 0-360 Degrees (0 = North)
);
CREATE TABLE gps.track_lines (
    track_id BIGINT PRIMARY KEY REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
    geom GEOGRAPHY(LINESTRING, 4326) NOT NULL,
    geom_wm GEOMETRY(LINESTRING, 3857) -- For Vector Tiles (Web Mercator)
);
---------------------------
-- 3. INDEXES & CONSTRAINTS
---------------------------
-- Ensures only one recording session is active at a time per database instance
CREATE UNIQUE INDEX one_active_track ON gps.tracks ((end_time IS NULL))
WHERE end_time IS NULL;
-- Spatial GIST indexes for fast proximity searches (ST_DWithin, ST_Distance)
CREATE INDEX IF NOT EXISTS idx_track_points_geom ON gps.track_points USING GIST (geom);
CREATE INDEX idx_track_lines_wm ON gps.track_lines USING GIST (geom_wm);
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
generated_name VARCHAR(50);
BEGIN
SELECT track_id INTO new_track_id
FROM gps.tracks
WHERE end_time IS NULL
LIMIT 1;
IF new_track_id IS NOT NULL THEN RETURN new_track_id;
END IF;
generated_name := 'Track ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI');
INSERT INTO gps.tracks(start_time, track_name)
VALUES (NOW(), generated_name)
RETURNING track_id INTO new_track_id;
RETURN new_track_id;
END;
$$;
CREATE OR REPLACE FUNCTION gps.create_track(p_track_name VARCHAR(50)) RETURNS BIGINT LANGUAGE plpgsql AS $$
DECLARE new_track_id BIGINT;
BEGIN
SELECT track_id INTO new_track_id
FROM gps.tracks
WHERE end_time IS NULL
LIMIT 1;
IF new_track_id IS NOT NULL THEN RETURN new_track_id;
END IF;
INSERT INTO gps.tracks(start_time, track_name)
VALUES (NOW(), p_track_name)
RETURNING track_id INTO new_track_id;
RETURN new_track_id;
END;
$$;
--- Standard entry point for raw GPS telemetry
-- Units: Lat/Long (Decimal), Speed (m/s), Heading (0-360 deg)
CREATE OR REPLACE PROCEDURE gps.add_track_point(
        p_track_id BIGINT,
        p_time_stamp TIMESTAMPTZ,
        p_latitude DOUBLE PRECISION,
        p_longitude DOUBLE PRECISION,
        p_speed_mps DOUBLE PRECISION,
        p_heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$ BEGIN
INSERT INTO gps.track_points (
        track_id,
        time_stamp,
        geom,
        speed_mps,
        heading_deg
    )
VALUES (
        p_track_id,
        p_time_stamp,
        ST_Point(p_longitude, p_latitude, 4326)::GEOGRAPHY,
        p_speed_mps,
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
        geom JSONB,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
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
        geom JSONB,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
    t.start_time,
    t.end_time
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id;
END;
$$;
-- Allows manual correction of track metadata
CREATE OR REPLACE PROCEDURE gps.update_track(
        update_track_id BIGINT,
        p_start_time TIMESTAMPTZ,
        p_end_time TIMESTAMPTZ,
        p_track_name VARCHAR(50)
    ) LANGUAGE plpgsql AS $$ BEGIN
UPDATE gps.tracks
SET start_time = p_start_time,
    end_time = p_end_time,
    track_name = p_track_name
WHERE track_id = update_track_id;
END;
$$;
CREATE OR REPLACE FUNCTION gps.view_all_tracks_mvt(z integer, x integer, y integer) RETURNS bytea LANGUAGE plpgsql AS $$
DECLARE mvt bytea;
BEGIN --ST_AsMVT to aggregate all rows into a single binary tile
SELECT ST_AsMVT(tile, 'tracks_layer') INTO mvt
FROM (
        SELECT t.track_id,
            t.start_time,
            t.end_time,
            t.track_name,
            -- Convert the geometry into the local coordinate system of the tile
            ST_AsMVTGeom(
                tl.geom_wm,
                -- Web Mercator geometry
                ST_TileEnvelope(z, x, y),
                -- The bounding box of the requested tile
                4096,
                256,
                true -- Extent, Buffer, Clip
            ) AS geom
        FROM gps.tracks AS t
            INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id -- Only process tracks that are actually inside this tile's area
        WHERE tl.geom_wm && ST_TileEnvelope(z, x, y)
    ) AS tile;
RETURN mvt;
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
CREATE OR REPLACE FUNCTION gps.get_track_tiles(z integer, x integer, y integer) RETURNS bytea LANGUAGE plpgsql AS $$
DECLARE mvt bytea;
BEGIN --  binary MVT format
SELECT ST_AsMVT(tile, 'tracks_layer', 4096, 'geom') INTO mvt
FROM (
        SELECT track_id,
            -- Condition the geometry (Clip, Simplify, Quantize)
            ST_AsMVTGeom(
                ST_Simplify(geom_wm, ST_LevelScale(z)),
                ST_TileEnvelope(z, x, y),
                4096,
                64,
                true -- Extent, Buffer, Clip
            ) AS geom
        FROM gps.track_lines -- filter using the Envelope to find lines in this tile
        WHERE geom_wm && ST_TileEnvelope(z, x, y)
    ) AS tile;
RETURN mvt;
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
        speed_mps DOUBLE PRECISION,
        heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$ #variable_conflict use_column BEGIN RETURN QUERY
SELECT point_id,
    track_id,
    time_stamp,
    geom,
    speed_mps,
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
        geom JSONB,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
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
        geom JSONB,
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
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
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
CREATE OR REPLACE FUNCTION gps.import_track(geojson_data TEXT) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE new_track_id INTEGER;
BEGIN
INSERT INTO gps.tracks(start_time, end_time)
VALUES (NOW(), NOW())
RETURNING track_id INTO new_track_id;
INSERT INTO gps.track_lines(track_id, geom)
VALUES (
        new_track_id,
        ST_SetSRID(ST_GeomFromGeoJSON(geojson_data), 4326)
    );
RETURN new_track_id;
END;
$$;
-- Fixes common GPS topology errors (self-intersections) to ensure spatial validity
CREATE OR REPLACE PROCEDURE gps.validate_geometry(finished_track_id BIGINT) LANGUAGE plpgsql AS $$
DECLARE cleaned_geom geometry;
BEGIN --  Attempt to clean and extract only the line parts (type 2)
SELECT ST_CollectionExtract(ST_MakeValid(geom_wm), 2) INTO cleaned_geom
FROM gps.track_lines
WHERE track_id = finished_track_id;
-- Only update if the result is a valid, non-empty LineString/MultiLineString
IF cleaned_geom IS NOT NULL
AND NOT ST_IsEmpty(cleaned_geom) THEN
UPDATE gps.track_lines
SET geom_wm = cleaned_geom,
    geom = ST_Transform(cleaned_geom, 4326)::geography
WHERE track_id = finished_track_id;
END IF;
END;
$$;
CREATE OR REPLACE FUNCTION ST_LevelScale(z integer) RETURNS float8 LANGUAGE plpgsql AS $$ BEGIN -- 40075016.68 is the Earth's circumference in meters (EPSG:3857)
    -- 256 is the standard tile pixel width
    RETURN 40075016.68 / (256 * |/ 2 ^ z);
END;
$$;
---------------------------
-- 6. TRIGGER SYSTEM
---------------------------
-- Automation: Dynamically builds LineStrings as points are inserted. 
-- Avoids expensive recalculations of the entire track during read operations.
CREATE OR REPLACE FUNCTION gps.update_track_line_trigger() RETURNS TRIGGER LANGUAGE plpgsql AS $$ BEGIN -- Try to create the line assuming it's the 2nd point.
    -- If it's the 1st point, this query returns 0 rows and does nothing.
    -- If the line already exists, it hits the EXCLUDED conflict.
INSERT INTO gps.track_lines (track_id, geom, geom_wm)
SELECT NEW.track_id,
    ST_MakeLine(
        geom::geometry
        ORDER BY time_stamp ASC
    )::geography,
    ST_Transform(
        ST_MakeLine(
            geom::geometry
            ORDER BY time_stamp ASC
        ),
        3857
    )
FROM gps.track_points
WHERE track_id = NEW.track_id
HAVING COUNT(*) = 2 ON CONFLICT (track_id) DO
UPDATE
SET geom = ST_AddPoint(
        gps.track_lines.geom::geometry,
        NEW.geom::geometry,
        -1
    )::geography,
    geom_wm = ST_AddPoint(
        gps.track_lines.geom_wm,
        ST_Transform(NEW.geom::geometry, 3857),
        -1
    );
RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS trg_update_track_line ON gps.track_points;
CREATE TRIGGER trg_update_track_line
AFTER
INSERT ON gps.track_points FOR EACH ROW EXECUTE FUNCTION gps.update_track_line_trigger();