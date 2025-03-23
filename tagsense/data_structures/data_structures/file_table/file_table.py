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
class FileTable(SQLITETable):
    """Table to store the fundamental file information for imported images. """

    table_name: str = "file_table"
    required_columns: set = {
        "rowid",
        "entry_key",
        "process_uid",
        "input_structure_uid",
        "input_data_key",
        "md5_hash",
        "original_name",
        "file_path",
        "original_file_path",
        "file_size",
        "file_extension",
        "date_created",
        "date_modified",
        "import_timestamp",
    }

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        """
        Creates the fundamental_file_records table if it does not exist.

        Args:
            conn (sqlite3.Connection): The SQLite database connection.
        """
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY,
            entry_key TEXT UNIQUE NOT NULL,
            process_uid TEXT NOT NULL,
            input_structure_uid TEXT,
            input_data_key TEXT,
            md5_hash TEXT NOT NULL,
            original_name TEXT,
            file_path TEXT,
            original_file_path TEXT,
            file_size INTEGER,
            file_extension TEXT,
            date_created TEXT,
            date_modified TEXT,
            import_timestamp TEXT
        )
        """
        conn.execute(sql)
        conn.commit()
        
class Files(AppDataStructure):
    table: SQLITETable = FileTable

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
