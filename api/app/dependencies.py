from dotenv import load_dotenv
import psycopg
import psycopg_pool
from psycopg import Connection
from psycopg.rows import dict_row
import os
from psycopg_pool import ConnectionPool

load_dotenv()

class DBConnectionPool:

    def __init__(self):
        self.pool: ConnectionPool
        self._init_connection_pool()

    def _init_connection_pool(self):
        conn_info = (
            f"host={os.getenv('DB_HOST', 'localhost')} "
            f"port={os.getenv('DB_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}"
        )
        # Using dict_row makes results look like {'id': 1} instead of (1,)

        self.pool = ConnectionPool(conn_info, kwargs={"row_factory": dict_row})

    def get_connection(self):
        """Returns a new connection to the carputer database."""

        return self.pool.connection()

dbConnectionPool: DBConnectionPool = DBConnectionPool()