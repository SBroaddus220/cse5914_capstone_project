# -*- coding: utf-8 -*-

"""
Interface for the SQLite database.
"""

# **** IMPORTS ****
import logging
import sqlite3
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
    logger.info(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def get_foreign_keys(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str, str, str]]:
    """Retrieve foreign key relationships for a given table.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Table name.

    Returns:
        List[Tuple[str, str, str, str]]: List of (from_table, from_column, to_table, to_column).
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    return [(ref[2], ref[3], table, ref[4]) for ref in cursor.fetchall()]


def find_referencing_rows(
    conn: sqlite3.Connection, table: str, column: str, value: Any
) -> Dict[str, List[Tuple]]:
    """Find all rows that reference a given row.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Target table name.
        column (str): Target column name.
        value (Any): Value to search for.

    Returns:
        Dict[str, List[Tuple]]: Mapping of referencing table names to lists of matching rows.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    references = cursor.fetchall()

    results = {}
    
    for ref in references:
        from_table = ref[2]  # Table that references this table
        from_column = ref[3]  # Column in the referencing table

        query = f"SELECT * FROM {from_table} WHERE {from_column} = ?"
        rows = cursor.execute(query, (value,)).fetchall()

        if rows:
            results[from_table] = rows
    
    return results


def find_referenced_rows(conn: sqlite3.Connection, table: str, row_id: Any) -> Dict[str, List[Tuple]]:
    """Find rows that a given row references.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Source table name.
        row_id (Any): ID of the row to check.

    Returns:
        Dict[str, List[Tuple]]: Mapping of referenced table names to lists of matching rows.
    """
    cursor = conn.cursor()
    foreign_keys = get_foreign_keys(conn, table)

    results = {}

    for from_table, from_column, to_table, to_column in foreign_keys:
        # Get the value of the foreign key column in the given row
        cursor.execute(f"SELECT {from_column} FROM {from_table} WHERE id = ?", (row_id,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            ref_value = result[0]
            query = f"SELECT * FROM {to_table} WHERE {to_column} = ?"
            referenced_rows = cursor.execute(query, (ref_value,)).fetchall()

            if referenced_rows:
                results[to_table] = referenced_rows

    return results


def find_sibling_rows(conn: sqlite3.Connection, table: str, row_id: Any) -> Dict[str, List[Tuple]]:
    """Find rows that share the same parent as a given row.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Table to check for siblings.
        row_id (Any): ID of the row whose siblings are sought.

    Returns:
        Dict[str, List[Tuple]]: Mapping of parent tables to lists of sibling rows.
    """
    cursor = conn.cursor()
    foreign_keys = get_foreign_keys(conn, table)

    results = {}

    for from_table, from_column, to_table, to_column in foreign_keys:
        # Get the parent's ID for the given row
        cursor.execute(f"SELECT {from_column} FROM {from_table} WHERE id = ?", (row_id,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            parent_id = result[0]

            # Find other rows in the same table with the same parent
            query = f"SELECT * FROM {from_table} WHERE {from_column} = ? AND id != ?"
            siblings = cursor.execute(query, (parent_id, row_id)).fetchall()

            if siblings:
                results[from_table] = siblings

    return results

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
    