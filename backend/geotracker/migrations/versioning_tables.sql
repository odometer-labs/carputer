CREATE TABLE IF NOT EXISTS gps.version (
    id BIGSERIAL PRIMARY KEY,
    version_number TEXT NOT NULL UNIQUE,
    git_hash TEXT,
    release_date TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO gps.version (version_number) 
VALUES ('1.0.0')
ON CONFLICT (version_number) DO NOTHING;