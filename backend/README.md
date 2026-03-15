### Carputer Database Management

This guide explains how to manage the PostgreSQL/PostGIS database using Docker Compose and psycopg3.

# Prerequisites

Before starting, ensure you have the necessary Python libraries and Docker installed.
On your virtual environment:

1. Install Python Dependencies
   pip install "psycopg[binary]" python-dotenv
2. Install Docker (Linux)
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   On Windows or Mac, go to https://www.docker.com/products/docker-desktop/
   or https://docs.docker.com/get-started/get-docker/ before running the
   venv and installing psycopg.

# Environment Configuration

Before starting the database, update your .env file in this directory to store your credentials.

File: .env

Example:

POSTGRES_USER=user_name_here
POSTGRES_DB=db_name_here
POSTGRES_PASSWORD=your_secure_password_here

---

Connection Settings (Standard for Docker on localhost)

DB_HOST=localhost
DB_PORT=5432

Note: These variables are automatically loaded by the docker-compose.yml file to initialize your
database with the correct user and permissions.

# Database Lifecycle Commands

Use these commands from the root directory (where the docker-compose.yml is located).
Make sure the .env file is in the same directory.

    Docker commands require sudo, see last section of this document on how to remove.

Action Command Description
Start docker compose up -d Starts the DB; creates it on first run, resumes if stopped.
Stop docker compose stop Hibernates the database without removing containers.
Resume docker compose start Wakes up the stopped database.
Remove docker compose down Stops and removes containers but keeps your data.
Nuke docker compose down -v Deletes everything, data included.

# Monitoring and Troubleshooting

View Live Logs
To see the database activity or check for initialization errors:
docker logs -f carputer_db (Press CTRL+C to exit the log view)

# Direct Database Access (CLI)

To run SQL queries manually, enter the interactive psql shell:
Log in to Carputer DB
docker exec -it carputer_db psql -U user_name_here -d db_name_here

Sample Test Commands:
Create a new track: SELECT gps.create_track();
View created track: SELECT \* FROM gps.tracks;
Exit shell: Type exit or \q

# Advanced: Manual Database Management

If you need to create or remove secondary databases without restarting Docker:

Create: docker exec -it carputer_db psql -U user_name_here -d postgres -c "CREATE DATABASE new_test_db;"
Drop: docker exec -it carputer_db psql -U user_name_here -d postgres -c "DROP DATABASE new_test_db;"

# Getting a Database Connection

An example connection to the carputer db is seen in database.py.
Note: Must have the db running first, using docker compose up -d to create, or docker compose start.

# Running Docker Without Sudo

By default, Docker requires root privileges. To allow your user to run Docker commands without sudo, follow these steps:

1. Create the docker group (if it doesn't exist):
   sudo groupadd docker

2. Add your user to the group:
   sudo usermod -aG docker $USER

3. Activate the changes:
   You can either log out and log back in, or run this command to apply the changes to your current terminal session immediately:
   newgrp docker
