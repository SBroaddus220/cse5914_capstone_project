# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** IMPORTS ****
import logging
from typing import Any

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class BaseProcess:
    """
    Base class for file processes.
    Each process can optionally define a TABLE_CLASS that inherits from BaseTable
    for storing process-specific data. The create_tables method will handle
    initialization of that table, if defined.
    """

    TABLE_CLASS = None  # Subclasses can override with a BaseTable subclass
    can_repeat: bool = False
    requires_installation: bool = False

    @classmethod
    def execute(cls, db_path: str, param: Any, output_callback=None) -> Any:
        """
        Default execute method. Subclasses typically override this
        to perform their specific actions. This method can still
        be called via super() to ensure table creation if needed.

        Args:
            db_path (str): Path to the SQLite database.
            param (Any): Could be the original file path or a database rowid,
                depending on the subclass's usage.
            output_callback (Callable[[str], None], optional): 
                A function for streaming output messages.

        Returns:
            Any: A message or result of the process (string, rowid, etc.).
        """
        import sqlite3
        if cls.TABLE_CLASS is not None:
            conn = sqlite3.connect(db_path)
            cls.create_tables(conn)
            conn.close()
        if output_callback:
            output_callback(f"{cls.__name__} executed.\n")
        return f"{cls.__name__} executed."

    @classmethod
    def create_tables(cls, conn) -> None:
        """
        Creates the table for this process if TABLE_CLASS is defined.
        
        Args:
            conn (sqlite3.Connection): The SQLite connection.
        """
        if cls.TABLE_CLASS is not None:
            cls.TABLE_CLASS.create_table(conn)

    @classmethod
    def install(cls) -> None:
        """
        Subclasses that require installation should override this method.
        """
        if cls.requires_installation:
            raise NotImplementedError(f"{cls.__name__} requires installation, but no method is defined.")

    def __new__(cls, *args, **kwargs):
        raise TypeError("This class cannot be instantiated.")


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
