from dotenv import load_dotenv
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
import os

load_dotenv()

def get_connection() -> Connection:
    """Returns a new connection to the carputer database."""

    conn_info = (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('POSTGRES_DB')} "
        f"user={os.getenv('POSTGRES_USER')} "
        f"password={os.getenv('POSTGRES_PASSWORD')}"
    )
    # Using dict_row makes results look like {'id': 1} instead of (1,)
    return psycopg.connect(conn_info, row_factory=dict_row)
