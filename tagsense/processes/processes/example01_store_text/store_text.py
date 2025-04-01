# -*- coding: utf-8 -*-

"""
Example algorithm to store text data.
"""

# **** IMPORTS ****
import sqlite3
import logging
from typing import Tuple, Optional

from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.example01_stored_text.stored_text import StoredText
from tagsense.data_structures.data_structures.file_table.file_table import Files

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class StoreText(AppProcess):
    """
    An example user-created process that is NOT repeatable for any given input.
    """
    name: str = "store_text"
    input: AppDataStructure = Files
    output: AppDataStructure = StoredText

    @classmethod
    def execute(cls, input_data_key: str) -> Tuple[str, Optional[dict]]:
        """
        Stores a single run entry.
        """
        print(f"Running {cls.name}...\n")

        # ****
        # Check if the process has already been run
        existing = cls.output.read_by_input_key(input_data_key)
        reference_msg = f"{input_data_key} from {cls.input.name}"
        if existing:
            msg = f"{cls.name} already executed for {reference_msg}. Skipping."
            print(msg + "\n")
            return (msg, None)

        # ****
        # Otherwise, create a new record
        data = {
            "data": "User-specific single-run data."
        }
        cls.output.create_entry(
            data=data,
            process=cls,
            input_data_structure=cls.input,
            input_data_key=input_data_key,
        )

        msg = f"{cls.name} completed for {reference_msg}."
        print(msg + "\n")
        return (msg, data)
    
# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
