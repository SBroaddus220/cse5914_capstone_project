# -*- coding: utf-8 -*-

"""
Utilities for the application.
"""

# **** IMPORTS ****
import logging

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

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
