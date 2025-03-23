# -*- coding: utf-8 -*-

"""
Class for file information of imported images.
"""

# **** IMPORTS ****
import sqlite3
import logging

from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.app_data_structure import AppDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class FileMetadataTable(SQLITETable):
    """Table to store the metadata for imported files. """

    table_name: str = "file_core_metadata"
    required_columns: set = {"rowid", "entry_key", "process_uid", "input_structure_uid", "input_data_key","metadata"}

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_key TEXT UNIQUE NOT NULL,
            process_uid TEXT NOT NULL,
            input_structure_uid TEXT NOT NULL,
            input_data_key TEXT NOT NULL,
            metadata TEXT NOT NULL
        )
        """
        conn.execute(sql)
        conn.commit()

class FileMetadata(AppDataStructure):
    table: SQLITETable = FileMetadataTable

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
