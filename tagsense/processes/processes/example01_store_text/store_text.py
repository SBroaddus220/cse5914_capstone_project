# -*- coding: utf-8 -*-

"""
Example algorithm to store text data.
"""

# **** IMPORTS ****
import logging
from typing import Any

from tagsense.database import get_db_connection
from tagsense.processes.base_process import BaseProcess
from tagsense.models.data_structures.example01_stored_text.stored_text import StoredText

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class StoreText(BaseProcess):
    """
    An example user-created process that is NOT repeatable (can_repeat=False).
    It simply sets a flag or data once for each file rowid. If already set,
    it should not be repeated.
    """
    TABLE_CLASS = StoredText
    can_repeat: bool = False

    @classmethod
    def execute(cls, db_path: str, param: Any, output_callback=None) -> str:
        """
        Stores a single run entry in single_run_process_records. Expects
        'param' to be the file's rowid. If there's already an entry for
        that file_id, it won't create another.
        """
        super().execute(db_path, param, output_callback)  # Ensures table creation

        row_id = int(param)
        if output_callback:
            output_callback("Running store text process...\n")

        try:
            conn = get_db_connection(db_path)

            # Check if we already have a record
            existing = conn.execute(
                f"SELECT rowid FROM {StoredText.TABLE_NAME} WHERE file_id = ?",
                (row_id,)
            ).fetchone()

            if existing:
                msg = f"Store text process already executed for file_id={row_id}. Skipping."
                conn.close()
                if output_callback:
                    output_callback(msg + "\n")
                return msg

            # Otherwise, create a new record
            data = {
                "file_id": row_id,
                "some_data": "User-specific single-run data."
            }
            StoredText.insert_record(conn, data)
            conn.close()

            msg = f"Store text process completed for file_id={row_id}."
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in store text process: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
