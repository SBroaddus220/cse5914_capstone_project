# -*- coding: utf-8 -*-

"""
Base foundation for all data structures.
"""

# **** IMPORTS ****
import os
import json
import hashlib
import jsonschema
from pathlib import Path
from typing import Any, Dict, Optional

# **** CLASS ****
class DataStructure:
    """
    Represents a hashmap data structure.

    Attributes:
        name (str | None): An optional human-readable name for the data structure.
        _storage (Dict[str, Any]): A dictionary to store data.
    """
    # **** ATTRIBUTES ****
    name: str | None = None
    _storage: Dict[str, Any] = {}
    json_schema: Dict[str, Any] = {}
    uid: str
    
    # **** DUNDER METHODS ****
    def __new__(cls, *args, **kwargs):
        """
        Prevents instantiation.
        These classes are designed to represent unique forms of data. 
        Instantiation doesn't make sense as any instance would be a change to the structure.
        """
        if cls is DataStructure:
            raise TypeError(f"{cls.__name__} cannot be instantiated directly.")
        return super().__new__(cls)

    @classmethod
    def __repr__(cls):
        return f"DataStructure({cls.name}, uid={cls.get_uid()[:8]})"
    
    # **** CLASS METHODS ****
    @classmethod
    def initialize(cls) -> None:
        """Initialize the data structure."""
        cls.uid = cls.get_uid()
    
    @classmethod
    def get_uid(cls) -> str:
        """Generate a unique identifier for this data structure."""
        raise NotImplementedError(f"{cls.__name__} must implement 'get_uid()'.")

    @classmethod
    def load_json_schema(cls, file_path: Path) -> None:
        """
        Load a JSON schema from a file and assign it to the class attribute.

        Args:
            file_path (Path): Path to the JSON schema file.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                cls.json_schema = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON schema file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON schema format: {e}")
    
    @classmethod
    def verify_structure(cls, data: Any) -> bool:
        """
        Verify if the given data conforms to the JSON schema.

        Args:
            data (Any): The data to validate.

        Returns:
            bool: True if valid, False otherwise.

        Raises:
            ValueError: If data does not conform to the schema.
        """
        try:
            jsonschema.validate(instance=data, schema=cls.json_schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Invalid data structure: {e.message}")

    @classmethod
    def _generate_new_key(cls) -> str:
        """Generate a new unique key for the data structure."""
        # Generate a random hash
        hash = hashlib.sha256(os.urandom(128)).hexdigest()
        while cls.read_by_entry_key(key=hash):  # Ensure the key is unique
            hash = hashlib.sha256(os.urandom(128)).hexdigest()
        return hash

    # Can have any args/kwargs. This is just an example.
    @classmethod
    def create_entry(cls, data: Any, process: Any, input_data_structure: 'DataStructure', input_data_key: str) -> Optional[Any]:
        """Create a new entry in the data structure.

        Args:
            data (Any): The data to store.
            process (Process): The process that generated the data.
            input_data_structure (DataStructure): The data structure that the input data conforms to.
            input_data_key (str): The key of the input data.

        Raises:
            ValueError: If the data does not conform to the structure.

        Returns:
            Any: Can be a key or a message.
        """
        if not cls.verify_structure(data):
            raise ValueError(f"Invalid data for {cls.name} format.")
        key = cls._generate_new_key()
        cls._storage[key] = {}
        cls._storage[key]["data"] = data
        cls._storage[key]["process"] = process
        cls._storage[key]["input_data_structure"] = input_data_structure
        cls._storage[key]["input_data_key"] = input_data_key
        return key
    
    @classmethod
    def fetch_entry_key_from_entry(cls, entry: Dict[str, Any]) -> str:
        """Fetch the entry key from an entry."""
        return next((k for k, v in cls._storage.items() if v["data"] == entry), None)

    @classmethod
    def fetch_process_uid_from_entry(cls, entry: Dict[str, Any]) -> str:
        """Fetch the process UID from an entry."""
        return cls._storage[cls.fetch_entry_key_from_entry(entry)]["process"].uid
    
    @classmethod
    def fetch_input_data_structure_uid_from_entry(cls, entry: Dict[str, Any]) -> str:
        """Fetch the input data structure from an entry."""
        return cls._storage[cls.fetch_entry_key_from_entry(entry)]["input_data_structure"]
    
    @classmethod
    def fetch_input_data_key_from_entry(cls, entry: Dict[str, Any]) -> str:
        """Fetch the input data key from an entry."""
        return cls._storage[cls.fetch_entry_key_from_entry(entry)]["input_data_key"]
        
    @classmethod
    def read_by_entry_key(cls, key: str) -> Optional[Any]:
        """Read data from data structure."""
        return cls._storage.get(key)["data"] if key in cls._storage else None

    @classmethod
    def read_by_input_key(cls, key: str) -> Optional[Any]:
        """Read data from data structure."""
        # Gets key that has the input key
        entry_key = next((k for k, v in cls._storage.items() if v["input_data_key"] == key), None)
        return cls.read_by_entry_key(entry_key)

    @classmethod
    def update(cls, key: str, updates: Dict[str, Any]) -> Optional[Any]:
        """Update an existing entry."""
        if key not in cls._storage:
            raise KeyError(f"No entry found with key '{key}' in {cls.name}.")
        cls._storage[key["data"]].update(updates)  # Update stored data
        if not cls.verify_structure(cls._storage[key["data"]]):  # Revalidate structure
            raise ValueError(f"Updated data does not conform to {cls.name} format.")
        return cls._storage[key["data"]]

    @classmethod
    def delete(cls, key: str) -> bool:
        """Delete an entry from the data structure.

        Args:
            key (str): Key of the entry to delete.

        Returns:
            bool: True if the entry was deleted, False otherwise.
        """
        return cls._storage.pop(key["data"], None) is not None

    @classmethod
    def list_all(cls) -> Dict[str, Any]:
        """List all stored data unless an external database is in use."""
        return cls._storage

    @classmethod
    def fetch_all_entry_keys(cls) -> list:
        """Fetch all keys from the data structure."""
        return list(cls._storage.keys())


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
