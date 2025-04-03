# -*- coding: utf-8 -*-

"""
Base foundation for searches in the application.
"""

# **** IMPORTS ****
import os
import logging
from PIL import Image
from PIL.Image import Image as PILImage
import sqlite3

from tagsense.searches.search import Search
from tagsense.registry import detected_data_structures
from tagsense.data_structures.data_structure import DataStructure
from tagsense.data_structures.data_structures.file_table.file_table import Files

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class AppSearch(Search):
    """Search wrapped for application usage."""
    
    @classmethod
    def get_help_text(cls) -> str:
        return "No help text available."
    
    @classmethod
    def generate_thumbnail(cls, result: dict, thumbnail_size=(300, 300)) -> Image.Image | None:
        """
        Attempts to find an associated file and generate a thumbnail.
        
        Args:
            result (dict): A dictionary containing a "file_path" key or references a file.
            thumbnail_size (tuple, optional): The size of the generated thumbnail.
        
        Returns:
            Image.Image | None: The generated thumbnail image, or None if the file is invalid.
        """
        file_path = result.get("file_path")
        
        # Attempt to find a file reference in the input data structure
        if not file_path:
            # Fetch input data structure uid from result
            input_data_structure_uid = cls.data_structure.fetch_input_data_structure_uid_from_entry(result)

            input_data_structure: DataStructure = None
            if input_data_structure_uid:
                # Find the corresponding data structure
                for detected_data_structure in detected_data_structures:
                    detected_data_structure: DataStructure
                    if detected_data_structure.uid == input_data_structure_uid:
                        input_data_structure = detected_data_structure

            if input_data_structure:
                # Fetch input data key from result
                input_data_key = cls.data_structure.fetch_input_data_key_from_entry(result)
                if input_data_key:
                    input_data = dict(input_data_structure.read_by_entry_key(input_data_key))
                    if input_data:
                        file_path = input_data.get("file_path")
            
        if file_path and os.path.exists(file_path):
            try:
                with Image.open(file_path) as img:
                    img = img.convert("RGBA")  # or "RGBA" if transparency needed
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    return img.copy()
            except Exception as e:
                logger.warning(f"Error generating thumbnail for {file_path}: {e}")
        
        return super().generate_thumbnail(result, thumbnail_size)
        
    
# **** FUNCTIONS ****
def generate_search_classes(conn: sqlite3.Connection, data_structures: list[DataStructure]) -> dict[str, AppSearch]:
    """
    Dynamically generates search classes based on table names.
    
    Args:
        conn (sqlite3.Connection): SQLite database connection.
    
    Returns:
        dict: A dictionary of {DataStructure.name: AppSearch}.
    """
    search_classes = {}

    for data_structure in data_structures:
        search_class = type(
            data_structure.name,  # Dynamically assign class name
            (AppSearch,),  # Base class
            {
                "name": data_structure.name,  # Explicitly set the class attribute
                "data_structure": data_structure
            }
        )
        search_classes[data_structure.name] = search_class
    
    return search_classes


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
