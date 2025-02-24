# -*- coding: utf-8 -*-

"""
View module for viewing a specific piece of data.
"""

# **** IMPORTS ****
import logging
from typing import List, Dict
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QCheckBox, QStackedWidget,
    QPushButton, QTableWidget, QAbstractItemView, QTableWidgetItem, QListWidget, QListWidgetItem, QDialog, QHeaderView
)

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class ClickableLabel(QLabel):
    """A QLabel that closes its top-level parent window when double-clicked."""
    def mouseDoubleClickEvent(self, event):
        self.window().close()
        super().mouseDoubleClickEvent(event)

class DataViewWindow(QMainWindow):
    """Window that displays three horizontal sections: left sidebar, center data (with grid/table switch),
    and right sidebar (thumbnail, related files, parents, children, siblings each with table/grid switch).
    Includes logic for process-based filtering.

    Args:
        parent (QWidget): Parent widget.
        rowid (str): The 'rowid' of the record to display.
        db_path (str): Path to the SQLite database.
    """

    def __init__(self, parent: QWidget, rowid: str, db_path: str) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self._rowid = rowid
        self.setWindowTitle(f"Details for rowid = {rowid}")
        self.showMaximized()

        # Main widget and layout (horizontal for three sections).
        self._main_widget = QWidget()
        self._main_layout = QHBoxLayout(self._main_widget)
        self.setCentralWidget(self._main_widget)

        # Prepare left sidebar.
        self._left_sidebar_widget = QWidget()
        self._left_sidebar_layout = QVBoxLayout(self._left_sidebar_widget)
        self._populate_left_sidebar()

        self._left_scroll_area = QScrollArea()
        self._left_scroll_area.setWidgetResizable(True)
        self._left_scroll_area.setWidget(self._left_sidebar_widget)

        # Prepare center view (stacked content per table, filtered by processes).
        self._center_container = QWidget()
        self._center_container_layout = QVBoxLayout(self._center_container)
        self._center_scroll_area = QScrollArea()
        self._center_scroll_area.setWidgetResizable(True)
        self._center_scroll_area.setWidget(self._center_container)

        # Dictionary of { table_name: (table_processes, widget) } to show/hide based on selected processes.
        self._table_widgets = {}
        self._selected_processes = set()

        self._populate_center_view()

        # Prepare right sidebar (thumbnail, related files, parents/children/siblings each with table/grid).
        self._right_sidebar_widget = QWidget()
        self._right_sidebar_layout = QVBoxLayout(self._right_sidebar_widget)
        self._populate_right_sidebar()

        # Add to main layout.
        self._main_layout.addWidget(self._left_scroll_area, 1)
        self._main_layout.addWidget(self._center_scroll_area, 3)
        self._main_layout.addWidget(self._right_sidebar_widget, 1)

    def _fetch_topmost_id(self) -> str:
        """Fetch the topmost identity record (currently the FileTable rowid).

        Returns:
            str: The topmost record ID.
        """
        return self._rowid

    def _fetch_related_tables(self, topmost_id: str) -> List[str]:
        """Fetch the list of tables that reference the topmost_id.

        Args:
            topmost_id (str): The row ID from the FileTable.

        Returns:
            List[str]: List of table names that reference the topmost record.
        """
        return ["FileTable", "TagTable", "MetadataTable"]

    def _fetch_table_records(self, table_name: str, topmost_id: str) -> List[Dict]:
        """Fetch records for a table referencing the topmost_id.

        Args:
            table_name (str): Table name.
            topmost_id (str): Row ID from FileTable.

        Returns:
            List[Dict]: A list of row dictionaries.
        """
        if table_name == "FileTable":
            return [{"rowid": topmost_id, "file_path": "/path/to/file.png"}]
        elif table_name == "TagTable":
            return [
                {"tag_id": "1", "tag_name": "example_tag"},
                {"tag_id": "2", "tag_name": "another_tag"}
            ]
        else:
            return [{"key": "value"}]

    def _fetch_table_processes(self, table_name: str) -> List[str]:
        """Fetch processes associated with a given table.

        Args:
            table_name (str): The table name.

        Returns:
            List[str]: List of processes for this table.
        """
        if table_name == "FileTable":
            return ["ProcessA", "ProcessCommon"]
        elif table_name == "TagTable":
            return ["ProcessB", "ProcessCommon"]
        else:
            return ["ProcessC"]

    def _fetch_all_processes(self) -> List[str]:
        """Fetch all possible processes across all tables.

        Returns:
            List[str]: A list of all unique processes.
        """
        all_tables = self._fetch_related_tables(self._fetch_topmost_id())
        processes = set()
        for tbl in all_tables:
            processes.update(self._fetch_table_processes(tbl))
        return sorted(list(processes))

    def _fetch_file_path(self, rowid: str) -> str:
        """Fetch file_path for the current datum from the FileTable.

        Args:
            rowid (str): The row ID.

        Returns:
            str: Path to the file if any.
        """
        # Dummy logic. In real code, query DB for the actual file path.
        return "/path/to/file.png"

    def _fetch_related_files(self, rowid: str) -> List[str]:
        """Fetch a list of related file paths for the given rowid.

        Args:
            rowid (str): The row ID to find related files for.

        Returns:
            List[str]: File paths related to the provided rowid.
        """
        return ["/path/to/related1.png", "/path/to/related2.png"]

    def _fetch_parents(self, rowid: str) -> List[str]:
        """Fetch list of parent data references.

        Args:
            rowid (str): The row ID of the data.

        Returns:
            List[str]: A list of parent references.
        """
        return ["ParentA", "ParentB"]

    def _fetch_children(self, rowid: str) -> List[str]:
        """Fetch list of child data references.

        Args:
            rowid (str): The row ID of the data.

        Returns:
            List[str]: A list of child references.
        """
        return ["Child1", "Child2"]

    def _fetch_siblings(self, rowid: str) -> List[str]:
        """Fetch list of sibling data references.

        Args:
            rowid (str): The row ID of the data.

        Returns:
            List[str]: A list of sibling references.
        """
        return ["SiblingX", "SiblingY"]

    def _populate_left_sidebar(self) -> None:
        """Populates the left sidebar with referencing tables and process checkboxes."""
        topmost_id = self._fetch_topmost_id()
        table_list = self._fetch_related_tables(topmost_id)

        self._left_sidebar_layout.addWidget(QLabel("Tables:"))
        self._table_checkboxes = []
        for tname in table_list:
            cb = QCheckBox(tname)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_table_checkbox_toggled)
            self._left_sidebar_layout.addWidget(cb)
            self._table_checkboxes.append(cb)

        self._left_sidebar_layout.addWidget(QLabel("Processes:"))
        self._process_checkboxes = []
        all_procs = self._fetch_all_processes()
        for proc in all_procs:
            cb = QCheckBox(proc)
            cb.setChecked(False)
            cb.stateChanged.connect(self._on_process_checkbox_toggled)
            self._left_sidebar_layout.addWidget(cb)
            self._process_checkboxes.append(cb)

        self._left_sidebar_layout.addStretch()

    def _on_table_checkbox_toggled(self, state: int) -> None:
        """Show/hide table widgets based on table checkbox states."""
        self._filter_center_tables_by_processes()

    def _on_process_checkbox_toggled(self, state: int) -> None:
        """Update selected processes and filter tables."""
        self._selected_processes.clear()
        for cb in self._process_checkboxes:
            if cb.isChecked():
                self._selected_processes.add(cb.text())
        self._filter_center_tables_by_processes()

    def _filter_center_tables_by_processes(self) -> None:
        """Enable/disable table widgets based on selected processes and table checkboxes."""
        for cb in self._table_checkboxes:
            tname = cb.text()
            widget_info = self._table_widgets.get(tname)
            if not widget_info:
                continue
            table_processes, widget = widget_info
            if not cb.isChecked():
                widget.setVisible(False)
                continue
            if not self._selected_processes:
                widget.setVisible(True)
            else:
                if self._selected_processes.intersection(table_processes):
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def _populate_center_view(self) -> None:
        """Populate the center area with a series of stacked widgets (table/grid), one per referencing table."""
        topmost_id = self._fetch_topmost_id()
        table_list = self._fetch_related_tables(topmost_id)

        for tname in table_list:
            records = self._fetch_table_records(tname, topmost_id)
            procs = self._fetch_table_processes(tname)
            widget = self._create_table_and_grid_for_table(tname, records, procs)
            self._center_container_layout.addWidget(widget)
            self._table_widgets[tname] = (set(procs), widget)

        self._center_container_layout.addStretch()

    def _create_table_and_grid_for_table(self, table_name: str, records: List[Dict], processes: List[str]) -> QWidget:
        """
        Creates a widget containing:
         - A label with table name and processes
         - Two buttons for switching between table and grid
         - A QStackedWidget with a table and a list widget (grid)
        """
        container = QWidget()
        layout = QVBoxLayout(container)

        lbl = QLabel(f"{table_name} (Processes: {', '.join(processes)})")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        table_btn = QPushButton("Table View")
        grid_btn = QPushButton("Grid View")
        btn_layout.addWidget(table_btn)
        btn_layout.addWidget(grid_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        stack = QStackedWidget()
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        grid_widget = QListWidget()
        grid_widget.setViewMode(QListWidget.ViewMode.IconMode)
        grid_widget.setFlow(QListWidget.Flow.LeftToRight)
        grid_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid_widget.setIconSize(QSize(64, 64))

        if records:
            columns = list(records[0].keys())
            table_widget.setColumnCount(len(columns))
            table_widget.setHorizontalHeaderLabels(columns)
            table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

            for row_idx, rec in enumerate(records):
                table_widget.insertRow(row_idx)
                for col_idx, col_key in enumerate(columns):
                    cell_value = str(rec.get(col_key, ""))
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(cell_value))

                item = QListWidgetItem()
                pix_path = rec.get("file_path", "")
                pix = QPixmap(pix_path)
                if not pix.isNull():
                    icon = QIcon(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
                    item.setIcon(icon)
                item.setText(str(rec))
                grid_widget.addItem(item)

        stack.addWidget(table_widget)
        stack.addWidget(grid_widget)
        layout.addWidget(stack)

        def switch_to_table():
            stack.setCurrentIndex(0)

        def switch_to_grid():
            stack.setCurrentIndex(1)

        table_btn.clicked.connect(switch_to_table)
        grid_btn.clicked.connect(switch_to_grid)

        return container

    def _populate_right_sidebar(self) -> None:
        """Populate the right sidebar with a thumbnail of the current datum, related files,
        and parents/children/siblings (each with table/grid view)."""
        # Thumbnail
        self._add_thumbnail_above_related_files()

        # Related Files
        related_files = self._fetch_related_files(self._rowid)
        self._add_relationship_widget("Related Files", related_files)

        # Parents
        parents = self._fetch_parents(self._rowid)
        self._add_relationship_widget("Parents", parents)

        # Children
        children = self._fetch_children(self._rowid)
        self._add_relationship_widget("Children", children)

        # Siblings
        siblings = self._fetch_siblings(self._rowid)
        self._add_relationship_widget("Siblings", siblings)

        self._right_sidebar_layout.addStretch()

    def _add_thumbnail_above_related_files(self) -> None:
        """Creates a clickable thumbnail for the current file, displayed at the top of the right sidebar."""
        file_path = self._fetch_file_path(self._rowid)
        self._thumbnail_label = ClickableLabel()
        if file_path:
            pix = QPixmap(file_path)
            if not pix.isNull():
                scaled = pix.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                self._thumbnail_label.setPixmap(scaled)
            else:
                self._thumbnail_label.setText("No valid image")
        else:
            self._thumbnail_label.setText("No image found")

        def open_fullsize_image(event):
            if not file_path:
                return
            full_window = QDialog(self)
            full_window.setWindowTitle("Full-Size Image")
            full_window.setMinimumSize(800, 600)
            scroll = QScrollArea(full_window)
            scroll.setWidgetResizable(True)

            label = QLabel()
            pix_local = QPixmap(file_path)
            if not pix_local.isNull():
                label.setPixmap(pix_local)
            else:
                label.setText("No valid image found")

            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll.setWidget(label)
            lay = QVBoxLayout(full_window)
            lay.addWidget(scroll)
            full_window.setLayout(lay)
            full_window.exec()

        self._thumbnail_label.mouseDoubleClickEvent = open_fullsize_image
        self._thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._right_sidebar_layout.addWidget(self._thumbnail_label)

    def _add_relationship_widget(self, rel_name: str, rel_list: List[str]) -> None:
        """Adds a table/grid switcher for a relationship (e.g. Related Files, Parents, Children, Siblings).

        Args:
            rel_name (str): Name of the relationship (e.g. "Related Files", "Parents").
            rel_list (List[str]): Items that represent each related entity.
        """
        rel_container = QWidget()
        rel_layout = QVBoxLayout(rel_container)

        title_label = QLabel(rel_name)
        title_label.setStyleSheet("font-weight: bold;")
        rel_layout.addWidget(title_label)

        btn_layout = QHBoxLayout()
        table_btn = QPushButton("Table View")
        grid_btn = QPushButton("Grid View")
        btn_layout.addWidget(table_btn)
        btn_layout.addWidget(grid_btn)
        btn_layout.addStretch()
        rel_layout.addLayout(btn_layout)

        stack = QStackedWidget()
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        grid_widget = QListWidget()
        grid_widget.setViewMode(QListWidget.ViewMode.IconMode)
        grid_widget.setFlow(QListWidget.Flow.LeftToRight)
        grid_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid_widget.setIconSize(QSize(64, 64))

        table_widget.setColumnCount(1)
        table_widget.setHorizontalHeaderLabels(["Item"])
        for i, val in enumerate(rel_list):
            table_widget.insertRow(i)
            table_widget.setItem(i, 0, QTableWidgetItem(val))

            item = QListWidgetItem(val)
            # No actual file path logic here for relationships, but you could extend it if needed.
            grid_widget.addItem(item)

        stack.addWidget(table_widget)
        stack.addWidget(grid_widget)
        rel_layout.addWidget(stack)

        def switch_to_table():
            stack.setCurrentIndex(0)

        def switch_to_grid():
            stack.setCurrentIndex(1)

        table_btn.clicked.connect(switch_to_table)
        grid_btn.clicked.connect(switch_to_grid)

        self._right_sidebar_layout.addWidget(rel_container)

# ****
if __name__ == "__main__":
    raise Exception("This module is not meant to be run on its own.")
