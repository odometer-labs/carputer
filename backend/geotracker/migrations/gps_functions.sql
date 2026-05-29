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
    track_id BIGSERIAL NOT NULL REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
    time_stamp TIMESTAMPTZ,
    geom GEOGRAPHY(Point, 4326) NOT NULL,
    -- WGS84 Standard
    speed_mps DOUBLE PRECISION,
    -- Units: meters per second
    heading_deg DOUBLE PRECISION -- Units: 0-360 Degrees (0 = North)
);
CREATE TABLE gps.track_lines (
    track_id BIGSERIAL PRIMARY KEY REFERENCES gps.tracks(track_id) ON DELETE CASCADE,
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
-- Create track function that auto generates a name when no name is passed in
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
-- Create track function that is passed in a name
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
-- Add track point without track id
CREATE OR REPLACE PROCEDURE gps.add_track_point(
        p_time_stamp TIMESTAMPTZ,
        p_latitude DOUBLE PRECISION,
        p_longitude DOUBLE PRECISION,
        p_speed_mps DOUBLE PRECISION,
        p_heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$
DECLARE p_track_id BIGINT;
BEGIN
SELECT track_id INTO p_track_id
FROM gps.tracks
WHERE end_time is NULL;
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
-- Add track point with track id
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
-- Marks the current active track as finished and creates the track line
-- or deletes the track if no points
CREATE OR REPLACE PROCEDURE gps.end_track() LANGUAGE plpgsql AS $$
DECLARE end_track_id BIGINT;
BEGIN --  Find the currently active track
SELECT track_id INTO end_track_id
FROM gps.tracks
WHERE end_time IS NULL
LIMIT 1;
-- If an active track is found, proceed
IF end_track_id IS NOT NULL THEN IF EXISTS (
    SELECT 1 -- Only generate a line if the track actually has recorded points
    FROM gps.track_points
    WHERE track_id = end_track_id
) THEN
INSERT INTO gps.track_lines (track_id, geom, geom_wm)
SELECT end_track_id,
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
WHERE track_id = end_track_id;
UPDATE gps.tracks
SET end_time = NOW()
WHERE track_id = end_track_id;
ELSE
DELETE FROM gps.tracks
WHERE track_id = end_track_id;
END IF;
END IF;
END;
$$;
-- Gets tracks vector tile based on mode -- all, single, nearby, road
CREATE OR REPLACE FUNCTION gps.get_tracks_mvt(
        -- z, x, y: address that builds the bounding box (tile envelope) for the vector tiles
        z INTEGER,
        x INTEGER,
        y INTEGER,
        mode TEXT DEFAULT 'all',
        -- only needed for retrieval of a single track
        p_track_id BIGINT DEFAULT NULL,
        -- only needed for retrieval of nearby tracks within a certain amount of meters
        p_within_meters DOUBLE PRECISION DEFAULT NULL
    ) RETURNS bytea LANGUAGE plpgsql AS $$
DECLARE mvt bytea;
latest_track_id BIGINT;
latest_geom GEOGRAPHY;
current_track_id BIGINT;
current_track_line_wm GEOMETRY;
road_search_zone_wm GEOMETRY;
tile_env GEOMETRY;
BEGIN tile_env := ST_TileEnvelope(z, x, y);
--------------------------------------------------
-- Nearby only: fetch latest point
--------------------------------------------------
IF mode = 'nearby' THEN
SELECT geom,
    track_id INTO latest_geom,
    latest_track_id
FROM gps.get_latest_track_point()
ORDER BY time_stamp DESC
LIMIT 1;
END IF;
--------------------------------------------------
-- Road only: fetch active track
--------------------------------------------------
IF mode = 'road' THEN -- 1. Find the ID of the single active track
SELECT t.track_id INTO current_track_id
FROM gps.tracks t
WHERE t.end_time IS NULL
ORDER BY t.start_time DESC
LIMIT 1;
IF current_track_id IS NOT NULL THEN
SELECT ST_MakeLine(
        ST_Transform(p.geom::geometry, 3857)
        ORDER BY p.time_stamp
    ) INTO current_track_line_wm
FROM gps.track_points p
WHERE p.track_id = current_track_id;
-- 3. Create the 30-meter search zone around it
IF current_track_line_wm IS NOT NULL THEN road_search_zone_wm := ST_Buffer(current_track_line_wm, 30);
END IF;
END IF;
END IF;
--------------------------------------------------
-- Main Query 
--------------------------------------------------
SELECT ST_AsMVT(tile, 'tracks_layer') INTO mvt
FROM (
        SELECT t.track_id,
            t.start_time,
            t.end_time,
            t.track_name,
            ST_AsMVTGeom(
                tl.geom_wm,
                tile_env,
                4096,
                -- 4096 x 4096 units (grid resolution)
                256,
                -- buffer (~6% more space)
                true
            ) AS geom
        FROM gps.tracks t
            JOIN gps.track_lines tl ON t.track_id = tl.track_id
        WHERE tl.geom_wm && tile_env
            AND (
                ------------------------------------------------------
                -- ALL MODE -- get all tracks in current tile envelope
                ------------------------------------------------------
                mode = 'all' -----------------------------------------
                -- SINGLE -- retrieve track based on p_track_id 
                --          AND in current tile envelope
                ------------------------------------------------------
                OR (
                    mode = 'single'
                    AND p_track_id IS NOT NULL
                    AND t.track_id = p_track_id
                ) ------------------------------------------------------
                -- NEARBY -- retrieves all tracks within p_within_meters
                --            AND in current tile envelope 
                --------------------------------------------------------
                OR (
                    mode = 'nearby'
                    AND p_within_meters IS NOT NULL
                    AND latest_track_id IS NOT NULL
                    AND latest_geom IS NOT NULL
                    AND t.track_id <> latest_track_id
                    AND ST_DWithin(
                        tl.geom,
                        latest_geom,
                        p_within_meters
                    )
                ) -------------------------------------------------------------
                -- ROAD -- retrieves all tracks that overlap with current track
                --         AND in tile envelope
                ---------------------------------------------------------------
                OR (
                    mode = 'road'
                    AND current_track_id IS NOT NULL
                    AND road_search_zone_wm IS NOT NULL
                    AND t.track_id <> current_track_id
                    AND t.end_time IS NOT NULL
                    AND ST_Intersects(tl.geom_wm, road_search_zone_wm)
                )
            )
    ) AS tile;
--------------------------------------------------
-- Normalize empty tile becomes NULL
--------------------------------------------------
IF mvt IS NULL
OR length(mvt) = 0 THEN RETURN NULL;
END IF;
RETURN mvt;
END;
$$;
-- Fetches a single track as a spatial LineString
CREATE OR REPLACE FUNCTION gps.retrieve_track(retrieve_track_id INTEGER) RETURNS TABLE (
        track_id BIGINT,
        geom JSONB,
        geom_wm JSONB,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ,
        track_name VARCHAR(50)
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
    ST_AsGEOJSON(tl.geom_wm, 6)::jsonb,
    t.start_time,
    t.end_time,
    t.track_name
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
        end_time TIMESTAMPTZ,
        track_name VARCHAR(50)
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
    t.start_time,
    t.end_time,
    t.track_name
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
        geom_wm GEOMETRY(Point, 3857),
        speed_mps DOUBLE PRECISION,
        heading_deg DOUBLE PRECISION
    ) LANGUAGE plpgsql AS $$ #variable_conflict use_column BEGIN RETURN QUERY
SELECT point_id,
    track_id,
    time_stamp,
    geom,
    ST_Transform(geom::geometry, 3857) AS geom_wm,
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
        end_time TIMESTAMPTZ,
        track_name VARCHAR(50)
    ) LANGUAGE plpgsql AS $$ BEGIN RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
    t.start_time,
    t.end_time,
    t.track_name
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
        end_time TIMESTAMPTZ,
        track_name VARCHAR(50)
    ) LANGUAGE plpgsql AS $$
DECLARE current_track_id BIGINT;
current_track_line_wm GEOMETRY;
road_search_zone_wm GEOMETRY;
BEGIN
SELECT t.track_id INTO current_track_id
FROM gps.tracks AS t
WHERE t.end_time IS NULL
ORDER BY t.start_time DESC
LIMIT 1;
IF current_track_id IS NULL THEN RETURN;
END IF;
SELECT ST_MakeLine(
        ST_Transform(p.geom::geometry, 3857)
        ORDER BY p.time_stamp
    ) INTO current_track_line_wm
FROM gps.track_points p
WHERE p.track_id = current_track_id;
IF current_track_line_wm IS NOT NULL THEN road_search_zone_wm := ST_Buffer(current_track_line_wm, 30);
END IF;
RETURN QUERY
SELECT t.track_id,
    ST_AsGeoJSON(tl.geom, 6)::jsonb,
    t.start_time,
    t.end_time,
    t.track_name
FROM gps.tracks AS t
    INNER JOIN gps.track_lines AS tl ON t.track_id = tl.track_id
WHERE t.track_id <> current_track_id
    AND t.end_time IS NOT NULL
    AND road_search_zone_wm IS NOT NULL
    AND ST_Intersects(tl.geom_wm, road_search_zone_wm);
END;
$$;
-- Utility for batch-importing external data sets as completed tracks
CREATE OR REPLACE FUNCTION gps.import_track(geojson_data TEXT) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE new_track_id INTEGER;
new_geom GEOMETRY;
BEGIN
INSERT INTO gps.tracks(start_time, end_time)
VALUES (NOW(), NOW())
RETURNING track_id INTO new_track_id;
SELECT ST_SetSRID(ST_GeomFromGeoJSON(geojson_data), 4326) INTO new_geom;
INSERT INTO gps.track_lines(track_id, geom, geom_wm)
VALUES (
        new_track_id,
        new_geom,
        ST_Transform(new_geom, 3857)
    );
RETURN new_track_id;
END;
$$;
CREATE OR REPLACE FUNCTION gps.import_gpx(new_track_name TEXT) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE new_track_id INTEGER;
BEGIN
INSERT INTO gps.tracks(start_time, end_time, track_name)
VALUES (NOW(), NOW(), new_track_name)
RETURNING track_id INTO new_track_id;
RETURN new_track_id;
END;
$$;
CREATE OR REPLACE PROCEDURE gps.end_gpx_track(end_track_id INTEGER) LANGUAGE plpgsql AS $$ BEGIN
INSERT INTO gps.track_lines (track_id, geom, geom_wm)
SELECT end_track_id,
    ST_MakeLine(
        geom::geometry
        ORDER BY point_id ASC
    )::geography,
    ST_Transform(
        ST_MakeLine(
            geom::geometry
            ORDER BY point_id ASC
        ),
        3857
    )
FROM gps.track_points
WHERE track_id = end_track_id;
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