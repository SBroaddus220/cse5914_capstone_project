# -*- coding: utf-8 -*-

"""
Data structure for example repeatable text appending.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.app_data_structure import AppDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class StoredRandomTextTable(SQLITETable):
    """A table to store data for a repeatable user process."""
    table_name: str = "stored_random_text_records"
    required_columns: set[str] = {"rowid", "entry_key", "process_uid", "input_structure_uid", "input_data_key", "data"}
    
    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_key TEXT UNIQUE NOT NULL,
            process_uid TEXT NOT NULL,
            input_structure_uid TEXT,
            input_data_key TEXT NOT NULL,
            data TEXT
        )
        """
        conn.execute(sql)
        conn.commit()

class StoredRandomText(AppDataStructure):
    table: SQLITETable = StoredRandomTextTable

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
