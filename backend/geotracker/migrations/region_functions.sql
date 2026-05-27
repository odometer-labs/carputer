CREATE OR REPLACE PROCEDURE gps.create_region(
    p_min_x DOUBLE PRECISION,
    p_max_x DOUBLE PRECISION,
    p_min_y DOUBLE PRECISION,
    p_max_y DOUBLE PRECISION,
    p_name TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO gps.region(min_x, max_x, min_y, max_y, name)
    VALUES(p_min_x, p_max_x, p_min_y, p_max_y, p_name);
END;
$$;

CREATE OR REPLACE FUNCTION gps.list_regions()
RETURNS TABLE(
    id BIGINT,
    min_x DOUBLE PRECISION,
    max_x DOUBLE PRECISION,
    min_y DOUBLE PRECISION,
    max_y DOUBLE PRECISION,
    name TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT r.id, r.min_x, r.max_x, r.min_y, r.max_y, r.name
    FROM gps.region AS r
    ORDER BY r.id DESC;
END;
$$;

CREATE OR REPLACE PROCEDURE gps.delete_region(
    p_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM gps.region WHERE id = p_id;
END;
$$;