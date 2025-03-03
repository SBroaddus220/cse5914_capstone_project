# -*- coding: utf-8 -*-

"""
A helper class to create and insert audit-log entries.
This module provides a DBAuditLog class that manages the audit-log table.
"""

import sqlite3
import json
from typing import Any, Dict, Optional

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
            record_id TEXT,
            changes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        conn.commit()

    @staticmethod
    def log_operation(
        conn: sqlite3.Connection,
        table_name: str,
        operation_type: str,    # e.g. "INSERT", "UPDATE", "DELETE"
        record_id: Optional[str],   
        changes: Dict[str, Any]
    ) -> None:
        """
        Inserts a record into db_operations_log describing the DB operation.
        'changes' should be a dict representing the changed or inserted fields.
        'record_id' might be an int or string ID (converted to str if needed).
        """
        
        # Convert to JSON
        changes_json = json.dumps(changes, default=str)
        sql = f"""
        INSERT INTO {DBAuditLog.TABLE_NAME} (table_name, operation_type, record_id, changes)
        VALUES (?, ?, ?, ?)
        """
        conn.execute(sql, (table_name, operation_type, record_id, changes_json))
        conn.commit()
