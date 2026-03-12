import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

def get_connection():
    """Returns a new connection to the carputer database."""
    conn_info = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )
    # Using dict_row makes results look like {'id': 1} instead of (1,)
    return psycopg.connect(conn_info, row_factory=dict_row)

# Test block: Runs only if you execute this file directly
if __name__ == "__main__":
    try:
        with get_connection() as conn:
            print("Successfully connected to the Carputer DB!")
    except Exception as e:
        print(f"Connection failed: {e}")
