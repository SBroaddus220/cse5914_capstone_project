# Below are two example user-created processes. One is repeatable (can_repeat=True),
# the other is not (can_repeat=False). Each has its own table class to store data.

# **** Table Classes ****
import sqlite3
from typing import Dict, Any, Optional

from tagsense.models.base_table import BaseTable

class AppendTextProcessTable(BaseTable):
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


class SingleRunProcessTable(BaseTable):
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


# **** Process Classes ****
import logging
from tagsense.processes.base_process import BaseProcess

logger = logging.getLogger(__name__)

class AppendTextProcess(BaseProcess):
    """
    An example repeatable user-created process that appends text to
    'append_text_process_records'. This can be run multiple times
    for the same file.
    """
    TABLE_CLASS = AppendTextProcessTable
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
            output_callback("Running AppendTextProcess...\n")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Check if we already have a record in append_text_process_records for this file
            existing = conn.execute(
                f"SELECT * FROM {AppendTextProcessTable.TABLE_NAME} WHERE file_id = ?",
                (row_id,)
            ).fetchone()

            new_text = "Appended some user data."
            if existing:
                # If found, append new text
                old_text = existing["appended_text"] or ""
                updated_text = old_text + "\n" + new_text

                AppendTextProcessTable.update_record(
                    conn,
                    existing["rowid"],
                    {"appended_text": updated_text},
                    id_column="rowid"
                )
                msg = f"Appended text to existing record for file_id={row_id}."
            else:
                # Otherwise, create a new record
                data = {"file_id": row_id, "appended_text": new_text}
                AppendTextProcessTable.insert_record(conn, data)
                msg = f"Created new append_text_process_records entry for file_id={row_id}."

            conn.close()
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in AppendTextProcess: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg


class SingleRunProcess(BaseProcess):
    """
    An example user-created process that is NOT repeatable (can_repeat=False).
    It simply sets a flag or data once for each file rowid. If already set,
    it should not be repeated.
    """
    TABLE_CLASS = SingleRunProcessTable
    can_repeat: bool = False

    def execute(self, db_path: str, param: Any, output_callback=None) -> str:
        """
        Stores a single run entry in single_run_process_records. Expects
        'param' to be the file's rowid. If there's already an entry for
        that file_id, it won't create another.
        """
        import sqlite3
        super().execute(db_path, param, output_callback)  # Ensures table creation

        row_id = int(param)
        if output_callback:
            output_callback("Running SingleRunProcess...\n")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Check if we already have a record
            existing = conn.execute(
                f"SELECT rowid FROM {SingleRunProcessTable.TABLE_NAME} WHERE file_id = ?",
                (row_id,)
            ).fetchone()

            if existing:
                msg = f"SingleRunProcess already executed for file_id={row_id}. Skipping."
                conn.close()
                if output_callback:
                    output_callback(msg + "\n")
                return msg

            # Otherwise, create a new record
            data = {
                "file_id": row_id,
                "some_data": "User-specific single-run data."
            }
            SingleRunProcessTable.insert_record(conn, data)
            conn.close()

            msg = f"SingleRunProcess completed for file_id={row_id}."
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in SingleRunProcess: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg
