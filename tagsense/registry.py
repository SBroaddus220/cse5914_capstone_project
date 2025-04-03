# -*- coding: utf-8 -*-

"""
Base foundation for processes.
"""

# **** IMPORTS ****
import sqlite3
import logging

from tagsense.config import DB_PATH
from tagsense.database import get_db_connection
from tagsense.processes.process import Process
from tagsense.searches.search import Search
from tagsense.data_structures.sqlite_table import SQLITETable
from tagsense.data_structures.data_structure import DataStructure

# **** CONSTANTS *****
process_registry: set[Process] = set()
search_registry: set[Search] = set()
detected_data_structures: set[DataStructure] = set()

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class InstalledProcesses(SQLITETable):
    """Table to persistently store installed processes."""
    table_name: str = "installed_processes"
    required_columns: set[str] = {"rowid", "process_uid"}
    
    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table_name} (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            process_uid TEXT UNIQUE NOT NULL
        )
        """
        conn.execute(sql)
        conn.commit()

# **** FUNCTIONS ****
def register_processes(classes: set[Process]):
    """Registers discovered process classes."""
    process_registry.update(classes)

    # Add to relevant registries
    for process_cls in classes:
        process_cls: Process
        if process_cls.input:
            detected_data_structures.add(process_cls.input)
        if process_cls.output:
            detected_data_structures.add(process_cls.output)

def register_searches(classes: set[Search]):
    """Registers discovered search classes."""
    search_registry.update(classes)

def mark_process_as_installed(process_cls: Process):
    """Marks a process class as installed."""
    # Add to persistent registry
    with get_db_connection(DB_PATH) as conn:
        InstalledProcesses.create_table(conn)
        existing_data = InstalledProcesses.fetch_all(conn)
        existing = any(record["process_uid"] == process_cls.uid for record in existing_data)
        if existing:
            raise Exception(f"Process {process_cls.name} is already installed.")
        # Insert into the installed processes table
        InstalledProcesses.insert_record(conn, {"process_uid": process_cls.uid})
    
def fetch_installed_processes() -> set[Process]:
    installed_processes = set()
    with get_db_connection(DB_PATH) as conn:
        InstalledProcesses.create_table(conn)
        existing_data = InstalledProcesses.fetch_all(conn)
        for existing_record in existing_data:
            process_uid = existing_record["process_uid"]
            process_cls = fetch_process_by_uid(process_uid)
            if process_cls:
                installed_processes.add(process_cls)
            else:
                logger.warning(f"Installed process with UID {process_uid} not found in registry.")
    return installed_processes

def is_process_installed(process_cls: Process) -> bool:
    """Checks if a process class is installed."""
    existing_data = []
    with get_db_connection(DB_PATH) as conn:
        InstalledProcesses.create_table(conn)
        existing_data = InstalledProcesses.fetch_all(conn)
    existing = any(record["process_uid"] == process_cls.uid for record in existing_data)
    return existing

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
