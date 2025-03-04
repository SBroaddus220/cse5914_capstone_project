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
from tagsense.processes.base_process import BaseProcess
from tagsense.searches.base_file_search import FileSearchBase
from tagsense.searches.base_file_search import generate_search_classes

from tagsense.config import LOGGER_CONFIG, DB_PATH
from tagsense.database import get_db_connection
from tagsense.models.model import TagExplorerModel
from tagsense.controllers.controller import TagExplorerController
from tagsense.views.main_window import MainWindow
from tagsense.models.data_structures.file_table.file_table import FileTable
from tagsense.models.data_structures.file_metadata.file_metadata import FileMetadata

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** MAIN ****
def main() -> None:
    # ****
    # Init DBs
    db_path = Path(DB_PATH)
    logger.info(f"Initializing core tables in database at {db_path}")
    # Creates database if not present
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch()

    conn = get_db_connection(db_path)
    try:
        # Create only the core tables
        FileTable.create_table(conn)
        FileMetadata.create_table(conn)
        
        # Verify each table has the required columns
        if not FileTable.verify_table(conn) or not FileTable.verify_table(conn):
            logger.error("Core tables do not have the required columns.")
            conn.close()
            sys.exit(1)
    finally:
        conn.close()

    # ****
    # Register and install processes if no installation required
    from tagsense.processes.preprocessing.extract_file_metadata.extract_file_metadata import ExtractFileMetadataProcess
    from tagsense.processes.preprocessing.file_preprocessing.file_preprocessing import FilePreprocessing

    registry.register_processes([ExtractFileMetadataProcess, FilePreprocessing])
    registry.mark_process_as_installed(ExtractFileMetadataProcess)
    registry.mark_process_as_installed(FilePreprocessing)
    
    
    discovered_processes = discover_classes(Path(__file__).parent / "tagsense" / "processes" / "processes", BaseProcess)
    for discovered_process in discovered_processes:
        if discovered_process.requires_installation:
            installed = registry.is_process_installed(discovered_process)
            logger.info(f"⚠️ {discovered_process.__name__} requires installation. Installed: {installed}")
        registry.register_processes([discovered_process])
    for process in registry.process_registry:
        process: BaseProcess
        process_name = process.__name__ 
        if process.requires_installation:
            logger.info(f"Skipping installation of {process_name}")
            continue
        if registry.is_process_installed(process):
            logger.info(f"{process_name} already installed")
            continue
        logger.info(f"Installing {process_name}...")
        process.install()
        registry.mark_process_as_installed(process)

    # Register all searches
    generated_searches = generate_search_classes(DB_PATH)
    for table_name, search_instance in generated_searches.items():
        registry.register_searches([search_instance])
    discovered_searches = discover_classes(Path(__file__).parent / "tagsense" / "searches" / "searches", FileSearchBase)
    for discovered_search in discovered_searches:
        registry.register_searches([discovered_search])
    
    # ****
    # Init GUI 
    app = QApplication(sys.argv)
    model = TagExplorerModel()
    controller = TagExplorerController(model)

    app.setApplicationName("TagSense")
    app.setApplicationDisplayName("TagSense")
    app.setOrganizationName("TagSense Inc.")

    def on_natural_language_query_change(text: str) -> None:
        controller.update_natural_language_query(text)

    def on_tag_search_change(text: str) -> None:
        # Example usage: fetching tags that match `text`
        # For now just pass
        pass

    def on_tag_selected(tag: str) -> None:
        # Example usage: removing or doing something with the selected tag
        pass

    view = MainWindow(
        on_natural_language_query_change,
        on_tag_search_change,
        on_tag_selected
    )
    # view.update_normal_tag_list(["common_tag_1", "common_tag_2", "common_tag_3"])
    # view.add_thumbnail("Thumbnail 1")
    # view.add_thumbnail("Thumbnail 2")
    view.show()

    sys.exit(app.exec())
    

# ****
if __name__ == "__main__":
    import logging.config
    logging.disable(logging.DEBUG)
    logging.config.dictConfig(LOGGER_CONFIG)
    main()
