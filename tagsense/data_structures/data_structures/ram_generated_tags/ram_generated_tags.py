# -*- coding: utf-8 -*-

"""
Data structure for generated RAM tags.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.app_data_structure import AppDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class RamGeneratedTagsTable(SQLITETable):
    table_name: str = "ram_generated_tags"
    required_columns: set[str] = {"rowid", "entry_key", "process_uid", "input_structure_uid", "input_data_key", "tags"}
    
    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_key TEXT UNIQUE NOT NULL,
            process_uid TEXT NOT NULL,
            input_structure_uid TEXT,
            input_data_key TEXT NOT NULL,
            tags TEXT
        )
        """
        conn.execute(sql)
        conn.commit()

class RamGeneratedTags(AppDataStructure):
    table: SQLITETable = RamGeneratedTagsTable

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.") 
