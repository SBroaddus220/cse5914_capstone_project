# -*- coding: utf-8 -*-

"""
Application wrapper for processes.
"""

# **** IMPORTS ****
import logging
import sqlite3
from typing import Callable, Any, Tuple, Optional

from tagsense import registry
from tagsense.processes.process import Process
from tagsense.data_structures.app_data_structure import AppDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class AppProcess(Process):
    """
    Process wrapped for application usage. This keeps the process from being tied to the application logic.
    """

    # **** CLASS VARIABLES ****
    requires_installation: bool = False
    conn: sqlite3.Connection  # Remember to dynamically set this in the main application

    def __init_subclass__(cls, **kwargs):
        """
        Ensures `uid` is set exactly once when the subclass is defined.
        """
        super().__init_subclass__(**kwargs)

        # Validate subclass attributes before UID generation
        cls.verify()

    # **** CLASS METHODS ****
    @classmethod
    def get_uid(cls) -> str:
        """Generate a unique identifier for this process.

        Returns:
            str: The unique identifier.
        """
        return cls.name
    
    @classmethod
    def install(cls) -> None:
        """Install the process."""
        registry.mark_process_as_installed(cls)
        cls.output.initialize()

    @classmethod
    def verify(cls):
        """Ensure that required attributes are correctly defined in subclasses.
        
        Raises:
            TypeError: If a required attribute is missing.
        """
        required_attrs = ["name", "input", "output", "deterministic", "uid"]
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(f"Class {cls.__name__} must define attribute '{attr}'.")


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
