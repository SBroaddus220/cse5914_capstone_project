# -*- coding: utf-8 -*-

"""
Example algorithm to append text data.
"""

# **** IMPORTS ****
import os
import sqlite3
import logging
from typing import Any, Tuple, Optional

from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.data_structures.data_structures.example02_stored_random_text.stored_random_text import StoredRandomText
from tagsense.data_structures.data_structures.file_table.file_table import Files


# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class StoreRandomText(AppProcess):
    """
    An example repeatable user-created process that IS repeatable for any given input.
    Repeated processes must be non-deterministic regarding solely the input data.
    In this case, the stored text is dependent on some randomly generated data.
    """
    name: str = "StoreRandomText"
    input: AppDataStructure = Files
    output: AppDataStructure = StoredRandomText
    deterministic: bool = False

    @classmethod
    def execute(cls, input_data_key: str, output_callback=None) -> Tuple[str, Optional[dict]]:
        """
        Appends text to an existing record or creates a new record.
        """
        if output_callback:
            output_callback("Running append text process...\n")
            
        # ****
        # Create a new record. Doesn't need to check if the process has already been run
        data = {
            "data": f"Random data: {str(os.urandom(8))}"
        }
        cls.output.create_entry(
            data=data,
            process=cls,
            input_data_structure=cls.input,
            input_data_key=input_data_key,
        )

        reference_msg = f"{input_data_key} from {cls.input}"
        msg = f"{cls.name} completed for {reference_msg}."
        if output_callback:
            output_callback(msg + "\n")
        return (msg, data)

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
