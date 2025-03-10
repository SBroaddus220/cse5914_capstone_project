# -*- coding: utf-8 -*-
"""
Data structure for storing YOLOv8 detected objects.
"""

# **** IMPORTS ****
import logging
import sqlite3

from tagsense.models.base_table import BaseTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DetectedObjects(BaseTable):
    """
    A table to store YOLOv8 object detection results
    """
    TABLE_NAME = "yolo_detected_objects"
    REQUIRED_COLUMNS = {"rowid", "file_id", "class_label", "confidence", "bbox"}

    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            rowid INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            class_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            bbox TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES file_table(rowid)
        )
        """
        conn.execute(sql)
        conn.commit()