import pandas as pd
import os
import sqlite3

def connect_db(db_path: str):
    """Connect to the SQLite database specified by db_path."""
    conn = sqlite3.connect(db_path)
    print(f" ! Database connected: {db_path}")
    return conn
