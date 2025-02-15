# -*- coding: utf-8 -*-

"""
Base foundation for searches.
"""

# **** IMPORTS ****
from abc import ABC, abstractmethod

# **** CLASS ****
class FileSearchBase(ABC):
    """Abstract base class for SQL-based file searches."""
    
    @abstractmethod
    def get_sql(self) -> str:
        """Returns the SQL query string."""
        pass

    def fetch_results(self, db_path: str) -> list[dict]:
        """
        Executes the query on the specified database and returns the results as a list of dicts.

        Args:
            db_path (str): Path to the SQLite database.
        
        Returns:
            list[dict]: List of rows as dictionaries.
        """
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(self.get_sql()).fetchall()
        conn.close()
        return [dict(row) for row in rows]

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
