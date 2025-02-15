# -*- coding: utf-8 -*-

"""
Search that shows core metadata for all files.
"""

# **** IMPORTS ****
from tagsense.searches.base_file_search import FileSearchBase

# **** CLASS ****
class AllFilesSearch(FileSearchBase):
    """Concrete example that selects all data from file_table."""
    
    def get_sql(self) -> str:
        return "SELECT * FROM file_table"

class AllFileMetadataSearch(FileSearchBase):
    """Concrete example that selects all data from file_table."""
    
    def get_sql(self) -> str:
        return "SELECT * FROM file_core_metadata"

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
