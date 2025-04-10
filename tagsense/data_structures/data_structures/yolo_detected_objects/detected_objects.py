# -*- coding: utf-8 -*-
"""
Data structure for storing YOLOv8 detected objects.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.app_data_structure import AppDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DetectedObjectsTable(SQLITETable):
    """
    A table to store YOLOv8 object detection results
    """
    table_name = "yolo_detected_objects"
    required_columns: set[str] = {"rowid", "entry_key", "process_uid", "input_structure_uid", "input_data_key", "class_label", "confidence", "bbox"}

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_key TEXT UNIQUE NOT NULL,
            process_uid TEXT NOT NULL,
            input_structure_uid TEXT,
            input_data_key TEXT NOT NULL,
            class_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            bbox TEXT NOT NULL
        )
        """
        conn.execute(sql)
        conn.commit()

class DetectedObjects(AppDataStructure):
    table: SQLITETable = DetectedObjectsTable

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.") 