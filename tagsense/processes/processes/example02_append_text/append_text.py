# -*- coding: utf-8 -*-

"""
Example algorithm to append text data.
"""

# **** IMPORTS ****
import logging
from typing import Any

from tagsense.processes.base_process import BaseProcess
from tagsense.models.data_structures.example02_appended_text.appended_text import AppendedText

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class AppendText(BaseProcess):
    """
    An example repeatable user-created process that appends text to
    'append_text_process_records'. This can be run multiple times
    for the same file.
    """
    TABLE_CLASS = AppendedText
    can_repeat: bool = True

    def execute(self, db_path: str, param: Any, output_callback=None) -> str:
        """
        Append some text for the given file. Expects 'param' to be the
        file's rowid. If there's no existing record, create one; if
        one exists, append more text.
        """
        import sqlite3
        super().execute(db_path, param, output_callback)  # Ensures table creation

        row_id = int(param)
        if output_callback:
            output_callback("Running append text process...\n")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Check if we already have a record in append_text_process_records for this file
            existing = conn.execute(
                f"SELECT * FROM {AppendedText.TABLE_NAME} WHERE file_id = ?",
                (row_id,)
            ).fetchone()

            new_text = "Appended some user data."
            if existing:
                # If found, append new text
                old_text = existing["appended_text"] or ""
                updated_text = old_text + "\n" + new_text

                AppendedText.update_record(
                    conn,
                    existing["rowid"],
                    {"appended_text": updated_text},
                    id_column="rowid"
                )
                msg = f"Appended text to existing record for file_id={row_id}."
            else:
                # Otherwise, create a new record
                data = {"file_id": row_id, "appended_text": new_text}
                AppendedText.insert_record(conn, data)
                msg = f"Created new append_text_process_records entry for file_id={row_id}."

            conn.close()
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in append text process: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
