# -*- coding: utf-8 -*-

"""
Foundational utility data structure for manual input.
"""

# **** IMPORTS ****
import logging
from typing import Any, Optional

from tagsense.data_structures.data_structure import DataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class ManualDataStructure(DataStructure):
    """Memory-based data structure designed to encompass any manual input data or serve as a placeholder for null data."""

    # **** ATTRIBUTES ****
    name: str = "Manual"
    
    # **** CLASS METHODS ****
    @classmethod
    def get_uid(cls):
        return cls.name

    @classmethod
    def verify_structure(cls, data: Any) -> bool:
        """Data cannot be empty."""
        return data is not None
    
    @classmethod
    def create_entry(cls, data: Any) -> Optional[Any]:
        if not cls.verify_structure(data):
            logger.error(f"Data is empty.")
            return None
        key = cls._generate_new_key()
        cls._storage[key] = {}
        cls._storage[key]["data"] = data
        return key
    
# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be executed directly.")
    