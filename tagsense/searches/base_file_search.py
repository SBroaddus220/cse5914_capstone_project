# -*- coding: utf-8 -*-

"""
Base foundation for searches.
"""

# **** IMPORTS ****
from typing import Optional
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget

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

    def get_left_sidebar_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """
        Returns an optional QWidget for the left sidebar, if this search requires input fields.
        
        Args:
            parent (Optional[QWidget]): The parent widget for the sidebar.
        
        Returns:
            Optional[QWidget]: The custom widget or None.
        """
        return None

    def get_help_text(self) -> str:
        """
        Returns help text for the 'Info' button describing this search.
        
        Returns:
            str: A message explaining how to use this search (if needed).
        """
        return "No additional help for this search."


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
