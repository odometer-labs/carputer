-- aprs_functions.sql
---------------------------
-- 1. SCHEMA
---------------------------
CREATE SCHEMA IF NOT EXISTS aprs;

---------------------------
-- 2. TABLES
---------------------------
CREATE TABLE aprs.stations (
    callsign VARCHAR(20) PRIMARY KEY,
    raw_packet TEXT,
    last_seen TIMESTAMPTZ NOT NULL,
    data TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE aprs.packet_history (
    packet_id BIGSERIAL PRIMARY KEY,
    callsign VARCHAR(20) NOT NULL,
    raw_packet TEXT,
    time_stamp TIMESTAMPTZ NOT NULL,
    data TEXT,
    received_at TIMESTAMPTZ DEFAULT NOW()
);

---------------------------
-- 3. INDEXES
---------------------------
CREATE INDEX IF NOT EXISTS idx_stations_last_seen ON aprs.stations(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_packet_history_callsign ON aprs.packet_history(callsign);
CREATE INDEX IF NOT EXISTS idx_packet_history_timestamp ON aprs.packet_history(time_stamp DESC);

---------------------------
-- 4. CRUD OPERATIONS
---------------------------

-- Standard entry point for APRS packet ingestion
CREATE OR REPLACE PROCEDURE aprs.ingest_packet(
    p_callsign VARCHAR(20),
    p_raw_packet TEXT,
    p_timestamp TEXT,
    p_data TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    -- Insert into packet history
    INSERT INTO aprs.packet_history (callsign, raw_packet, time_stamp, data)
    VALUES (p_callsign, p_raw_packet, p_timestamp::TIMESTAMPTZ, p_data);
    
    -- Upsert into stations (update if exists, insert if not)
    INSERT INTO aprs.stations (callsign, raw_packet, last_seen, data)
    VALUES (p_callsign, p_raw_packet, p_timestamp::TIMESTAMPTZ, p_data)
    ON CONFLICT (callsign) 
    DO UPDATE SET 
        raw_packet = EXCLUDED.raw_packet,
        last_seen = EXCLUDED.last_seen,
        data = EXCLUDED.data;
END;
$$;

-- Fetches all APRS stations ordered by most recent
CREATE OR REPLACE FUNCTION aprs.view_all_stations()
RETURNS TABLE (
    callsign VARCHAR(20),
    raw_packet TEXT,
    last_seen TIMESTAMPTZ,
    data TEXT,
    packet_count BIGINT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.callsign,
        s.raw_packet,
        s.last_seen,
        s.data,
        COUNT(h.packet_id) as packet_count
    FROM aprs.stations s
    LEFT JOIN aprs.packet_history h ON s.callsign = h.callsign
    GROUP BY s.callsign, s.raw_packet, s.last_seen, s.data
    ORDER BY s.last_seen DESC;
END;
$$;

-- Fetches details for a specific APRS station
CREATE OR REPLACE FUNCTION aprs.get_station(p_callsign VARCHAR(20))
RETURNS TABLE (
    callsign VARCHAR(20),
    raw_packet TEXT,
    last_seen TIMESTAMPTZ,
    data TEXT,
    packet_count BIGINT,
    first_seen TIMESTAMPTZ
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.callsign,
        s.raw_packet,
        s.last_seen,
        s.data,
        COUNT(h.packet_id) as packet_count,
        MIN(h.received_at) as first_seen
    FROM aprs.stations s
    LEFT JOIN aprs.packet_history h ON s.callsign = h.callsign
    WHERE s.callsign = p_callsign
    GROUP BY s.callsign, s.raw_packet, s.last_seen, s.data;
END;
$$;

-- Get recent packet history for a station
CREATE OR REPLACE FUNCTION aprs.get_station_history(
    p_callsign VARCHAR(20),
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    packet_id BIGINT,
    raw_packet TEXT,
    time_stamp TIMESTAMPTZ,
    data TEXT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.packet_id,
        h.raw_packet,
        h.time_stamp,
        h.data
    FROM aprs.packet_history h
    WHERE h.callsign = p_callsign
    ORDER BY h.time_stamp DESC
    LIMIT p_limit;
END;
$$;
