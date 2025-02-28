# -*- coding: utf-8 -*-

"""
Search that returns only the even rows from the database.
"""

# **** IMPORTS ****
from tagsense.searches.base_file_search import FileSearchBase

# **** CLASSES ****
class EvenRows(FileSearchBase):
    """Gets only the even rows from the database."""
    
    def get_sql(self) -> str:
        return "SELECT * FROM file_table WHERE rowid % 2 = 0"

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")