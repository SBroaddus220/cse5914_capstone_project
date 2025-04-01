# -*- coding: utf-8 -*-

"""
Interface for the SQLite database.
"""

# **** IMPORTS ****
import logging
import sqlite3
import sqlparse
from pathlib import Path
from typing import Any, Dict, List, Tuple

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** FUNCTIONS ****
def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database.

    Args:
        db_path (Path): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Connection object to the SQLite database.
    """
    logger.debug(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def backup_database(source_db_conn: sqlite3.Connection, destination_db_path: Path) -> None:
    """Copies the source database to the destination path.

    Args:
        source_db_conn (sqlite3.Connection): Connection to the source database.
        destination_db_path (Path): Path to the destination database.
    """
    logger.info(f"Backing up database at {source_db_conn} to {destination_db_path}")
    backup_conn = get_db_connection(destination_db_path)
    source_db_conn.backup(backup_conn)

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
    