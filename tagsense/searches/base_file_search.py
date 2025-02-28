# -*- coding: utf-8 -*-

"""
Base foundation for searches.
"""

# **** IMPORTS ****
import sqlite3
from typing import Optional
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget

from tagsense.database import get_db_connection

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
        conn = get_db_connection(db_path)
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

def generate_search_classes(db_path):
    """
    Dynamically generates search classes based on table names.
    
    Args:
        db_path (str): Path to the SQLite database.
    
    Returns:
        dict: A dictionary of {table_name: dynamically_created_class_instance}.
    """
    # Fetch table names from SQLite
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    search_classes = {}

    for table_name in tables:
        # Dynamically create a search class for each table
        class_name = f"{table_name.capitalize()}Search"

        # Define the class dynamically
        search_class = type(
            class_name,
            (FileSearchBase,),
            {"get_sql": lambda self, t=table_name: f"SELECT * FROM {t}"}
        )

        # Store an instance of the class
        search_classes[table_name] = search_class()

    return search_classes


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
