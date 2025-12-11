import sqlite3
from datetime import datetime

import pandas as pd

from config import DB_PATH


def init_db():
    """
    Create the SQLite database and the `complaints` table if it does not already exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_type TEXT NOT NULL,
            intensity INTEGER,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            timestamp TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            votes INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def get_connection():
    """
    Return a new SQLite connection.
    """
    return sqlite3.connect(DB_PATH)


def add_complaint(issue_type, intensity, lat, lon, description, photo_path):
    """
    Insert a new complaint into the database.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO complaints (issue_type, intensity, lat, lon, timestamp, description, photo_path, votes)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            issue_type,
            intensity,
            lat,
            lon,
            datetime.now().isoformat(),
            description,
            photo_path,
        ),
    )
    conn.commit()
    conn.close()


def load_complaints():
    """
    Load all complaints as a pandas DataFrame.
    """
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM complaints", conn)
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df
