# -*- coding: utf-8 -*-

"""
View module for the main window of the application.
"""

# **** IMPORTS ****
import logging
import sqlite3
from typing import Callable
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QStackedWidget, QComboBox, QPushButton, 
    QTableWidget, QHeaderView, QTableWidgetItem, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QPixmap, QIcon, QAction
from PyQt6.QtWidgets import QAbstractItemView

from tagsense.config import DB_PATH
from tagsense.models.data_structures.file_table.file_table import FileTable
from tagsense.searches.base_file_search import FileSearchBase, generate_search_classes
from tagsense.views.data_view_window import DataViewWindow
from tagsense.searches.searches.example01_even_rows.even_rows import EvenRows
from tagsense.searches.searches.example02_left_sidebar_search.left_sidebar_search import LeftSidebarSearch

from tagsense.views.dialog_windows.file_import import FileImport
from tagsense.views.dialog_windows.run_processes import RunProcesses
from tagsense.views.dialog_windows.export_search import ExportSearch
from tagsense.views.dialog_windows.settings import Settings
from tagsense.views.dialog_windows.help import Help

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class MainWindow(QMainWindow):
    """Main window for the tag-based explorer."""

    def __init__(
        self,
        on_natural_language_query_change: Callable[[str], None],
        on_tag_search_change: Callable[[str], None],
        on_tag_selected: Callable[[str], None],
        parent: QWidget = None
    ) -> None:
        """
        Initializes the MainWindow.

        Args:
            on_natural_language_query_change (Callable[[str], None]): Callback for natural language input changes.
            on_tag_search_change (Callable[[str], None]): Callback for tag input changes.
            on_tag_selected (Callable[[str], None]): Callback when a tag is selected.
            parent (QWidget, optional): Optional parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.init_ui()  # Creates the menu bar and top-level menus

        # Create the main splitter: left (custom sidebar) and right (content)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # We'll create a vertical splitter on the left so we can have top/bottom
        # collapsible sections. The user wants the top collapsed initially,
        # and the bottom to take ~75% of the real estate, the "center" ~25%.
        self.left_sidebar_vsplit = QSplitter(Qt.Orientation.Vertical)

        self.top_spacer = QWidget()
        self.center_widget_holder = QWidget()
        self.center_layout = QVBoxLayout(self.center_widget_holder)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        self.bottom_spacer = QWidget()

        self.left_sidebar_vsplit.addWidget(self.top_spacer)
        self.left_sidebar_vsplit.addWidget(self.center_widget_holder)
        self.left_sidebar_vsplit.addWidget(self.bottom_spacer)

        # Let top and bottom be collapsible
        self.left_sidebar_vsplit.setCollapsible(0, True)
        self.left_sidebar_vsplit.setCollapsible(1, False)
        self.left_sidebar_vsplit.setCollapsible(2, True)

        # The user wants the top collapsed at start, the bottom to take about 75%.
        # We'll attempt [0, 1, 3] so top is 0, center is 1, bottom is 3 => ~ 25% for center, ~75% for bottom.
        self.left_sidebar_vsplit.setSizes([0, 1, 3])

        # Add the left splitter to the main splitter
        self.main_splitter.addWidget(self.left_sidebar_vsplit)

        # Default search
        self.current_search: FileSearchBase = LeftSidebarSearch()
        self.db_path: str = DB_PATH

        # Create the right side widget
        self.right_widget = QWidget()
        self.main_splitter.addWidget(self.right_widget)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 4)

        right_layout = QVBoxLayout(self.right_widget)
        # Top controls (search dropdown, info button, view buttons)
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setContentsMargins(0, 0, 0, 0)

        # Dropdown + info button
        self.search_dropdown = QComboBox()

        # First, add custom searches
        custom_searches = [
            ("Left Sidebar Search", LeftSidebarSearch()),
            ("Even Rows", EvenRows()),
        ]

        for index, (formatted_name, search_instance) in enumerate(custom_searches):
            self.search_dropdown.addItem(formatted_name)
            self.search_dropdown.setItemData(index, search_instance, role=Qt.ItemDataRole.UserRole)

        # Generate search classes dynamically for database tables
        search_classes = generate_search_classes(self.db_path)

        # Add auto-generated searches AFTER the custom ones
        start_index = len(custom_searches)

        for index, (table_name, search_instance) in enumerate(search_classes.items(), start=start_index):
            formatted_name = f"All {table_name.replace('_', ' ').title()}"
            self.search_dropdown.addItem(formatted_name)
            self.search_dropdown.setItemData(index, search_instance, role=Qt.ItemDataRole.UserRole)

        self.search_dropdown.currentIndexChanged.connect(self.handle_search_dropdown_change)

        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.show_search_info)

        left_controls = QHBoxLayout()
        left_controls.addWidget(self.search_dropdown)
        left_controls.addWidget(self.info_button)
        left_controls.addStretch()

        # Table view & grid view
        self.table_view_button = QPushButton("Table View")
        self.grid_view_button = QPushButton("Grid View")
        self.table_view_button.clicked.connect(self.switch_to_table_view)
        self.grid_view_button.clicked.connect(self.switch_to_grid_view)

        right_controls = QHBoxLayout()
        right_controls.addStretch()
        right_controls.addWidget(self.table_view_button)
        right_controls.addWidget(self.grid_view_button)

        top_controls_layout.addLayout(left_controls)
        top_controls_layout.addLayout(right_controls)

        # Stacked widget for table vs. thumbnail view
        self.file_view_stacked = QStackedWidget()
        self.table_widget = QTableWidget()
        self.table_widget.itemDoubleClicked.connect(self.handle_table_double_click)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.file_view_stacked.addWidget(self.table_widget)

        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(self.thumbnail_list.ViewMode.IconMode)
        self.thumbnail_list.setFlow(self.thumbnail_list.Flow.LeftToRight)
        self.thumbnail_list.setResizeMode(self.thumbnail_list.ResizeMode.Adjust)
        self.thumbnail_list.setIconSize(QSize(128, 128))
        self.thumbnail_list.setGridSize(QSize(150, 150))
        self.thumbnail_list.setDragEnabled(False)
        self.thumbnail_list.setMovement(self.thumbnail_list.Movement.Static)
        self.thumbnail_list.itemDoubleClicked.connect(self.handle_thumbnail_double_click)
        self.file_view_stacked.addWidget(self.thumbnail_list)

        right_layout.addLayout(top_controls_layout)
        right_layout.addWidget(self.file_view_stacked)

        self.populate_file_views()
        self.update_left_sidebar()

    def init_ui(self):
        # Create menu bar (encompasses menus)
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        help_settings_menu = menu_bar.addMenu("Help")

        # Create menu item actions
        open_dialog_action = QAction("Import Files", self)
        open_dialog_action.triggered.connect(lambda: FileImport(self).exec())
        run_processes_action = QAction("Run Processes", self)
        run_processes_action.triggered.connect(lambda: RunProcesses(self).exec())
        export_dialog_action = QAction("Export Search", self)
        export_dialog_action.triggered.connect(lambda: ExportSearch(self).exec())

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: Settings(self).exec())
        help_action = QAction("Help", self)
        help_action.triggered.connect(lambda: Help(self).exec())

        # Add all actions to their respective menus
        file_menu.addAction(open_dialog_action)
        file_menu.addAction(export_dialog_action)
        file_menu.addAction(run_processes_action)
        help_settings_menu.addAction(settings_action)
        help_settings_menu.addAction(help_action)

    def update_left_sidebar(self) -> None:
        """
        Updates the left sidebar based on the current search's custom widget.
        Collapses the entire left splitter if no widget is provided.
        """
        # Remove existing layout content from self.center_layout
        while self.center_layout.count():
            item = self.center_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        # Get the search-provided widget (may be None)
        widget = self.current_search.get_left_sidebar_widget(self.center_widget_holder)
        if widget is None:
            # Hide the entire vsplit
            self.left_sidebar_vsplit.setVisible(False)
            self.main_splitter.setSizes([0, 1])
        else:
            self.left_sidebar_vsplit.setVisible(True)
            self.center_layout.addWidget(widget)
            # Expand a bit
            self.main_splitter.setSizes([1, 3])

    def handle_natural_language_input(self, text: str) -> None:
        """
        Handles updates to the natural language input.

        Args:
            text (str): Updated text for the natural language query.
        """
        self.on_natural_language_query_change(text)

    def handle_tag_input(self, text: str) -> None:
        """
        Handles updates to the tag input.

        Args:
            text (str): Updated text for the tag query.
        """
        self.on_tag_search_change(text)

    def handle_tag_list_click(self, item: QListWidgetItem) -> None:
        """
        Handles clicks on items in either tag list.

        Args:
            item (QListWidgetItem): The clicked tag list item.
        """
        self.on_tag_selected(item.text())


    def handle_search_dropdown_change(self, index: int) -> None:
        """
        Handles change in the search dropdown, updates the current search, and repopulates the view.
        Also updates the left sidebar.
        """
        self.current_search = self.search_dropdown.itemData(index, role=Qt.ItemDataRole.UserRole)
        self.populate_file_views()
        self.update_left_sidebar()

    def show_search_info(self) -> None:
        """
        Displays the help text of the current search in a QMessageBox.
        """
        QMessageBox.information(self, "Search Info", self.current_search.get_help_text())

    def switch_to_table_view(self) -> None:
        """
        Switches the stacked widget to show the table view.
        """
        self.file_view_stacked.setCurrentIndex(0)

    def switch_to_grid_view(self) -> None:
        """
        Switches the stacked widget to show the thumbnail (grid) view.
        """
        self.file_view_stacked.setCurrentIndex(1)

    def populate_file_views(self) -> None:
        """
        Populates both the table and the thumbnail grid using the current search.
        """
        self.clear_thumbnails()
        self.table_widget.clear()
        self.table_widget.setRowCount(0)

        results = self.current_search.fetch_results(self.db_path)
        if not results:
            self.table_widget.setColumnCount(0)
            return

        columns = list(results[0].keys())
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Allow user to resize columns manually but also stretch the last one
        for col_idx in range(len(columns)):
            self.table_widget.horizontalHeader().setSectionResizeMode(
                col_idx,
                QHeaderView.ResizeMode.Interactive if col_idx < len(columns)-1
                else QHeaderView.ResizeMode.Stretch
            )
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.rowid_col_idx = None
        if "rowid" in columns:
            self.rowid_col_idx = columns.index("rowid")

        for row_idx, record in enumerate(results):
            self.table_widget.insertRow(row_idx)
            for col_idx, col_key in enumerate(columns):
                item_value = str(record.get(col_key, ""))
                self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(item_value))

            rowid = str(record.get("rowid", ""))
            file_path = self._fetch_file_path(rowid)
            pixmap = QPixmap(file_path)
            thumbnail_item = QListWidgetItem(f"RowID: {rowid}")
            if pixmap.isNull():
                thumbnail_item.setText(f"RowID: {rowid}\nNo thumbnail")
            else:
                scaled_pix = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumbnail_item.setIcon(QIcon(scaled_pix))

            thumbnail_item.setData(Qt.ItemDataRole.UserRole, rowid)
            self.thumbnail_list.addItem(thumbnail_item)

    def handle_table_double_click(self, item: QTableWidgetItem) -> None:
        """Opens detail window when a user double-clicks a table cell."""
        if self.rowid_col_idx is None:
            return
        row_idx = item.row()
        rowid = self.table_widget.item(row_idx, self.rowid_col_idx).text()
        self.open_detail_window(rowid)

    def handle_thumbnail_double_click(self, item: QListWidgetItem) -> None:
        """Opens detail window when a user double-clicks a thumbnail item."""
        rowid = item.data(Qt.ItemDataRole.UserRole)
        self.open_detail_window(rowid)

    def update_system_tag_list(self, tags: list[str]) -> None:
        """
        Updates the system tag list with the specified tags.

        Args:
            tags (list[str]): New system tags to display.
        """
        self.system_tag_list.clear()
        for tag in tags:
            self.system_tag_list.addItem(tag)

    def add_thumbnail(self, file_name: str) -> None:
        """
        Adds a new thumbnail item to the thumbnail list.

        Args:
            file_name (str): The file name or path to represent in the list.
        """
        self.thumbnail_list.addItem(QListWidgetItem(file_name))

    def clear_thumbnails(self) -> None:
        """
        Removes all thumbnail items from the thumbnail list.
        """
        self.thumbnail_list.clear()

    def open_detail_window(self, rowid: str) -> None:
        """
        Opens a new, non-blocking window showing the image (if any) for the given rowid,
        preserving aspect ratio, and closing on double-click.
        """
        window = DataViewWindow(self, rowid, self.db_path)
        window.show()

    def _fetch_file_path(self, rowid: str) -> str:
        """Fetches file_path from FileTable for the given rowid."""
        conn = sqlite3.connect(self.db_path)
        record = FileTable.fetch_record(conn, rowid, "rowid")
        conn.close()
        if record:
            return record.get("file_path", "")
        return ""

# ****
if __name__ == "__main__":
    raise Exception("This module is not meant to be run on its own.")
