# -*- coding: utf-8 -*-

"""
Base class for all sources.
"""

# ****
import logging
import sqlite3
from typing import Any, Dict, List, Optional

# ****
# Set up logger
logger = logging.getLogger(__name__)

# ****
class BaseSource:
    """
    A base class to define standard CRUD operations for source tables.
    Subclasses can override these methods or extend them as needed.
    """

    TABLE_NAME: str = ""  # Must be overridden in subclasses
    REQUIRED_COLUMNS: set = set()  # Must be overridden in subclasses

    @classmethod
    def create_table(cls, conn: sqlite3.Connection):
        """
        Create the table for this source if it doesn't already exist.
        Subclasses should override with their own CREATE TABLE statement.
        """
        raise NotImplementedError("Subclasses must implement create_table()")

    @classmethod
    def verify_table(cls, conn: sqlite3.Connection) -> bool:
        """
        Verify that this source table has all required columns.
        """
        return cls._verify_columns(conn, cls.TABLE_NAME, cls.REQUIRED_COLUMNS)

    @classmethod
    def insert_record(cls, conn: sqlite3.Connection, data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a single record into the table and return the new record ID.
        
        Returns:
            int: The newly inserted record ID, or None if the ID cannot be determined.
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        cursor = conn.execute(sql, list(data.values()))
        conn.commit()

        # Attempt to determine the new record ID
        record_id = None
        if "source_id" in data:
            record_id = int(data["source_id"])  # Explicit ID field
        elif "id" in data:
            record_id = int(data["id"])  # Explicit ID field
        else:
            # If the table has an INTEGER PRIMARY KEY, fetch last inserted row ID
            row = conn.execute("SELECT last_insert_rowid()").fetchone()
            if row and row[0]:
                record_id = int(row[0])

        # Log the operation
        cls._log_operation(conn, "INSERT", str(record_id) if record_id else None, data)

        return record_id  # Return the new record ID

    @classmethod
    def update_record(cls, conn: sqlite3.Connection, row_id: int, data: Dict[str, Any], id_column="rowid") -> None:
        """
        Update a record by specifying the row ID (or another unique ID column).
        By default, uses rowid if not otherwise specified.
        """
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        sql = f"UPDATE {cls.TABLE_NAME} SET {set_clause} WHERE {id_column} = ?"
        conn.execute(sql, list(data.values()) + [row_id])
        conn.commit()
        cls._log_operation(conn, "UPDATE", str(row_id), data)

    @classmethod
    def delete_record(cls, conn: sqlite3.Connection, row_id: int, id_column="rowid") -> None:
        """
        Delete a record from the table by row ID (or another ID column).
        """
        old_record = cls.fetch_record(conn, row_id, id_column) or {}  # Fetch existing record for logging
        sql = f"DELETE FROM {cls.TABLE_NAME} WHERE {id_column} = ?"
        conn.execute(sql, (row_id,))
        conn.commit()
        cls._log_operation(conn, "DELETE", str(row_id), old_record)

    @classmethod
    def fetch_record(cls, conn: sqlite3.Connection, row_id: int, id_column="rowid") -> Optional[Dict[str, Any]]:
        """
        Fetch a single record by row ID (or another unique ID column).
        Returns a dictionary of column->value if found, otherwise None.
        """
        cursor = conn.execute(f"SELECT * FROM {cls.TABLE_NAME} WHERE {id_column} = ?", (row_id,))
        row = cursor.fetchone()
        if row is None:
            return None

        desc = [d[0] for d in cursor.description]
        return dict(zip(desc, row))

    @classmethod
    def fetch_all(cls, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """
        Fetch all records from the table as a list of dicts.
        """
        cursor = conn.execute(f"SELECT * FROM {cls.TABLE_NAME}")
        rows = cursor.fetchall()
        desc = [d[0] for d in cursor.description]
        return [dict(zip(desc, row)) for row in rows]

    @classmethod
    def _verify_columns(cls, conn: sqlite3.Connection, table_name: str, required_columns: set) -> bool:
        """
        Helper method to check if a table has at least the required columns.
        """
        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        actual_columns = {row[1] for row in cursor.fetchall()}
        return required_columns.issubset(actual_columns)

    @classmethod
    def _log_operation(cls, conn: sqlite3.Connection, operation_type: str, record_id: Optional[str], changes: Dict[str, Any]) -> None:
        """
        Internal convenience method to log each DB operation.
        """
        DBAuditLog.log_operation(conn, cls.TABLE_NAME, operation_type, record_id, changes)