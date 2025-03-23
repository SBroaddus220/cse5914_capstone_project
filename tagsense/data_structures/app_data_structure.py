# -*- coding: utf-8 -*-

"""
Application wrapper for data structures.
"""

# **** IMPORTS ****
import os
import json
import hashlib
import sqlite3
import jsonschema
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Tuple 

from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.data_structure import DataStructure

# **** CLASS ****
class AppDataStructure(DataStructure):
    """
    Represents a hashmap data structure for application usage.
    The application incorporates SQLITE table operations for data storage.
    This base class assumes a single SQLITE table is referenced that perfectly maps to the data structure.
    """

    # **** CLASS ATTRIBUTES ****
    table: SQLITETable
    conn: sqlite3.Connection  # Remember to dynamically set this in the main application
    
    # **** DUNDER METHODS ****
    def __init_subclass__(cls, **kwargs):
        """
        Enforce that every subclass defines a valid SQLITETable.
        """
        super().__init_subclass__(**kwargs)

        # Set the name to the table name
        cls.name = cls.table.table_name
        
        # Generate UID once per subclass
        cls.uid = cls.get_uid()
        
        # Verify subclass attributes
        cls.verify()

        if not hasattr(cls, 'table') or not issubclass(cls.table, SQLITETable):
            raise TypeError(f"{cls.__name__} must define a `table` attribute that is a subclass of SQLITETable.")

    # **** CLASS METHODS ****
    @classmethod
    def get_uid(cls) -> str:
        """Generate a unique identifier for this data structure."""
        return cls.table.table_name
    
    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the data structure.

        Args:
            conn (sqlite3.Connection): SQLite database connection.
        """
        super().initialize()
        cls.table.create_table(cls.conn)
        cls.table.verify_table(cls.conn)
        
    @classmethod
    def verify(cls):
        """Ensure that required attributes are correctly defined in subclasses.
        
        Raises:
            TypeError: If a required attribute is missing.
        """
        required_attrs = ["name", "uid", "table"]
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(f"Class {cls.__name__} must define attribute '{attr}'.")

    @classmethod
    def create_entry(cls, data: Dict[str, Any], process: Any, input_data_structure: Union['AppDataStructure', None], input_data_key: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Create a new entry in the referenced table.

        Args:
            data (Dict[str, Any]): Data to insert.
            process (Any): The process that generated the data.
            input_data_structure (AppDataStructure | None): The data structure that the input data conforms to.
            input_data_key (str): The key of the input data.

        Returns:
            Tuple[Any, Dict[str, Any]]: The entry key and the data that was inserted.
        """
        if not hasattr(process, 'get_uid'):
            raise ValueError("Process must implement 'get_uid()' to create an entry.")
        
        if input_data_structure and not hasattr(input_data_structure, 'get_uid'):
            raise ValueError("Input data structure must implement 'get_uid()' to create an entry.")

        # Ensure metadata is included
        entry_key = cls._generate_new_key()
        data["entry_key"] = entry_key
        data["process_uid"] = process.get_uid()
        data["input_structure_uid"] = input_data_structure.get_uid() if input_data_structure else None
        data["input_data_key"] = input_data_key
    
        # Ensure data keys match the table's required columns (except auto-incremented rowid)
        required_fields = cls.table.required_columns - {"rowid"}
        missing_fields = required_fields - data.keys()
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Insert the data
        cls.table.insert_record(cls.conn, data)

        return entry_key, data
    
    @classmethod
    def read(cls, column_name: str, value: str) -> Optional[Dict[str, Any]]:
        """
        Read data from the referenced table.

        Args:
            column_name (str): The column name to search.
            value (str): The value for the data.

        Returns:
            Optional[Dict[str, Any]]: The retrieved data, if found.
        """
        existing_record = cls.conn.execute(
            f"SELECT * FROM {cls.table.table_name} WHERE {column_name} = ?",
            (value,)
        ).fetchone()
        return existing_record
    
    @classmethod
    def fetch_entry_key_from_entry(cls, entry: Dict[str, Any]) -> str:
        """Fetch the entry key from an entry."""
        return entry.get("entry_key", None)

    @classmethod
    def fetch_process_uid_from_entry(cls, entry: Dict[str, Any]) -> str:
        return entry["process_uid"]
    
    @classmethod
    def fetch_input_data_structure_uid_from_entry(cls, entry: Dict[str, Any]) -> 'AppDataStructure':
        return entry["input_structure_uid"]
    
    @classmethod
    def fetch_input_data_key_from_entry(cls, entry: Dict[str, Any]) -> str:
        return entry["input_data_key"]

    @classmethod
    def read_by_entry_key(cls, key: str) -> Optional[Dict[str, Any]]:
        existing_record = cls.conn.execute(
            f"SELECT * FROM {cls.table.table_name} WHERE entry_key = ?",
            (key,)
        ).fetchone()
        return existing_record

    @classmethod
    def read_by_input_key(cls, key: str) -> Optional[Dict[str, Any]]:
        existing_record = cls.conn.execute(
            f"SELECT * FROM {cls.table.table_name} WHERE input_data_key = ?",
            (key,)
        ).fetchone()
        return existing_record

    @classmethod
    def update(cls, row_id: int, updates: Dict[str, Any]) -> None:
        """
        Update the referenced table with the provided data.

        Args:
            row_id (int): Row ID to update.
            updates (Dict[str, Any]): Updated data fields.

        Raises:
            ValueError: If updated data does not conform to the schema.
        """
        existing_data = cls.read(cls.conn, row_id)
        if not existing_data:
            raise KeyError(f"No entry found with row ID '{row_id}' in {cls.name}.")

        existing_data.update(updates)
        if not cls.verify_structure(existing_data):
            raise ValueError(f"Updated data does not conform to {cls.name} format.")

        cls.table.update_record(cls.conn, row_id, updates)

    @classmethod
    def delete(cls, row_id: int) -> None:
        """
        Delete an entry from the referenced table.

        Args:
            row_id (int): Row ID to delete.
        """
        cls.table.delete_record(cls.conn, row_id)

    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        """
        List all data from the referenced table.

        Args:
            conn (sqlite3.Connection): SQLite database connection.

        Returns:
            List[Dict[str, Any]]: A list of records.
        """
        return cls.table.fetch_all(cls.conn)

    @classmethod
    def fetch_all_entry_keys(cls):
        """Fetch all keys from the data structure."""
        entry_keys = []
        for entry in cls.list_all():
            entry_keys.append(cls.fetch_entry_key_from_entry(entry))
        return entry_keys


if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
