# -*- coding: utf-8 -*-

"""
Algorithm to store YOLOv8 object data
"""

import logging
from typing import Any

from tagsense.processes.base_process import BaseProcess
from tagsense.models.data_structures.yolo_detected_objects.detected_objects import DetectedObjects
from ultralytics import YOLO

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DetectObjects(BaseProcess):
    """
    Functions for YOLOv8 object detection.
    """
    TABLE_CLASS = DetectedObjects
    can_repeat: bool = False  # ???

    def execute(self, db_path: str, param: Any, output_callback=None) -> str:
        """
        Stores a single run entry in single_run_process_records. Expects
        'param' to be the file's rowid. If there's already an entry for
        that file_id, it won't create another.
        """
        import sqlite3
        import json
        super().execute(db_path, param, output_callback)  # Ensures table creation

        row_id = int(param)
        if output_callback:
            output_callback("Running detect objects process...\n")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Check if we already have a record
            existing = conn.execute(
                f"SELECT rowid FROM {DetectedObjects.TABLE_NAME} WHERE file_id = ?",
                (row_id,)
            ).fetchone()

            if existing:
                msg = f"Detect objects process already executed for file_id={row_id}. Skipping."
                conn.close()
                if output_callback:
                    output_callback(msg + "\n")
                return msg
            
            # Otherwise, create a new record
            cursor = conn.execute("SELECT file_path FROM file_table WHERE rowid = ?", (row_id,))
            file_row = cursor.fetchone()
            if not file_row:
                raise ValueError(f"No file found for rowid={row_id}")
            file_path = file_row["file_path"]
            model = YOLO("yolov8n.pt")
            results = model(file_path)
            
            for result in results:
                for box in result.boxes.data:
                    x1, y1, x2, y2, confidence, class_id = box.tolist()
                    data = {
                        "file_id": row_id,
                        "class_label": model.names[int(class_id)],
                        "confidence": confidence,
                        "bbox": json.dumps([x1, y1, x2, y2])
                    }
                    DetectedObjects.insert_record(conn, data)
            conn.close()

            msg = f"Detect objects process completed for file_id={row_id}."
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in detect objects process: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
