# -*- coding: utf-8 -*-

"""
Data structure for example repeatable text appending.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.models.base_table import BaseTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class AppendedText(BaseTable):
    """
    A table to store 'appended text' data for a repeatable user process.
    """
    TABLE_NAME = "append_text_process_records"
    REQUIRED_COLUMNS = {"rowid", "file_id", "appended_text"}

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            rowid INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            appended_text TEXT
        )
        """
        conn.execute(sql)
        conn.commit()

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
