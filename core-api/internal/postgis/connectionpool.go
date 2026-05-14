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

const DatabaseUrl = "db:5432"
const DatabaseName = "carputer"

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

	var connectionUrl string = fmt.Sprintf("postgres://%s@%s/%s", databaseCreds, DatabaseUrl, DatabaseName)

	pool, err := pgxpool.New(context.Background(), connectionUrl)
	return pool
}

func getDatabaseUsernamePassword() (string, error) {
	var username string = os.Getenv("POSTGRES_USER")
	var password string = os.Getenv("POSTGRES_PASSWORD")

	if len([]rune(username)) != 0 && len([]rune(password)) != 0 {
		return fmt.Sprintf("%s:%s", username, password), nil
	}

	if len([]rune(username)) == 0 {
		slog.Warn("Unable to find POSTGRES_USER environment variable")
	}

	if len([]rune(password)) == 0 {
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
