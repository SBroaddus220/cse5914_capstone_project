# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** CONSTANTS *****
process_registry = []
search_registry = []
installed_processes = set()

# **** FUNCTIONS ****
def register_processes(classes):
    """Registers discovered process classes."""
    process_registry.extend(classes)

def register_searches(classes):
    """Registers discovered search classes."""
    search_registry.extend(classes)

def mark_process_as_installed(process_cls):
    """Marks a process class as installed."""
    installed_processes.add(process_cls)

def is_process_installed(process_cls) -> bool:
    """Checks if a process class is installed."""
    return process_cls in installed_processes



# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be executed directly.")
