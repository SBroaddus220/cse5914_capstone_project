# -*- coding: utf-8 -*-

"""
Entry point for the application.
"""

# **** IMPORTS ****
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from tagsense.config import LOGGER_CONFIG, DB_PATH
from tagsense.database import get_db_connection
from tagsense.models.model import TagExplorerModel
from tagsense.controllers.controller import TagExplorerController
from tagsense.views.main_window import TagExplorerView
from tagsense.processes.preprocessing import FileTable, FileCoreMetadataTable

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** MAIN ****
def main() -> None:
    # ****
    # Init DBs
    db_path = Path(DB_PATH)
    logger.info(f"Initializing core tables in database at {db_path}")

    conn = get_db_connection(db_path)
    try:
        # Create only the core tables
        FileTable.create_table(conn)
        FileCoreMetadataTable.create_table(conn)
        
        # Verify each table has the required columns
        if not FileTable.verify_table(conn) or not FileTable.verify_table(conn):
            logger.error("Core tables do not have the required columns.")
            conn.close()
            sys.exit(1)
    finally:
        conn.close()
    
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

    view = TagExplorerView(
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
