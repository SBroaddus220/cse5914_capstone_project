# -*- coding: utf-8 -*-

"""
Extracts metadata from files.
"""

# **** IMPORTS ****
import json
import logging
import sqlite3
from PIL import Image, ExifTags
from typing import Any, Dict, Tuple, Optional

from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.file_metadata.file_metadata import FileMetadata
from tagsense.data_structures.data_structures.file_table.file_table import Files

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class ExtractFileMetadataProcess(AppProcess):
    """
    Extracts metadata for a given file type (image, video, document, etc.).
    Additional file type support can be added by extending the _extract_metadata_for_filetype method.
    """
    name: str = "extract_file_metadata"
    input: AppDataStructure = Files
    output: AppDataStructure = FileMetadata

    @classmethod
    def execute(cls, input_data_key: str) -> Tuple[str, Optional[dict]]:
        """
        Main entry point for metadata extraction.
        Resolves the file path from DB, extracts metadata, and inserts
        results into the file metadata table.
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
        # Otherwise, extract metadata
        # Convert file_record to dict. Currently a sqlite3.row object
        file_record = cls.input.read_by_entry_key(input_data_key)
        if not file_record:
            msg = "No matching file record found in database."
            print(msg + "\n")
            return (msg, None)

        file_path: str = file_record["file_path"]
        file_extension: str = file_record["file_extension"].lower()

        # Extract metadata
        metadata_dict = cls._extract_metadata_for_filetype(file_extension, file_path)
        print(f"Extracted metadata: {metadata_dict}\n")

        # Insert into file metadata table
        data = {"metadata": json.dumps(metadata_dict)}
        cls.output.create_entry(
            data=data,
            process=cls,
            input_data_structure=cls.input,
            input_data_key=input_data_key,
        )

        msg = f"{cls.name} process completed for {reference_msg}."
        print(msg + "\n")
        return (msg, data)

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
