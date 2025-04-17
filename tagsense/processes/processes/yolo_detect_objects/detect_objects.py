# -*- coding: utf-8 -*-

"""
Algorithm to store YOLOv8 object data
"""

import logging
from typing import Tuple, Optional
from pathlib import Path
import json

from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.yolo_detected_objects.detected_objects import DetectedObjects
from tagsense.data_structures.data_structures.file_table.file_table import Files

from ultralytics import YOLO

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DetectObjects(AppProcess):
    """
    Functions for YOLOv8 object detection. Not repeatedable for any given input.
    """
    name: str = "detect_objects"
    input: AppDataStructure = Files
    output: AppDataStructure = DetectedObjects

    @classmethod
    def execute(cls, input_data_key: str) -> Tuple[str, Optional[dict]]:
        """
        Stores a single run entry.
        """

        print(f"Running {cls.name}...\n")
            
        # ****
        # Check if the process has already been run
        existing = cls.output.read_by_input_key(input_data_key)
        reference_msg = f"{input_data_key} from {cls.input.name}"
        if existing:
            msg = f"{cls.name} already executed for {reference_msg}. Skipping."
            print(msg + "\n")
            return (msg, None)
        
        # ****
        # Otherwise, create a new record
        file_record = cls.input.read_by_entry_key(input_data_key)
        if not file_record:
            msg = "No matching file record found in database."
            print(msg + "\n")
            return (msg, None)
        
        file_path: str = Path(file_record["file_path"]).as_posix()
        model = YOLO("yolov8n.pt")
        results = model(file_path)

        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, confidence, class_id = box.tolist()
                data = {
                    "class_label": model.names[int(class_id)],
                    "confidence": confidence,
                    "bbox": json.dumps([x1, y1, x2, y2])
                }
                
                cls.output.create_entry(
                    data=data,
                    process=cls,
                    input_data_structure=cls.input,
                    input_data_key=input_data_key,
                )
                

        msg = f"{cls.name} process completed for {reference_msg}."
        print(msg + "\n")
        return (msg, {"success": True})


# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
