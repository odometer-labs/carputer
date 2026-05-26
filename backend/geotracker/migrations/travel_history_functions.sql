CREATE OR REPLACE PROCEDURE gps.create_travel_history(
    p_min_x DOUBLE PRECISION,
    p_max_x DOUBLE PRECISION,
    p_min_y DOUBLE PRECISION,
    p_max_y DOUBLE PRECISION,
    p_track_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO gps.travel_history (min_x, max_x, min_y, max_y, track_id)
    VALUES (p_min_x, p_max_x, p_min_y, p_max_y, p_track_id);
END;
$$;

CREATE OR REPLACE FUNCTION gps.list_travel_history()
RETURNS TABLE(
    id BIGINT,
    min_x DOUBLE PRECISION,
    max_x DOUBLE PRECISION,
    min_y DOUBLE PRECISION,
    max_y DOUBLE PRECISION,
    track_id BIGINT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.min_x, t.max_x, t.min_y, t.max_y, t.track_id, t.created_at
    FROM gps.travel_history AS t
    ORDER BY t.id DESC;
END;
$$;

