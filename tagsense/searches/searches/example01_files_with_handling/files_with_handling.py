# -*- coding: utf-8 -*-

"""
Search that returns only the even rows from the database.
"""

# **** IMPORTS ****
import os
from PIL import Image

from tagsense.searches.app_search import AppSearch
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.file_table.file_table import Files

# **** CLASSES ****
class FilesWithHandling(AppSearch):
    """Search that can handle natural language and explicit queries with basic logic."""
    name: str = "Files With Handling"
    data_structure: AppDataStructure = Files
    
    @classmethod
    def handle_explicit_query(cls, query: str) -> list[dict]:
        """Handles an explicit query."""
        print("Hi! I'm handling an explicit query.")
        return [{"message": "I'm handling an explicit query."}]

    @classmethod
    def handle_natural_language_query(cls, query: str) -> list[dict]:
        """Handles a natural language query."""
        print("Hi! I'm handling a natural language query.")
        return [{"message": "I'm handling a natural language query."}]

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")