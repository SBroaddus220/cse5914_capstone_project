# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** IMPORTS ****
import logging
import inspect
import hashlib
from typing import Any, Union, Callable, Tuple, Optional

from tagsense.data_structures.data_structure import DataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASS ****
class Process:
    """
    Represents any functional transformation.

    Attributes:
        name (str | None): An optional human-readable name for the process.
        input (DataStructure): The data structure that this process expects.
        output (DataStructure): The data structure that this process produces.
        deterministic (bool): Whether the process always produces the same output for the same input.
          - Determines if a process can be repeated. A process should not run if it has already been run and is not repeatable.
        uid (str): A unique identifier for this process.
    """
    # **** ATTRIBUTES ****
    name: Union[str, None] = None
    input: DataStructure
    output: DataStructure
    deterministic: bool = True
    uid: str

    # **** DUNDER METHODS ****
    def __new__(cls, *args, **kwargs):
        """
        Prevents instantiation.
        These classes are designed to represent unique forms of processes.
        Instantiation doesn't make sense as any instance would be a change to the process.
        """
        if cls is Process:
            raise TypeError(f"{cls.__name__} cannot be instantiated directly.")
        return super().__new__(cls)    

    @classmethod
    def __repr__(cls):
        return f"Process({cls.name}, deterministic={cls.deterministic}, uid={cls.get_uid()[:8]})"

    def __init_subclass__(cls, **kwargs):
        """
        Ensures `uid` is set exactly once when the subclass is defined.
        """
        super().__init_subclass__(**kwargs)

        # Generate UID once per subclass
        cls.uid = cls.get_uid()

    # **** CLASS METHODS ****
    @classmethod
    def get_uid(cls) -> str:
        """Generate a unique identifier for this process.

        Returns:
            str: The unique identifier.
        """
        return cls.name

    @classmethod
    def execute(cls, input_data_key: str) -> Tuple[Any, Optional[dict]]:
        """Execute the process.

        Args:
            input_data_key (str): The key of the input data.

        Returns:
            Tuple[Any, Optional[dict]]: Message from the process and dictionary of processed data if successful.
        """
        raise NotImplementedError(f"{cls.__name__} must implement 'execute'.")

    @classmethod
    def verify(cls):
        """Ensure that required attributes are correctly defined in subclasses.
        
        Raises:
            TypeError: If a required attribute is missing.
        """
        required_attrs = ["name", "inputs", "outputs", "deterministic", "uid"]
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(f"Class {cls.__name__} must define attribute '{attr}'.")


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
