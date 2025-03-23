# -*- coding: utf-8 -*-

"""
Utilities for the application.
"""

# **** IMPORTS ****
import re
import logging
import inspect
import importlib.util
from pathlib import Path
from collections import deque
from typing import List, Type

from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtWidgets import QTableWidget

# **** LOGGER ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class QueryValidator:
    """
    Class to validate and process complex search queries.

    Methods:
    - validate_query(query): Validates entire query syntax.
    - find_queries(text): Finds all valid query matches in a given text and groups tags within each match.
    - validate_tag(tag): Validates an individual tag.
    """

    TAG_REGEX = r"-?\w+"
    GROUP_REGEX = rf"-?\(\s*(?:{TAG_REGEX}(?:\s+(?:and|or)?\s*{TAG_REGEX})+)\s*\)"
    ELEMENT_REGEX = rf"(?:{GROUP_REGEX}|{TAG_REGEX})"
    OPERATOR_REGEX = r"(?:and|or)"

    QUERY_PATTERN = re.compile(
        rf"{ELEMENT_REGEX}(?:\s+(?:{OPERATOR_REGEX}\s+)?{ELEMENT_REGEX})*",
        re.VERBOSE | re.IGNORECASE,
    )

    TAG_PATTERN = re.compile(r"^-?\w+$")

    TAG_SEARCH_PATTERN = re.compile(TAG_REGEX)

    @classmethod
    def validate_query(cls, query: str) -> bool:
        """Validate entire query syntax."""
        full_query_pattern = re.compile(
            rf"^\s*{cls.QUERY_PATTERN.pattern}\s*$", re.VERBOSE | re.IGNORECASE
        )
        return bool(full_query_pattern.match(query))

    @classmethod
    def find_queries(cls, text: str):
        """
        Finds all valid query matches in a given text.
        Returns a list of dictionaries, each containing the matched query and the grouped tags.
        """
        matches = []
        for match in cls.QUERY_PATTERN.finditer(text):
            query_str = match.group()
            tags = cls.TAG_SEARCH_PATTERN.findall(query_str)
            matches.append({"query": query_str, "tags": tags})
        return matches

    @classmethod
    def validate_tag(cls, tag: str) -> bool:
        """Validate individual tag."""
        return bool(cls.TAG_PATTERN.match(tag))



def sort_processes(processes: set) -> list:
    """
    Sorts a set of Processes so that any process producing a data structure
    is placed before processes requiring that data structure. In the event
    of a cycle, those processes involved in the cycle are placed at the end.

    Args:
        processes (Set[Process]): Set of process classes to sort.

    Returns:
        List[Process]: A sorted list of process classes.
    """
    processes_list = list(processes)
    adjacency = {proc: [] for proc in processes_list}
    in_degree = {proc: 0 for proc in processes_list}

    for p1 in processes_list:
        for p2 in processes_list:
            if p1 is p2:
                continue
            if getattr(p1, "output", None) == getattr(p2, "input", None):
                adjacency[p1].append(p2)
                in_degree[p2] += 1

    queue = deque([p for p in processes_list if in_degree[p] == 0])
    result = []

    while queue:
        current = queue.popleft()
        result.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    remaining = [p for p in processes_list if p not in result]
    return result + remaining

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

    return discovered_classes

def get_row_data(table_widget: QTableWidget, row_idx: int) -> dict[str, str]:
    """
    Fetches all data in a given row of a QTableWidget as a dictionary.

    Args:
        table_widget (QTableWidget): The table widget.
        row_idx (int): The row index.

    Returns:
        dict[str, str]: A dictionary mapping column headers to cell values.
    """
    headers = [table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())]
    values = [table_widget.item(row_idx, col).text() if table_widget.item(row_idx, col) else "" 
              for col in range(table_widget.columnCount())]
    return dict(zip(headers, values))

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
