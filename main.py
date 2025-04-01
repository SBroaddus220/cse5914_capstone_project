# -*- coding: utf-8 -*-

"""
Entry point for the application.
"""

# **** IMPORTS ****
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from tagsense import registry
from tagsense.util import discover_classes
from tagsense.searches.app_search import AppSearch
from tagsense.database import get_db_connection
from tagsense.views.main_window import MainWindow
from tagsense.config import LOGGER_CONFIG, DB_PATH
from tagsense.processes.app_process import AppProcess
from tagsense.data_structures.app_data_structure import AppDataStructure
from tagsense.searches.app_search import generate_search_classes
from tagsense.data_structures.manual_data_structure import ManualDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** FUNCTIONS ****
def global_exception_hook(exctype, value, tb):
    """Called for any unhandled exception that would cause the app to crash."""
    logger.error("Unhandled exception in application", exc_info=(exctype, value, tb))
    if conn is not None:
        try:
            logger.info("Closing database connection due to unhandled exception.")
            conn.close()
        except Exception:
            pass  # Just ignore any errors here
    # If you want the app to keep running (rarely advisable), remove sys.exit
    sys.exit(1)
sys.excepthook = global_exception_hook

# **** MAIN ****
def main() -> None:
    global conn
    
    # ****
    # Init DBs
    db_path = Path(DB_PATH)
    logger.info(f"Initializing database at {db_path}")

    # Creates database if not present
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch()
    
    conn = get_db_connection(DB_PATH)  # Open DB connection
    AppDataStructure.db_path = db_path

    try:
        # ****
        # Register and install processes if no installation required
        discovered_processes = discover_classes(Path(__file__).parent / "tagsense" / "processes" / "processes", AppProcess)
        for discovered_process in discovered_processes:
            discovered_process: AppProcess
            if discovered_process.requires_installation:
                installed = registry.is_process_installed(discovered_process)
                logger.info(f"⚠️ {discovered_process.__name__} requires installation. Installed: {installed}")
            else:
                registry.mark_process_as_installed(discovered_process)
            registry.register_processes({discovered_process})

        # Remove manual data structure from detected data structures
        registry.detected_data_structures.remove(ManualDataStructure)
        ManualDataStructure.initialize()
        
        # ****
        # Register all searches
        for data_structure in registry.detected_data_structures:
            data_structure: AppDataStructure
            logger.info(f"Initializing data structure: {data_structure.name}...")
            data_structure.initialize()
        generated_searches = generate_search_classes(conn, registry.detected_data_structures)
        for search_name, search_instance in generated_searches.items():
            registry.register_searches({search_instance})
        discovered_searches = discover_classes(Path(__file__).parent / "tagsense" / "searches" / "searches", AppSearch)
        for discovered_search in discovered_searches:
            registry.register_searches({discovered_search})

        # ****
        # Init GUI 
        app = QApplication(sys.argv)

        app.setApplicationName("TagSense")
        app.setApplicationDisplayName("TagSense")
        app.setOrganizationName("TagSense Inc.")

        # Attach DB connection closing logic to app exit
        def close_db_connection():
            if conn:
                logger.info("Closing database connection on app exit.")
                conn.close()

        # Connect the closing function to the `aboutToQuit` signal
        app.aboutToQuit.connect(close_db_connection)

        # Create the main window and show it
        view = MainWindow(conn)
        view.show()

        # Start the event loop
        sys.exit(app.exec())

    except Exception as e:
        # This only catches exceptions BEFORE or DURING the start of app.exec()
        logger.error(f"Caught exception during startup", exc_info=e)
        if conn is not None:
            conn.close()
        raise e

    

# ****
if __name__ == "__main__":
    import logging.config
    logging.disable(logging.DEBUG)
    logging.config.dictConfig(LOGGER_CONFIG)
    main()
