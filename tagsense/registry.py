# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** CONSTANTS *****
class_registry = []
installed_processes = set()

# **** FUNCTIONS ****
def register_classes(classes):
    """Registers discovered process classes."""
    class_registry.extend(classes)

def mark_installed(process_cls):
    """Marks a process class as installed."""
    installed_processes.add(process_cls)

def is_installed(process_cls) -> bool:
    """Checks if a process class is installed."""
    return process_cls in installed_processes

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be executed directly.")
