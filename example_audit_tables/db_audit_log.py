# -*- coding: utf-8 -*-

"""
A helper class to create and insert audit-log entries.
"""

# ****
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, Optional

# ****
class DBAuditLog:
    """
    A helper class to create and insert audit-log entries.
    
    Usage:
      1) Call create_log_table(conn) at application startup to ensure
         the audit table is created.
      2) Call log_operation(...) whenever an INSERT, UPDATE, or DELETE
         occurs.
    """

    TABLE_NAME = "db_operations_log"

    @staticmethod
    def create_log_table(conn: sqlite3.Connection) -> None:
        """
        Create a table to store each database operation with a timestamp,
        the table name, operation type, row id, the changed data, etc.
        """
        sql = f"""
        CREATE TABLE IF NOT EXISTS {DBAuditLog.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            record_id TEXT,  -- Not always an integer, e.g. 'source_id' might be used
            changes TEXT,    -- JSON representation of the changes or inserted data
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        conn.commit()

    @staticmethod
    def log_operation(
        conn: sqlite3.Connection,
        table_name: str,
        operation_type: str,   # e.g. "INSERT", "UPDATE", "DELETE"
        record_id: Optional[str],
        changes: Dict[str, Any]
    ) -> None:
        """
        Inserts a record into db_operations_log describing the DB operation.
        'changes' should be a dict representing the changed or inserted fields.
        'record_id' might be an int or string ID (converted to str if needed).
        """
        # Convert changes to a JSON string
        changes_json = json.dumps(changes, default=str)
        sql = f"""
        INSERT INTO {DBAuditLog.TABLE_NAME} (table_name, operation_type, record_id, changes)
        VALUES (?, ?, ?, ?)
        """
        conn.execute(sql, (table_name, operation_type, str(record_id) if record_id else None, changes_json))
        conn.commit()


# ****
if __name__ == "__main__":
    raise Exception("This module is not meant to be run directly.")
