import pandas as pd
import os
import duckdb

def connect_db(db_path: str):
    """Connect to the SQLite database specified by db_path."""
    conn = duckdb.connect(database=db_path, read_only=False)

    print(f" ! Database connected: {db_path}")
    return conn
