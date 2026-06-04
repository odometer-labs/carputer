-- aprs_tables.sql
-- APRS Station Tracking Tables and Functions
-- Run after gps_functions.sql

---------------------------
-- 1. APRS TABLES
---------------------------

-- Stores unique APRS stations (callsigns)
CREATE TABLE IF NOT EXISTS gps.aprs_stations (
    callsign VARCHAR(20) PRIMARY KEY,
    ssid VARCHAR(5),                       -- SSID suffix (e.g., -10, -15)
    symbol_table CHAR(1) DEFAULT '/',      -- APRS symbol table ('/' or '\')
    symbol_code CHAR(1) DEFAULT 'k',       -- APRS symbol code (e.g., 'k' = car)
    last_comment TEXT,                     -- Last status/comment from station
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    geom GEOGRAPHY(Point, 4326),           -- Most recent position
    packet_count INTEGER DEFAULT 1
);

-- Stores APRS position history for each station
CREATE TABLE IF NOT EXISTS gps.aprs_history (
    history_id BIGSERIAL PRIMARY KEY,
    callsign VARCHAR(20) NOT NULL REFERENCES gps.aprs_stations(callsign) ON DELETE CASCADE,
    time_stamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    geom GEOGRAPHY(Point, 4326) NOT NULL,
    altitude_m DOUBLE PRECISION,           -- Altitude in meters
    speed_knots DOUBLE PRECISION,          -- Speed in knots
    course_deg DOUBLE PRECISION,           -- Course/heading 0-360
    raw_packet TEXT,                       -- Original packet for debugging
    comment TEXT
);

-- Stores raw APRS packets for debugging/replay
CREATE TABLE IF NOT EXISTS gps.aprs_raw_packets (
    packet_id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    raw_packet TEXT NOT NULL,
    parsed_ok BOOLEAN DEFAULT FALSE,
    parse_error TEXT
);

---------------------------
-- 2. APRS INDEXES
---------------------------

CREATE INDEX IF NOT EXISTS idx_aprs_stations_geom 
    ON gps.aprs_stations USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_aprs_stations_last_seen 
    ON gps.aprs_stations(last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_aprs_history_geom 
    ON gps.aprs_history USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_aprs_history_callsign_time 
    ON gps.aprs_history(callsign, time_stamp DESC);

CREATE INDEX IF NOT EXISTS idx_aprs_history_time 
    ON gps.aprs_history(time_stamp DESC);

CREATE INDEX IF NOT EXISTS idx_aprs_raw_received 
    ON gps.aprs_raw_packets(received_at DESC);

---------------------------
-- 3. APRS FUNCTIONS
---------------------------

-- Upsert an APRS station with position
CREATE OR REPLACE FUNCTION gps.upsert_aprs_station(
    p_callsign VARCHAR(20),
    p_latitude DOUBLE PRECISION,
    p_longitude DOUBLE PRECISION,
    p_symbol_table CHAR(1) DEFAULT '/',
    p_symbol_code CHAR(1) DEFAULT 'k',
    p_comment TEXT DEFAULT NULL,
    p_altitude_m DOUBLE PRECISION DEFAULT NULL,
    p_speed_knots DOUBLE PRECISION DEFAULT NULL,
    p_course_deg DOUBLE PRECISION DEFAULT NULL,
    p_raw_packet TEXT DEFAULT NULL
) RETURNS VARCHAR(20) LANGUAGE plpgsql AS $$
DECLARE
    v_ssid VARCHAR(5);
    v_base_callsign VARCHAR(20);
BEGIN
    -- Extract SSID if present (e.g., "W1ABC-10" -> ssid = "-10")
    IF p_callsign LIKE '%-%' THEN
        v_base_callsign := split_part(p_callsign, '-', 1);
        v_ssid := '-' || split_part(p_callsign, '-', 2);
    ELSE
        v_base_callsign := p_callsign;
        v_ssid := NULL;
    END IF;

    -- Upsert station record
    INSERT INTO gps.aprs_stations (
        callsign, ssid, symbol_table, symbol_code, 
        last_comment, last_seen, geom, packet_count
    )
    VALUES (
        p_callsign, v_ssid, p_symbol_table, p_symbol_code,
        p_comment, NOW(), 
        ST_Point(p_longitude, p_latitude, 4326)::GEOGRAPHY,
        1
    )
    ON CONFLICT (callsign) DO UPDATE SET
        symbol_table = COALESCE(EXCLUDED.symbol_table, gps.aprs_stations.symbol_table),
        symbol_code = COALESCE(EXCLUDED.symbol_code, gps.aprs_stations.symbol_code),
        last_comment = COALESCE(EXCLUDED.last_comment, gps.aprs_stations.last_comment),
        last_seen = NOW(),
        geom = EXCLUDED.geom,
        packet_count = gps.aprs_stations.packet_count + 1;

    -- Add to history
    INSERT INTO gps.aprs_history (
        callsign, geom, altitude_m, speed_knots, 
        course_deg, raw_packet, comment
    )
    VALUES (
        p_callsign,
        ST_Point(p_longitude, p_latitude, 4326)::GEOGRAPHY,
        p_altitude_m, p_speed_knots, p_course_deg,
        p_raw_packet, p_comment
    );

    RETURN p_callsign;
END;
$$;

-- Get all APRS stations within N meters of current GPS position
CREATE OR REPLACE FUNCTION gps.get_aprs_stations_near(
    p_meters DOUBLE PRECISION DEFAULT 50000  -- 50km default
) RETURNS TABLE (
    callsign VARCHAR(20),
    symbol_table CHAR(1),
    symbol_code CHAR(1),
    last_comment TEXT,
    last_seen TIMESTAMPTZ,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    distance_m DOUBLE PRECISION,
    packet_count INTEGER
) LANGUAGE plpgsql AS $$
DECLARE
    v_current_pos GEOGRAPHY;
BEGIN
    -- Get most recent GPS position (exclude rows with NULL timestamps)
    SELECT tp.geom INTO v_current_pos
    FROM gps.track_points tp
    WHERE tp.time_stamp IS NOT NULL
    ORDER BY tp.time_stamp DESC
    LIMIT 1;

    IF v_current_pos IS NULL THEN
        -- No GPS fix, return all recent stations
        RETURN QUERY
        SELECT 
            s.callsign,
            s.symbol_table,
            s.symbol_code,
            s.last_comment,
            s.last_seen,
            ST_Y(s.geom::GEOMETRY) AS latitude,
            ST_X(s.geom::GEOMETRY) AS longitude,
            NULL::DOUBLE PRECISION AS distance_m,
            s.packet_count
        FROM gps.aprs_stations s
        WHERE s.last_seen > NOW() - INTERVAL '24 hours'
        ORDER BY s.last_seen DESC
        LIMIT 100;
    ELSE
        RETURN QUERY
        SELECT 
            s.callsign,
            s.symbol_table,
            s.symbol_code,
            s.last_comment,
            s.last_seen,
            ST_Y(s.geom::GEOMETRY) AS latitude,
            ST_X(s.geom::GEOMETRY) AS longitude,
            ST_Distance(s.geom, v_current_pos) AS distance_m,
            s.packet_count
        FROM gps.aprs_stations s
        WHERE ST_DWithin(s.geom, v_current_pos, p_meters)
          AND s.last_seen > NOW() - INTERVAL '24 hours'
        ORDER BY ST_Distance(s.geom, v_current_pos)
        LIMIT 100;
    END IF;
END;
$$;

-- Get position history for a specific station
CREATE OR REPLACE FUNCTION gps.get_aprs_station_history(
    p_callsign VARCHAR(20),
    p_hours INTEGER DEFAULT 24
) RETURNS TABLE (
    time_stamp TIMESTAMPTZ,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude_m DOUBLE PRECISION,
    speed_knots DOUBLE PRECISION,
    course_deg DOUBLE PRECISION,
    comment TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.time_stamp,
        ST_Y(h.geom::GEOMETRY) AS latitude,
        ST_X(h.geom::GEOMETRY) AS longitude,
        h.altitude_m,
        h.speed_knots,
        h.course_deg,
        h.comment
    FROM gps.aprs_history h
    WHERE h.callsign = p_callsign
      AND h.time_stamp > NOW() - (p_hours || ' hours')::INTERVAL
    ORDER BY h.time_stamp DESC;
END;
$$;

-- Log a raw packet (for debugging/replay)
CREATE OR REPLACE PROCEDURE gps.log_aprs_raw_packet(
    p_raw_packet TEXT,
    p_parsed_ok BOOLEAN DEFAULT FALSE,
    p_parse_error TEXT DEFAULT NULL
) LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO gps.aprs_raw_packets (raw_packet, parsed_ok, parse_error)
    VALUES (p_raw_packet, p_parsed_ok, p_parse_error);
END;
$$;

-- Cleanup old APRS data (call periodically)
CREATE OR REPLACE PROCEDURE gps.cleanup_aprs_data(
    p_history_days INTEGER DEFAULT 30,
    p_raw_days INTEGER DEFAULT 7
) LANGUAGE plpgsql AS $$
BEGIN
    -- Delete old history
    DELETE FROM gps.aprs_history 
    WHERE time_stamp < NOW() - (p_history_days || ' days')::INTERVAL;
    
    -- Delete old raw packets
    DELETE FROM gps.aprs_raw_packets 
    WHERE received_at < NOW() - (p_raw_days || ' days')::INTERVAL;
    
    -- Delete stations not seen in 90 days
    DELETE FROM gps.aprs_stations 
    WHERE last_seen < NOW() - INTERVAL '90 days';
END;
$$;

-- Summary stats for dashboard
CREATE OR REPLACE FUNCTION gps.get_aprs_stats() RETURNS TABLE (
    total_stations BIGINT,
    stations_24h BIGINT,
    total_packets BIGINT,
    packets_24h BIGINT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM gps.aprs_stations)::BIGINT AS total_stations,
        (SELECT COUNT(*) FROM gps.aprs_stations WHERE last_seen > NOW() - INTERVAL '24 hours')::BIGINT AS stations_24h,
        (SELECT COALESCE(SUM(packet_count), 0) FROM gps.aprs_stations)::BIGINT AS total_packets,
        (SELECT COUNT(*) FROM gps.aprs_history WHERE time_stamp > NOW() - INTERVAL '24 hours')::BIGINT AS packets_24h;
END;
$$;
