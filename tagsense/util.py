# -*- coding: utf-8 -*-

"""
Utilities for the application.
"""

# **** IMPORTS ****
import os
import logging
import inspect
import importlib.util
from pathlib import Path
from typing import List, Type

from tagsense import registry

# **** LOGGER ****
logger = logging.getLogger(__name__)

# **** FUNCTIONS ****
def create_divider(name: str, total_width: int = 50) -> str:
    """
    Creates a divider line with the given name centered among dashes.
    
    Args:
        name (str): The text to place in the divider.
        total_width (int): The total width of the divider line.
    
    Returns:
        str: The formatted divider line.
    """
    prefix = "# "
    name_len = len(name)
    max_name_space = total_width - len(prefix)
    if name_len >= max_name_space:
        return f"# {name}"
    space_for_dashes = max_name_space - name_len
    left = space_for_dashes // 2
    right = space_for_dashes - left
    return prefix + ("-" * left) + name + ("-" * right)


def discover_classes(directory: Path, base_class: Type) -> List:
    """
    Recursively discovers any subclasses of a given base class within all .py files in the given directory.

    Args:
        directory (Path): Path to the directory containing potential class modules.
        base_class (Type): The base class to search for subclasses.

    Returns:
        List: Instantiated subclasses of the specified base class.
    """
    discovered_classes = []

    for module_path in directory.rglob("*.py"):
        if module_path.name.startswith("__init__"):
            continue

        module_name = (
            module_path.relative_to(directory)
            .with_suffix("")
            .as_posix()
            .replace("/", ".")
        )

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, base_class) and obj is not base_class:
                    logger.info(f"Discovered {obj.__name__}")
                    discovered_classes.append(obj)

                    if obj.requires_installation:
                        installed = registry.is_installed(obj)
                        logger.info(f"⚠️ {obj.__name__} requires installation. Installed: {installed}")

    registry.register_classes(discovered_classes)


# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
