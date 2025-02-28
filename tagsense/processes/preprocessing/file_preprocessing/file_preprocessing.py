# -*- coding: utf-8 -*-

"""
Fundamental file preprocessing.
"""

# **** IMPORTS ****
import os
import shutil
import logging
import sqlite3
import hashlib
from typing import Any
from datetime import datetime

from tagsense.config import CLIENT_FILES_DIR
from tagsense.processes.base_process import BaseProcess
from tagsense.models.data_structures.file_table.file_table import FileTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class FilePreprocessing(BaseProcess):
    """
    Hashes a file and records it and its core metadata in the database.
    """
    TABLE_CLASS = FileTable
    can_repeat: bool = True

    @classmethod
    def execute(cls, db_path: str, param: Any, output_callback=None) -> int:
        super().execute(db_path, param, output_callback)
        file_path = str(param)

        if output_callback:
            output_callback("Executing initial file preprocessing...\n")

        try:
            # Use row_factory so we can reference columns by name
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            md5_hash = cls._calculate_md5(file_path)
            if output_callback:
                output_callback(f"Calculated MD5: {md5_hash}\n")

            existing = conn.execute(
                f"SELECT * FROM {FileTable.TABLE_NAME} WHERE md5_hash = ?",
                (md5_hash,)
            ).fetchone()

            new_basename = os.path.basename(file_path)
            new_ctime = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            new_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

            if existing is not None:
                rowid = existing["rowid"]
                old_original_name = existing["original_name"]
                old_original_path = existing["original_file_path"]
                old_date_created = existing["date_created"]
                old_date_modified = existing["date_modified"]

                # Split each comma-delimited string to see if it's already present
                existing_names = set(old_original_name.split(",")) if old_original_name else set()
                existing_paths = set(old_original_path.split(",")) if old_original_path else set()
                existing_ctimes = set(old_date_created.split(",")) if old_date_created else set()
                existing_mtimes = set(old_date_modified.split(",")) if old_date_modified else set()

                # If all these new data points are already in the sets, skip re-appending
                if (
                    new_basename in existing_names and
                    file_path in existing_paths and
                    new_ctime in existing_ctimes and
                    new_mtime in existing_mtimes
                ):
                    if output_callback:
                        output_callback("Exact file match found in appended data. Skipping re-insert.\n")
                    conn.close()
                    return rowid

                # Otherwise, append new data
                new_original_name = old_original_name + "," + new_basename
                new_original_path = old_original_path + "," + file_path
                new_date_created = old_date_created + "," + new_ctime
                new_date_modified = old_date_modified + "," + new_mtime

                FileTable.update_record(
                    conn,
                    rowid,
                    {
                        "original_name": new_original_name,
                        "original_file_path": new_original_path,
                        "date_created": new_date_created,
                        "date_modified": new_date_modified
                    },
                    id_column="rowid"
                )
                conn.close()

                if output_callback:
                    output_callback(f"Core process re-run. Updated rowid={rowid} for existing MD5.\n")
                return rowid

            # Otherwise create a new record
            _, original_name = os.path.split(file_path)
            file_extension = os.path.splitext(original_name)[1].lower()
            new_filename = f"{md5_hash}{file_extension}"

            destination_dir = CLIENT_FILES_DIR
            os.makedirs(destination_dir, exist_ok=True)
            destination_path = os.path.join(destination_dir, new_filename)
            shutil.copy2(file_path, destination_path)

            file_size = os.path.getsize(destination_path)
            date_created = datetime.fromtimestamp(os.path.getctime(destination_path)).isoformat()
            date_modified = datetime.fromtimestamp(os.path.getmtime(destination_path)).isoformat()
            import_timestamp = datetime.now().isoformat()

            data = {
                "md5_hash": md5_hash,
                "original_name": original_name,
                "file_path": destination_path,
                "original_file_path": file_path,
                "file_size": file_size,
                "file_extension": file_extension,
                "date_created": date_created,
                "date_modified": date_modified,
                "import_timestamp": import_timestamp,
            }
            new_rowid = FileTable.insert_record(conn, data)
            conn.close()

            if output_callback:
                output_callback(f"New file record created. rowid={new_rowid}\n")
            return new_rowid

        except Exception as e:
            err_msg = f"Error in initial file preprocessing: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return -1

    @classmethod
    def _calculate_md5(self, file_path: str) -> str:
        """
        Calculates the MD5 hash of a given file.

        Args:
            file_path (str): The path to the file.

        Returns:
            str: The MD5 hash in hexadecimal format.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read the file in chunks to avoid large memory usage
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
