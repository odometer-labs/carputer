-- create a new version
CREATE OR REPLACE PROCEDURE gps.create_new_version(
    p_version_number TEXT,
    p_git_hash TEXT,
    p_release_date TIMESTAMPTZ
)
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO gps.version (version_number, git_hash, release_date)
    VALUES (p_version_number, p_git_hash, p_release_date);
END;
$$;

-- returns the latest version
CREATE OR REPLACE FUNCTION gps.get_latest_version()
RETURNS TABLE(
    id BIGINT,
    version_number TEXT,
    git_hash TEXT,
    release_date TIMESTAMPTZ
)
LANGUAGE plpgsql
AS
$$
BEGIN 
    RETURN QUERY
    SELECT v.id, v.version_number, v.git_hash, v.release_date
    FROM gps.version AS v 
    ORDER BY v.id DESC
    LIMIT 1;
END;
$$;

-- lists all the versions
CREATE OR REPLACE FUNCTION gps.get_version_history()
RETURNS TABLE(
    id BIGINT,
    version_number TEXT,
    git_hash TEXT,
    release_date TIMESTAMPTZ
)
LANGUAGE plpgsql
AS
$$
BEGIN 
    RETURN QUERY
    SELECT v.id, v.version_number, v.git_hash, v.release_date 
    FROM gps.version;
END;
$$;