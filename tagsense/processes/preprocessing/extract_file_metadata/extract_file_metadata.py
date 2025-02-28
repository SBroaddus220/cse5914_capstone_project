# -*- coding: utf-8 -*-

"""
Extracts metadata from files.
"""

# **** IMPORTS ****
import json
import logging
import sqlite3
from PIL import Image, ExifTags
from typing import Any, Dict, Optional

from tagsense.processes.base_process import BaseProcess
from tagsense.models.data_structures.file_table.file_table import FileTable
from tagsense.models.data_structures.file_metadata.file_metadata import FileMetadata


# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class ExtractFileMetadataProcess(BaseProcess):
    """
    Extracts metadata for a given file type (image, video, document, etc.).
    Currently implemented to handle images. Additional file type support
    can be added by extending the _extract_metadata_for_filetype method.
    """
    TABLE_CLASS = FileMetadata
    can_repeat: bool = False

    @classmethod
    def execute(cls, db_path: str, param: Any, output_callback=None) -> str:
        """
        Main entry point for metadata extraction. Expects a rowid (int).
        Resolves the file path from DB, extracts metadata, and inserts
        results into the file metadata table.

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
            metadata_dict = cls._extract_metadata_for_filetype(file_extension, file_path)
            if output_callback:
                output_callback(f"Extracted metadata: {metadata_dict}\n")

            # Insert into file metadata table
            FileMetadata.insert_record(conn, {
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


    @classmethod
    def _fetch_fundamental_record(
        cls, conn: sqlite3.Connection, file_path: str
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

    @classmethod
    def _extract_metadata_for_filetype(cls, file_extension: str, file_path: str) -> Dict[str, Any]:
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
            return cls._extract_image_metadata(file_path)
        else:
            # Placeholder: no specialized extraction
            return {"info": "No specialized metadata extraction for this file type."}

    @classmethod
    def _extract_image_metadata(cls, file_path: str) -> Dict[str, Any]:
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
    raise Exception("This script is not meant to be run directly.")
