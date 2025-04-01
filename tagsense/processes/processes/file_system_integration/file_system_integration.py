# -*- coding: utf-8 -*-

"""
Fundamental file preprocessing.
"""

# **** IMPORTS ****
import os
import sqlite3
import shutil
import logging
import blake3
from datetime import datetime
from typing import Tuple, Optional
from pathlib import Path

from tagsense.config import CLIENT_FILES_DIR
from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.file_table.file_table import Files
from tagsense.data_structures.manual_data_structure import ManualDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class FileSystemIntegration(AppProcess):
    """
    Hashes a file and records it and its core metadata in the database.
    """
    name: str = "file_system_integration"
    input: AppDataStructure = ManualDataStructure
    output: AppDataStructure = Files

    @classmethod
    def execute(cls, input_data_key: str, output_callback=None) -> Tuple[str, Optional[dict]]:
        """Execute the process. Assumes "file_path" is a key in the input data structure."""
        
        if output_callback:
            output_callback(f"Executing {cls.name}...\n")

        # ****
        # Parse the input data
        input_data = cls.input.read_by_entry_key(input_data_key)
        if not input_data:
            err_msg = f"Error in {cls.name}: No data found for key {input_data_key}."
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return (err_msg, None)
        file_path = input_data["file_path"]
    
        # ****
        # Hash the file and check if it already exists in the database
        blake3_hash = cls._calculate_blake3(file_path)
        if output_callback:
            output_callback(f"Calculated BLAKE3: {blake3_hash}\n")
        existing = cls.output.read(column_name="blake3_hash", value=blake3_hash)
        if existing:
            message = f"{cls.name} already executed for {file_path} and has entry key {existing['entry_key']}. Skipping."
            if output_callback:
                output_callback(f"{message}\n")
            return (message, None)
        
        # ****
        # If not, create new record
        _, original_name = os.path.split(file_path)
        file_extension = os.path.splitext(original_name)[1].lower()
        new_filename = f"{blake3_hash}{file_extension}"

        destination_dir = CLIENT_FILES_DIR
        os.makedirs(destination_dir, exist_ok=True)
        destination_path = os.path.join(destination_dir, new_filename)
        shutil.copy2(file_path, destination_path)

        file_size = os.path.getsize(destination_path)
        date_created = datetime.fromtimestamp(os.path.getctime(destination_path)).isoformat()
        date_modified = datetime.fromtimestamp(os.path.getmtime(destination_path)).isoformat()
        import_timestamp = datetime.now().isoformat()

        data = {
            "blake3_hash": blake3_hash,
            "original_name": original_name,
            "file_path": destination_path,
            "original_file_path": file_path,
            "file_size": file_size,
            "file_extension": file_extension,
            "date_created": date_created,
            "date_modified": date_modified,
            "import_timestamp": import_timestamp,
        }
        new_rowid = cls.output.create_entry(
            data=data,
            process=cls,
            input_data_structure=cls.input,
            input_data_key=input_data_key,
        )

        msg = f"{cls.name} completed for {original_name}."
        if output_callback:
            output_callback(f"{msg}.\n")
        return (msg, data)

    @classmethod
    def _calculate_blake3(self, file_path: Path) -> str:
        """
        Calculates the BLAKE3 hash of a given file.

        Args:
            file_path (Path): The path to the file.

        Returns:
            str: The BLAKE3 hash in hexadecimal format.
        """
        hash_blake3 = blake3.blake3()
        with open(file_path, "rb") as f:
            # Read the file in chunks to avoid large memory usage
            for chunk in iter(lambda: f.read(4096), b""):
                hash_blake3.update(chunk)
        return hash_blake3.hexdigest()

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
