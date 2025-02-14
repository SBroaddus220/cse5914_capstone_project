# -*- coding: utf-8 -*-

"""
Class for file information of imported images.
"""

# **** IMPORTS ****
import sqlite3
import logging

from tagsense.models.base_table import BaseTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class FileTable(BaseTable):
    """
    Table to store the fundamental file information for imported images.
    """

    TABLE_NAME: str = "file_table"
    REQUIRED_COLUMNS: set = {
        "rowid",
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
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            rowid INTEGER PRIMARY KEY,
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


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
