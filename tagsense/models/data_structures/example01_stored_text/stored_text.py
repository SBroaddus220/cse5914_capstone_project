# -*- coding: utf-8 -*-

"""
Data structure for example single-run text storage.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.models.base_table import BaseTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class StoredText(BaseTable):
    """
    A table to store a single-run flag or data for a non-repeatable user process.
    """
    TABLE_NAME = "single_run_process_records"
    REQUIRED_COLUMNS = {"rowid", "file_id", "some_data"}

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            rowid INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            some_data TEXT
        )
        """
        conn.execute(sql)
        conn.commit()

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
