# -*- coding: utf-8 -*-

"""
Processes for basic file preprocessing.
"""

# **** IMPORTS ****
import os
import json
import logging
import hashlib
import shutil
import sqlite3
from PIL import Image, ExifTags
from datetime import datetime
from typing import Dict, Any, Optional

from tagsense.config import CLIENT_FILES_DIR
from tagsense.processes.base_process import BaseProcess
from tagsense.models.file_table import FileTable
from tagsense.models.file_core_metadata import FileCoreMetadataTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class FilePreprocessing(BaseProcess):
    """
    Hashes a file and records it and its core metadata in the database.
    """
    TABLE_CLASS = FileTable
    can_repeat: bool = True

    def execute(self, db_path: str, param: Any, output_callback=None) -> int:
        import sqlite3
        from tagsense.models.file_table import FileTable

        super().execute(db_path, param, output_callback)
        file_path = str(param)

        if output_callback:
            output_callback("Executing initial file preprocessing...\n")

        try:
            # Use row_factory so we can reference columns by name
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            md5_hash = self._calculate_md5(file_path)
            if output_callback:
                output_callback(f"Calculated MD5: {md5_hash}\n")

            existing = conn.execute(
                f"SELECT * FROM {FileTable.TABLE_NAME} WHERE md5_hash = ?",
                (md5_hash,)
            ).fetchone()

            # Gather the "new" data to potentially append
            import os
            from datetime import datetime

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

            from tagsense.config import CLIENT_FILES_DIR
            import shutil

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


class ExtractFileMetadataProcess(BaseProcess):
    """
    Extracts metadata for a given file type (image, video, document, etc.).
    Currently implemented to handle images. Additional file type support
    can be added by extending the _extract_metadata_for_filetype method.
    """
    TABLE_CLASS = FileCoreMetadataTable
    can_repeat: bool = False

    def execute(self, db_path: str, param: Any, output_callback=None) -> str:
        """
        Main entry point for metadata extraction. Expects a rowid (int).
        Resolves the file path from DB, extracts metadata, and inserts
        results into FileCoreMetadataTable.

        Args:
            db_path (str): The path to the SQLite database.
            param (Any): Expects the rowid of the file record.
            output_callback (Callable[[str], None], optional): Callback for streaming output.

        Returns:
            str: A message describing the result of the process.
        """
        super().execute(db_path, param, output_callback)  # Ensures table creation if needed
        row_id = int(param)

        if output_callback:
            output_callback("Extracting core metadata...\n")

        try:
            conn = sqlite3.connect(db_path)

            # Fetch the file record using row_id
            file_record = FileTable.fetch_record(conn, row_id, "rowid")
            if not file_record:
                msg = "No matching file record found in database."
                if output_callback:
                    output_callback(msg + "\n")
                conn.close()
                return msg

            file_id = file_record["rowid"]
            file_path = file_record["file_path"]
            file_extension = file_record["file_extension"].lower()

            # Extract metadata
            metadata_dict = self._extract_metadata_for_filetype(file_extension, file_path)
            if output_callback:
                output_callback(f"Extracted metadata: {metadata_dict}\n")

            # Insert into FileCoreMetadataTable
            FileCoreMetadataTable.insert_record(conn, {
                "file_id": file_id,
                "metadata": json.dumps(metadata_dict)
            })
            conn.close()

            msg = f"Metadata extracted and inserted for file_id: {file_id}"
            if output_callback:
                output_callback(msg + "\n")
            return msg

        except Exception as e:
            err_msg = f"Error in ExtractFileMetadataProcess: {e}"
            logger.error(err_msg)
            if output_callback:
                output_callback(err_msg + "\n")
            return err_msg


    def _fetch_fundamental_record(
        self, conn: sqlite3.Connection, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches the fundamental file record by matching on file_path.

        Args:
            conn (sqlite3.Connection): The SQLite database connection.
            file_path (str): The path to the file.

        Returns:
            Optional[Dict[str, Any]]: The file record if found, otherwise None.
        """
        sql = f"""
        SELECT *
        FROM {FileTable.TABLE_NAME}
        WHERE file_path = ?
        LIMIT 1
        """
        cursor = conn.execute(sql, (file_path,))
        row = cursor.fetchone()
        if row is None:
            return None
        desc = [d[0] for d in cursor.description]
        return dict(zip(desc, row))

    def _extract_metadata_for_filetype(self, file_extension: str, file_path: str) -> Dict[str, Any]:
        """
        Dispatch method to extract metadata based on file extension.

        Args:
            file_extension (str): The file extension (including '.').
            file_path (str): The path to the file.

        Returns:
            Dict[str, Any]: A dictionary containing extracted metadata.
        """
        # You could expand this with more elif statements for different file types
        if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]:
            return self._extract_image_metadata(file_path)
        else:
            # Placeholder: no specialized extraction
            return {"info": "No specialized metadata extraction for this file type."}

    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        metadata_dict: Dict[str, Any] = {}
        try:
            img = Image.open(file_path)
            width, height = img.size

            color_depth = None
            if img.mode == "RGB":
                color_depth = 24
            elif img.mode == "RGBA":
                color_depth = 32
            elif img.mode == "L":
                color_depth = 8

            dpi = img.info.get("dpi", (None, None))
            color_profile = img.info.get("icc_profile", None)
            compression_profile = img.info.get("compression", None)

            exif_data = {}
            if hasattr(img, "_getexif") and img._getexif():
                raw_exif = img._getexif()
                for tag_id, value in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    # Convert any type that isn't natively JSON-serializable to string
                    exif_data[tag_name] = str(value)

            metadata_dict = {
                "dimensions": f"{width}x{height}",
                "color_depth": color_depth,
                "color_profile": bool(color_profile),
                "dpi": dpi,
                "compression_profile": compression_profile
            }
            
            exif_data = {}
            if hasattr(img, "_getexif") and img.getexif():
                raw_exif = img.getexif()
                for tag_id in raw_exif:
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    data = raw_exif.get(tag_id)
                    if isinstance(data, bytes):
                        data = data.decode()
                    # Convert any type that isn't natively JSON-serializable to string
                    exif_data[tag_name] = str(data)

                metadata_dict["exif"] = exif_data

        except Exception as e:
            logger.error(f"Failed to extract image metadata: {e}")
            metadata_dict = {"error": f"Could not extract image metadata: {e}"}

        return metadata_dict



# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
