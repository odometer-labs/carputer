Carputer Database Management

This guide explains how to manage the PostgreSQL/PostGIS database for the Carputer project 
using Docker Compose and psycopg3.

Prerequisites

Before starting, ensure you have the necessary Python libraries and Docker installed.
1. Install Python Dependencies
    pip install "psycopg[binary]" python-dotenv
2. Install Docker (Linux)
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

Environment Configuration
Before starting the database, update your .env file in this directory to store your credentials.

File: .env

Example:

POSTGRES_USER=driver_admin
POSTGRES_DB=carputer
POSTGRES_PASSWORD=your_secure_password_here
Note: These variables are automatically loaded by the docker-compose.yml file to initialize your database 
with the correct user and permissions



Database Lifecycle Commands

Use these commands from the root directory (where the docker-compose.yml is located).

Action  Command Description
Start   docker compose up -d    Starts the DB in the background and runs init.sql.
Stop    docker compose stop     Hibernates the database without removing containers.
Resume  docker compose start    Wakes up the stopped database.
Remove  docker compose down     Stops and removes containers but keeps your data.
Nuke    docker compose down -v  Deletes everything, data included.

Monitoring and Troubleshooting
View Live Logs
To see the database activity or check for initialization errors:
docker logs -f carputer_db (Press CTRL+C to exit the log view)

 Direct Database Access (CLI)
 To run SQL queries manually, enter the interactive psql shell:
 Log in to Carputer DB
 docker exec -it carputer_db psql -U driver_admin -d carputer

Sample Test Commands:
Create a new track: SELECT gps.create_track();
View created track: SELECT * FROM gps.tracks;
Exit shell: Type exit or \q 

Advanced: Manual Database Management
If you need to create or remove secondary databases without restarting Docker:

Create: docker exec -it carputer_db psql -U driver_admin -d postgres -c "CREATE DATABASE new_test_db;
"Drop: docker exec -it carputer_db psql -U driver_admin -d postgres -c "DROP DATABASE new_test_db;"