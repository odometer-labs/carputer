package postgis

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

var connectionPool *pgxpool.Pool

func Initialize() {
	connectionPool = createConnectionPool()
}

func GetConnectionPool() *pgxpool.Pool {
	if connectionPool == nil {
		connectionPool = createConnectionPool()
	}
	return connectionPool
}

func createConnectionPool() *pgxpool.Pool {
	databaseCreds, err := getDatabaseUsernamePassword()
	if err != nil {
		panic(err)
	}

	host := envOr("DB_HOST", "db")
	port := envOr("DB_PORT", "5432")
	dbname := envOr("POSTGRES_DB", "carputer")

	connectionUrl := fmt.Sprintf("postgres://%s@%s:%s/%s", databaseCreds, host, port, dbname)

	pool, err := pgxpool.New(context.Background(), connectionUrl)
	if err != nil {
		panic(fmt.Sprintf("failed to create connection pool: %v", err))
	}
	return pool
}

func getDatabaseUsernamePassword() (string, error) {
	username := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")

	if username != "" && password != "" {
		return fmt.Sprintf("%s:%s", username, password), nil
	}

	if username == "" {
		slog.Warn("Unable to find POSTGRES_USER environment variable")
	}
	if password == "" {
		slog.Warn("Unable to find POSTGRES_PASSWORD environment variable")
	}

	// Fall back to .env files
	err := godotenv.Load()
	if err != nil {
		return "", errors.New("Unable to find POSTGRES_USER and POSTGRES_PASSWORD environment variables")
	}

	username = os.Getenv("POSTGRES_USER")
	password = os.Getenv("POSTGRES_PASSWORD")
	return fmt.Sprintf("%s:%s", username, password), nil
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
