# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** IMPORTS ****
from tagsense.processes.process import Process
from tagsense.searches.search import Search
from tagsense.data_structures.data_structure import DataStructure

# **** CONSTANTS *****
process_registry: set[Process] = set()
search_registry: set[Search] = set()
installed_processes: set[Process] = set()
detected_data_structures: set[DataStructure] = set()

# **** FUNCTIONS ****
def register_processes(classes: set[Process]):
    """Registers discovered process classes."""
    process_registry.update(classes)

def register_searches(classes: set[Search]):
    """Registers discovered search classes."""
    search_registry.update(classes)

def mark_process_as_installed(process_cls: Process):
    """Marks a process class as installed."""
    installed_processes.add(process_cls)
    if process_cls.input:
        detected_data_structures.add(process_cls.input)
    if process_cls.output:
        detected_data_structures.add(process_cls.output)

def is_process_installed(process_cls: Process) -> bool:
    """Checks if a process class is installed."""
    return process_cls in installed_processes

def fetch_search_by_name(name: str) -> Search:
    """Fetches a search by name."""
    for search in search_registry:
        if search.name == name:
            return search

def fetch_process_by_uid(uid: str) -> Process:
    """Fetches a process by UID."""
    for process in process_registry:
        if process.uid == uid:
            return process

def fetch_data_structure_by_uid(uid: str) -> DataStructure:
    """Fetches a data structure by UID."""
    for data_structure in detected_data_structures:
        if data_structure.uid == uid:
            return data_structure



# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be executed directly.")
