"""View module for the tag-based explorer application."""

import logging
from typing import Callable
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QLineEdit, QListWidget,
    QVBoxLayout, QHBoxLayout, QListWidgetItem, QComboBox, QFrame, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QDialog, QLabel, QScrollArea, QAbstractItemView
)
from PyQt6.QtGui import QAction, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize

from tagsense.config import DB_PATH
from tagsense.searches.base_file_search import FileSearchBase
from tagsense.searches.all_files.all_files_search import AllFilesSearch, AllFileMetadataSearch
from tagsense.views.dialog_windows import MediaImport, ExportSearch, Settings, Help

logger = logging.getLogger(__name__)

def _create_vlines_wrapped_widget(widget: QWidget) -> QWidget:
    """
    Wraps the given widget with vertical lines on each side.
    
    Args:
        widget (QWidget): The widget to wrap.
    
    Returns:
        QWidget: A new widget containing the original widget with two vertical lines.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    left_line = QFrame()
    left_line.setFrameShape(QFrame.Shape.VLine)
    left_line.setFrameShadow(QFrame.Shadow.Sunken)

    right_line = QFrame()
    right_line.setFrameShape(QFrame.Shape.VLine)
    right_line.setFrameShadow(QFrame.Shadow.Sunken)

    layout.addWidget(left_line)
    layout.addWidget(widget)
    layout.addWidget(right_line)
    return container

class TagExplorerView(QMainWindow):
    """Main window for the tag-based explorer."""

    def __init__(
        self,
        on_natural_language_query_change: Callable[[str], None],
        on_tag_search_change: Callable[[str], None],
        on_tag_selected: Callable[[str], None],
        parent: QWidget = None
    ) -> None:
        """
        Initializes the TagExplorerView.

        Args:
            on_natural_language_query_change (Callable[[str], None]): Callback for natural language input changes.
            on_tag_search_change (Callable[[str], None]): Callback for tag input changes.
            on_tag_selected (Callable[[str], None]): Callback when a tag is selected.
            parent (QWidget, optional): Optional parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.init_ui()

        # Main horizontal splitter for left (controls) and right (thumbnails)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side big splitter
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top spacer for adjustable empty space
        self.top_spacer = QWidget()

        # Middle splitter holds the four sections:
        #   1) Natural language search
        #   2) Tag search
        #   3) System tag area (+dropdown)
        #   4) Normal tag area (+dropdown)
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)

        # Bottom spacer for adjustable empty space
        self.bottom_spacer = QWidget()

        # Natural language search section
        self.natural_language_input = QLineEdit()
        self.natural_language_input.setPlaceholderText("Enter natural language query...")

        # Tag search section
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter tag search query...")

        # System tags
        self.system_widget = QWidget()
        self.system_layout = QVBoxLayout(self.system_widget)
        self.system_sort_dropdown = QComboBox()
        self.system_sort_dropdown.addItems(["System Sort A", "System Sort B"])
        self.system_tag_list = QListWidget()
        self.system_layout.addWidget(self.system_sort_dropdown)
        self.system_layout.addWidget(self.system_tag_list)

        # Normal tags
        self.normal_widget = QWidget()
        self.normal_layout = QVBoxLayout(self.normal_widget)
        self.normal_sort_dropdown = QComboBox()
        self.normal_sort_dropdown.addItems(["Normal Sort A", "Normal Sort B"])
        self.normal_tag_list = QListWidget()
        self.normal_layout.addWidget(self.normal_sort_dropdown)
        self.normal_layout.addWidget(self.normal_tag_list)

        # Wrap each of the four sections with vertical lines
        wrapped_natural_language_input = _create_vlines_wrapped_widget(self.natural_language_input)
        wrapped_tag_input = _create_vlines_wrapped_widget(self.tag_input)
        wrapped_system_widget = _create_vlines_wrapped_widget(self.system_widget)
        wrapped_normal_widget = _create_vlines_wrapped_widget(self.normal_widget)

        self.content_splitter.addWidget(wrapped_natural_language_input)
        self.content_splitter.addWidget(wrapped_tag_input)
        self.content_splitter.addWidget(wrapped_system_widget)
        self.content_splitter.addWidget(wrapped_normal_widget)
        for i in range(self.content_splitter.count()):
            self.content_splitter.setCollapsible(i, False)

        self.left_splitter.addWidget(self.top_spacer)
        self.left_splitter.addWidget(self.content_splitter)
        self.left_splitter.addWidget(self.bottom_spacer)

        # Let top_spacer and bottom_spacer be collapsible, center always visible
        self.left_splitter.setCollapsible(0, True)
        self.left_splitter.setCollapsible(1, False)
        self.left_splitter.setCollapsible(2, True)

        # Explicitly set initial sizes so top is collapsed by default
        self.left_splitter.setSizes([0, 1, 0])

        self.current_search: FileSearchBase = AllFilesSearch()
        self.db_path: str = DB_PATH

        # Create a horizontal layout for the dropdown and view buttons
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail list for grid view
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(self.thumbnail_list.ViewMode.IconMode)
        self.thumbnail_list.setFlow(self.thumbnail_list.Flow.LeftToRight)
        self.thumbnail_list.setResizeMode(self.thumbnail_list.ResizeMode.Adjust)
        self.thumbnail_list.setIconSize(QSize(128, 128))
        self.thumbnail_list.setGridSize(QSize(150, 150))
        self.thumbnail_list.setDragEnabled(False)
        self.thumbnail_list.setMovement(self.thumbnail_list.Movement.Static)
        # Connect double-click signal
        self.thumbnail_list.itemDoubleClicked.connect(self.handle_thumbnail_double_click)

        # Dropdown (left-aligned) + info button
        self.search_dropdown = QComboBox()
        self.search_dropdown.addItem("All Files")
        self.search_dropdown.setItemData(0, AllFilesSearch(), role=Qt.ItemDataRole.UserRole)
        self.search_dropdown.addItem("All File Metadata")
        self.search_dropdown.setItemData(1, AllFileMetadataSearch(), role=Qt.ItemDataRole.UserRole)

        # When the search dropdown changes, update the current search and repopulate the view
        self.search_dropdown.currentIndexChanged.connect(self.handle_search_dropdown_change)

        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.show_search_info)

        left_controls = QHBoxLayout()
        left_controls.addWidget(self.search_dropdown)
        left_controls.addWidget(self.info_button)
        left_controls.addStretch()  # push items to the left

        # Two view buttons (right-aligned)
        self.table_view_button = QPushButton("Table View")
        self.grid_view_button = QPushButton("Grid View")
        self.table_view_button.clicked.connect(self.switch_to_table_view)
        self.grid_view_button.clicked.connect(self.switch_to_grid_view)

        right_controls = QHBoxLayout()
        right_controls.addStretch()  # push buttons to the right
        right_controls.addWidget(self.table_view_button)
        right_controls.addWidget(self.grid_view_button)

        # Combine left and right controls into top_controls_layout
        top_controls_layout.addLayout(left_controls)
        top_controls_layout.addLayout(right_controls)

        # Stacked widget for switching between table view and thumbnail list
        self.file_view_stacked = QStackedWidget()
        # Table
        self.table_widget = QTableWidget()
        self.table_widget.itemDoubleClicked.connect(self.handle_table_double_click)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # self.table_widget.setColumnCount(10)  # Adjust as needed
        self.file_view_stacked.addWidget(self.table_widget)
        # Grid (thumbnail_list already defined)
        self.file_view_stacked.addWidget(self.thumbnail_list)

        # Modify right_widget layout to include these new controls
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.addLayout(top_controls_layout)
        right_layout.addWidget(self.file_view_stacked)


        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.right_widget)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 4)

        container_layout = QHBoxLayout()
        container_layout.addWidget(self.main_splitter)
        container = QWidget()
        container.setLayout(container_layout)
        self.setCentralWidget(container)

        # Connect signals
        self.natural_language_input.textChanged.connect(self.handle_natural_language_input)
        self.tag_input.textChanged.connect(self.handle_tag_input)
        self.system_tag_list.itemClicked.connect(self.handle_tag_list_click)
        self.normal_tag_list.itemClicked.connect(self.handle_tag_list_click)

        self.populate_file_views()

    def init_ui(self):
        # Create menu bar (encompasses menus)
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        help_settings_menu = menu_bar.addMenu("Help")

        # Create menu item actions
        open_dialog_action = QAction("Import Media", self)
        open_dialog_action.triggered.connect(lambda: MediaImport(self).exec())
        export_dialog_action = QAction("Export Search", self)
        export_dialog_action.triggered.connect(lambda: ExportSearch(self).exec())

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: Settings(self).exec())
        help_action = QAction("Help", self)
        help_action.triggered.connect(lambda: Help(self).exec())

        # Add all actions to their respective menus
        file_menu.addAction(open_dialog_action)
        file_menu.addAction(export_dialog_action)
        help_settings_menu.addAction(settings_action)
        help_settings_menu.addAction(help_action)

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
        """
        self.current_search = self.search_dropdown.itemData(index, role=Qt.ItemDataRole.UserRole)
        self.populate_file_views()

    def show_search_info(self) -> None:
        """
        Displays the SQL query of the current search.
        """
        query = self.current_search.get_sql()
        QMessageBox.information(self, "Search Info", query)

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

    def update_normal_tag_list(self, tags: list[str]) -> None:
        """
        Updates the normal tag list with the specified tags.

        Args:
            tags (list[str]): New normal tags to display.
        """
        self.normal_tag_list.clear()
        for tag in tags:
            self.normal_tag_list.addItem(tag)

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
        window = ImageWindow(self, rowid, self.db_path)
        window.show()

    def _fetch_file_path(self, rowid: str) -> str:
        """Fetches file_path from FileTable for the given rowid."""
        import sqlite3
        from tagsense.models.file_table import FileTable
        conn = sqlite3.connect(self.db_path)
        record = FileTable.fetch_record(conn, rowid, "rowid")
        conn.close()
        if record:
            return record.get("file_path", "")
        return ""


class ClickableLabel(QLabel):
    """A QLabel that closes its top-level parent window when double-clicked."""
    def mouseDoubleClickEvent(self, event):
        self.window().close()
        super().mouseDoubleClickEvent(event)



class ImageWindow(QMainWindow):
    """Window to display an image while maintaining aspect ratio, closing on double-click."""

    def __init__(self, parent: QWidget, rowid: str, db_path: str) -> None:
        super().__init__(parent)
        self._original_pixmap = QPixmap()
        self.setWindowTitle(f"Details for rowid = {rowid}")
        self.showMaximized()
        self._db_path = db_path
        self._rowid = rowid

        # Make sure this attribute is defined before _load_pixmap is called

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        self.label = ClickableLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.container.setLayout(self.layout)
        scroll_area.setWidget(self.container)
        self.setCentralWidget(scroll_area)

        self._load_pixmap()

    def _load_pixmap(self) -> None:
        import sqlite3
        from tagsense.models.file_table import FileTable
        conn = sqlite3.connect(self._db_path)
        record = FileTable.fetch_record(conn, self._rowid, "rowid")
        conn.close()

        if not record:
            self.label.setText(f"No database record found for rowid {self._rowid}")
            return

        file_path = record.get("file_path", "")
        pm = QPixmap(file_path)
        if pm.isNull():
            self.label.setText(f"No valid image for rowid {self._rowid}")
            return

        self._original_pixmap = pm
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._original_pixmap.isNull():
            return
        available_size = self.container.size()
        scaled_pm = self._original_pixmap.scaled(
            available_size.width(),
            available_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.label.setPixmap(scaled_pm)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def mouseDoubleClickEvent(self, event):
        self.close()
        super().mouseDoubleClickEvent(event)
