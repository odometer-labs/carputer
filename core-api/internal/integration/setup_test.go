//go:build integration

package integration

import (
	"context"
	"fmt"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

var testPool *pgxpool.Pool

func TestMain(m *testing.M) {
	host := envOr("DB_HOST", "localhost")
	port := envOr("DB_PORT", "5432")
	user := os.Getenv("POSTGRES_USER")
	pass := os.Getenv("POSTGRES_PASSWORD")
	dbname := envOr("POSTGRES_DB", "carputer")

	url := fmt.Sprintf("postgres://%s:%s@%s:%s/%s", user, pass, host, port, dbname)

	pool, err := pgxpool.New(context.Background(), url)
	if err != nil {
		fmt.Fprintf(os.Stderr, "integration test setup: failed to connect to DB: %v\n", err)
		os.Exit(1)
	}

	if err := pool.Ping(context.Background()); err != nil {
		fmt.Fprintf(os.Stderr, "integration test setup: DB ping failed: %v\n", err)
		os.Exit(1)
	}

	testPool = pool
	code := m.Run()
	pool.Close()
	os.Exit(code)
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func truncateTracks(t *testing.T) {
	t.Helper()
	_, err := testPool.Exec(context.Background(),
		`TRUNCATE gps.track_lines, gps.track_points, gps.tracks CASCADE`)
	if err != nil {
		t.Fatalf("truncate tracks: %v", err)
	}
}

func truncateAPRS(t *testing.T) {
	t.Helper()
	_, err := testPool.Exec(context.Background(),
		`TRUNCATE gps.aprs_history, gps.aprs_raw_packets, gps.aprs_stations CASCADE`)
	if err != nil {
		t.Fatalf("truncate aprs: %v", err)
	}
}

func truncateTravelHistory(t *testing.T) {
	t.Helper()
	_, err := testPool.Exec(context.Background(), `TRUNCATE gps.travel_history`)
	if err != nil {
		t.Fatalf("truncate travel_history: %v", err)
	}
}

func truncateVersions(t *testing.T) {
	t.Helper()
	_, err := testPool.Exec(context.Background(), `TRUNCATE gps.version`)
	if err != nil {
		t.Fatalf("truncate version: %v", err)
	}
}
