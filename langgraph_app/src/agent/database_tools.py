import pandas as pd
import duckdb
import threading
import os
import pandas as pd
import os
import duckdb

# Database paths (try in order)
# Normalize the relative path properly
_relative_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "olist.db"))
DB_PATHS = [
    _relative_db_path,
    "/media/edward/SSD-Data/My Folder/ai-data-analyzer/olist.db",
    "C:\\Users\\OSVALDO-SOFTENG\\Documents\\edward-portfolio\\GIT\\ai-data-analyzer\\olist.db"
]

# Thread-local storage for database connections
thread_local = threading.local()
def get_db_connection():
    """Get a thread-safe database connection for LangGraph.
    
    This function uses thread-local storage to ensure each thread
    has its own database connection, which is essential for LangGraph's
    concurrent execution model.
    """
    if not hasattr(thread_local, "conn") or thread_local.conn is None:
        print(f" ! Attempting to connect to database...")
        for db_path in DB_PATHS:
            try:
                # Check if file exists first
                if not os.path.exists(db_path):
                    print(f" ! Database file not found: {db_path}")
                    continue
                    
                print(f" ! Trying to connect to: {db_path}")
                conn = duckdb.connect(database=db_path, read_only=True)
                thread_local.conn = conn
                thread_local.db_path = db_path
                print(f" ! Database connected successfully: {db_path}")
                try:
                    conn.execute("LOAD spatial;")
                    conn.execute("LOAD httpfs;")
                    conn.execute("LOAD fts;")
                    conn.execute("LOAD icu;")
                except Exception as e:
                    conn.execute("INSTALL spatial;")
                    conn.execute("INSTALL httpfs;")
                    conn.execute("INSTALL fts;")
                    conn.execute("INSTALL icu;")
                print(f" ! Extensions loaded successfully")
                break
            except Exception as e:
                print(f" ! Failed to connect to {db_path}: {e}")
                continue
        else:
            # Provide helpful error message with all attempted paths
            attempted_paths = "\n  - ".join(DB_PATHS)
            raise Exception(f"Failed to connect to any database path. Attempted paths:\n  - {attempted_paths}")
    return thread_local.conn

def connect_db(db_path: str):
    """Connect to the SQLite database specified by db_path."""
    conn = duckdb.connect(database=db_path, read_only=False)

    print(f" ! Database connected: {db_path}")
    return conn
