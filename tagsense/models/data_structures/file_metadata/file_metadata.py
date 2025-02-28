# -*- coding: utf-8 -*-

"""
Class for file information of imported images.
"""

# **** IMPORTS ****
import sqlite3
import logging

from tagsense.models.base_table import BaseTable
from tagsense.models.data_structures.file_table.file_table import FileTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class FileMetadata(BaseTable):
    """
    Table to store the core metadata for imported files.
    """

    TABLE_NAME: str = "file_core_metadata"
    REQUIRED_COLUMNS: set = {
        "rowid",
        "file_id",
        "metadata",
    }

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        """
        Creates the file_core_metadata table if it does not exist.

        Args:
            conn (sqlite3.Connection): The SQLite database connection.
        """
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            rowid INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            metadata TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES {FileTable.TABLE_NAME}(rowid)
        )
        """
        conn.execute(sql)
        conn.commit()

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
