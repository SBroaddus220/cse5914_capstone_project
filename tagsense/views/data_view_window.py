# -*- coding: utf-8 -*-

"""
View module for viewing a specific piece of data.
"""

# **** IMPORTS ****
import sqlite3
import logging
from typing import List, Dict, Any
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QCheckBox, QStackedWidget,
    QPushButton, QTableWidget, QAbstractItemView, QTableWidgetItem, QListWidget, QListWidgetItem, QDialog, QHeaderView
)

from tagsense import registry
from tagsense.processes.base_process import BaseProcess
from tagsense.database import find_parent_child_rows, get_db_connection, get_foreign_keys_from_sql, extract_table_names
from tagsense.searches.base_file_search import FileSearchBase

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DataViewWindow(QMainWindow):
    """Window that displays three horizontal sections: left sidebar, center data (with grid/table switch),
    and right sidebar (thumbnail, related files, parents, children, siblings each with table/grid switch).
    Includes logic for process-based filtering.

    Args:
        parent (QWidget): Parent widget.
        rowid (str): The 'rowid' of the record to display.
        db_path (str): Path to the SQLite database.
    """

    def __init__(self, parent: QWidget, rowid: str, current_search: FileSearchBase, db_path: str) -> None:
        """
        Initializes the DataViewWindow with three sections: this datum, children, and parents.
        Also prepares the left sidebar for filtering by tables, searches, and processes.

        Args:
            parent (QWidget): The parent widget.
            rowid (str): The rowid of the record to display.
            current_search (FileSearchBase): The current active search instance.
            db_path (str): The path to the SQLite database.
        """
        super().__init__(parent)
        logger.debug("Initializing DataViewWindow with rowid=%s", rowid)

        self._db_path = db_path
        self._rowid = rowid
        conn = get_db_connection(db_path)

        # Gather parent-child relationships
        logger.debug("Gathering parent-child rows")
        related_queries = []
        for search in registry.search_registry:
            search_instance = search if isinstance(search, FileSearchBase) else search()
            related_queries.append(search_instance.get_sql())
        self._parent_child_rows = find_parent_child_rows(
            conn,
            current_search.get_sql(),
            self._rowid,
            related_queries
        )

        # Identify searches
        logger.debug("Identifying related searches")
        self._related_searches = []
        for search in registry.search_registry:
            search_instance = search if isinstance(search, FileSearchBase) else search()
            if search_instance.get_sql() in self._parent_child_rows.get("matched_queries", []):
                self._related_searches.append(search_instance)
        # Ensure current_search is in the list
        if current_search not in self._related_searches:
            self._related_searches.append(current_search)

        # Identify processes
        logger.debug("Identifying related processes")
        self._related_processes = []
        for process in registry.installed_processes:
            if process not in self._related_processes:
                for data_structure in process.data_structures:
                    if data_structure.TABLE_NAME in self._parent_child_rows.get("matched_tables", []):
                        self._related_processes.append(process)
                        break

        # Main Window Setup
        self.setWindowTitle(f"Details for rowid = {rowid}")
        self.showMaximized()

        self._main_widget = QWidget()
        self._main_layout = QHBoxLayout(self._main_widget)
        self.setCentralWidget(self._main_widget)

        # Left Sidebar
        self._left_sidebar_widget = QWidget()
        self._left_sidebar_layout = QVBoxLayout(self._left_sidebar_widget)
        self._populate_left_sidebar()
        self._left_scroll_area = QScrollArea()
        self._left_scroll_area.setWidgetResizable(True)
        self._left_scroll_area.setWidget(self._left_sidebar_widget)

        # Center Container
        logger.debug("Setting up center container with this datum, children, and parents")
        self._center_container = QWidget()
        self._center_container_layout = QVBoxLayout(self._center_container)
        self._center_scroll_area = QScrollArea()
        self._center_scroll_area.setWidgetResizable(True)
        self._center_scroll_area.setWidget(self._center_container)

        # For filtering
        self._selected_tables = set()
        self._selected_searches = set()
        self._selected_processes = set()

        # Track widgets for filtering
        # Keys will be (section_type, search_name, table_name)
        self._section_widgets = {}

        self._populate_center_view(current_search)
        self._main_layout.addWidget(self._left_scroll_area, 1)
        self._main_layout.addWidget(self._center_scroll_area, 3)

    def _populate_left_sidebar(self) -> None:
        """
        Populates the left sidebar with referencing tables, searches, and process checkboxes.
        By default, all relevant items are checked so they appear in the center view.
        """
        logger.debug("Populating left sidebar")
        table_list = self._parent_child_rows["matched_tables"]

        # Tables
        self._left_sidebar_layout.addWidget(QLabel("Tables:"))
        self._table_checkboxes = []
        for tname in table_list:
            cb = QCheckBox(tname)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_table_checkbox_toggled)
            self._left_sidebar_layout.addWidget(cb)
            self._table_checkboxes.append(cb)

        # Searches
        self._left_sidebar_layout.addWidget(QLabel("Searches:"))
        self._search_checkboxes = []
        # Map each search's get_sql() -> class name for reverse lookup
        self._search_sql_to_name = {}
        for search in self._related_searches:
            name = search.__class__.__name__
            sql = search.get_sql()
            self._search_sql_to_name[sql] = name

        # Use the class name as the checkbox label
        # (each is checked by default)
        for sql, name in self._search_sql_to_name.items():
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_search_checkbox_toggled)
            self._left_sidebar_layout.addWidget(cb)
            self._search_checkboxes.append(cb)

        # Processes
        self._left_sidebar_layout.addWidget(QLabel("Processes:"))
        self._process_checkboxes = []
        for proc in self._related_processes:
            cb = QCheckBox(proc.__name__)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_process_checkbox_toggled)
            self._left_sidebar_layout.addWidget(cb)
            self._process_checkboxes.append(cb)

        self._left_sidebar_layout.addStretch()

    def _on_table_checkbox_toggled(self, state: int) -> None:
        """
        Handler for toggling table checkboxes. Updates the set of selected tables and applies filters.

        Args:
            state (int): The checkbox state (checked/unchecked).
        """
        logger.debug("Table checkbox toggled")
        self._selected_tables.clear()
        # Re-collect any that remain checked
        for cb in self._table_checkboxes:
            if cb.isChecked():
                self._selected_tables.add(cb.text())
        self._apply_filters()


    def _on_search_checkbox_toggled(self, state: int) -> None:
        """
        Handler for toggling search checkboxes. Updates the set of selected searches and applies filters.

        Args:
            state (int): The checkbox state (checked/unchecked).
        """
        logger.debug("Search checkbox toggled")
        self._selected_searches.clear()
        for cb in self._search_checkboxes:
            if cb.isChecked():
                self._selected_searches.add(cb.text())
        self._apply_filters()


    def _on_process_checkbox_toggled(self, state: int) -> None:
        """
        Handler for toggling process checkboxes. Updates the set of selected processes and applies filters.

        Args:
            state (int): The checkbox state (checked/unchecked).
        """
        logger.debug("Process checkbox toggled")
        self._selected_processes.clear()
        for cb in self._process_checkboxes:
            if cb.isChecked():
                self._selected_processes.add(cb.text())
        self._apply_filters()



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

    def _apply_filters(self) -> None:
        """
        Applies filters based on selected tables, searches, and processes to hide/show the widgets
        in the children/parents sections.
        """
        logger.debug("Applying filters to children/parents sections")
        # If no processes are selected, that constraint is ignored (everything is shown for processes).
        for (section_type, search_name, table_name), (widget, proc_set) in self._section_widgets.items():
            show_widget = True

            # Filter by table
            if table_name not in self._selected_tables:
                show_widget = False

            # Filter by search
            if search_name not in self._selected_searches:
                show_widget = False

            # Filter by process
            # If we have selected processes, require intersection
            if self._selected_processes and not (self._selected_processes.intersection(proc_set)):
                show_widget = False

            widget.setVisible(show_widget)














    def _populate_center_view(self, current_search: FileSearchBase) -> None:
        """
        Populates the center area with three sections:
        1) This datum (table-only view).
        2) Children (each search can toggle between table/grid).
        3) Parents (each search can toggle between table/grid).
        """
        logger.debug("Populating center view sections")

        # -- THIS DATUM SECTION --
        this_datum_container = QWidget()
        this_datum_layout = QVBoxLayout(this_datum_container)
        lbl_this_datum = QLabel("This Datum (Table View Only)")
        lbl_this_datum.setStyleSheet("font-weight: bold;")
        this_datum_layout.addWidget(lbl_this_datum)

        # Fetch single record
        try:
            table_for_current_search = extract_table_names(current_search.get_sql())[0]
            conn = get_db_connection(self._db_path)
            cur = conn.cursor()
            sql = f"SELECT * FROM {str(table_for_current_search)} WHERE rowid=?"
            cur.execute(sql, (self._rowid,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                records = [dict(zip(columns, row))]
            else:
                records = []
            conn.close()
        except Exception as exc:
            logger.exception("Failed to fetch this datum record: %s", exc)
            records = []

        this_datum_table = self._create_single_table_view(records)
        this_datum_layout.addWidget(this_datum_table)
        self._center_container_layout.addWidget(this_datum_container)

        # -- CHILDREN SECTION --
        if "children" in self._parent_child_rows:
            children_container = QWidget()
            children_layout = QVBoxLayout(children_container)
            lbl_children = QLabel("Children")
            lbl_children.setStyleSheet("font-weight: bold;")
            children_layout.addWidget(lbl_children)

            for child_query, child_info in self._parent_child_rows["children"].items():
                matched_table = child_info.get("matched_table", "")
                matched_rows = child_info.get("matched_rows", [])
                # Attempt to map this child's SQL to the search class name
                # (fall back to raw query string if not found)
                search_name = self._search_sql_to_name.get(child_query, child_query)
                widget = self._create_table_and_grid_view(
                    search_name,
                    matched_table,
                    matched_rows,
                    section_type="children"
                )
                children_layout.addWidget(widget)

            self._center_container_layout.addWidget(children_container)

        # -- PARENTS SECTION --
        if "parents" in self._parent_child_rows:
            parents_container = QWidget()
            parents_layout = QVBoxLayout(parents_container)
            lbl_parents = QLabel("Parents")
            lbl_parents.setStyleSheet("font-weight: bold;")
            parents_layout.addWidget(lbl_parents)

            for parent_query, parent_info in self._parent_child_rows["parents"].items():
                matched_table = parent_info.get("matched_table", "")
                matched_rows = parent_info.get("matched_rows", [])
                search_name = self._search_sql_to_name.get(parent_query, parent_query)
                widget = self._create_table_and_grid_view(
                    search_name,
                    matched_table,
                    matched_rows,
                    section_type="parents"
                )
                parents_layout.addWidget(widget)

            self._center_container_layout.addWidget(parents_container)

        self._center_container_layout.addStretch()







    def _create_single_table_view(self, records: List[Dict[str, Any]]) -> QTableWidget:
        """
        Creates a QTableWidget displaying a single record (or empty if no records).

        Args:
            records (List[Dict[str, Any]]): The records to display (expected to contain one).

        Returns:
            QTableWidget: The table widget populated with the single record.
        """
        logger.debug("Creating single-table view for 'this datum'")
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        if not records:
            return table_widget

        columns = list(records[0].keys())
        table_widget.setColumnCount(len(columns))
        table_widget.setHorizontalHeaderLabels(columns)
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        for idx, rec in enumerate(records):
            table_widget.insertRow(idx)
            for col_idx, col_key in enumerate(columns):
                cell_value = str(rec.get(col_key, ""))
                table_widget.setItem(idx, col_idx, QTableWidgetItem(cell_value))

        return table_widget


    def _create_table_and_grid_view(
        self,
        search_name: str,
        table_name: str,
        row_dicts: List[sqlite3.Row],
        section_type: str
    ) -> QWidget:
        """
        Creates a container with a label, two buttons to switch between table and grid,
        and a QStackedWidget that holds both a table widget and a grid widget for the given row_dicts.

        Args:
            search_name (str): The name or identifier for the search.
            table_name (str): The name of the table referenced.
            row_dicts (List[sqlite3.Row]): The list of row objects.
            section_type (str): One of 'children' or 'parents' (used for filtering).

        Returns:
            QWidget: A container widget with table/grid switching.
        """
        logger.debug("Creating table/grid view for search=%s, table=%s, section=%s", search_name, table_name, section_type)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Title Label
        lbl_title = QLabel(f"{search_name} - {table_name}")
        lbl_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_title)

        # Buttons for switching
        btn_layout = QHBoxLayout()
        table_btn = QPushButton("Table View")
        grid_btn = QPushButton("Grid View")
        btn_layout.addWidget(table_btn)
        btn_layout.addWidget(grid_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Stacked Widget
        stack = QStackedWidget()
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        grid_widget = QListWidget()
        grid_widget.setViewMode(QListWidget.ViewMode.IconMode)
        grid_widget.setFlow(QListWidget.Flow.LeftToRight)
        grid_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid_widget.setIconSize(QSize(64, 64))

        # Convert row objects to dict
        records = []
        if row_dicts:
            cols = row_dicts[0].keys()
            for r in row_dicts:
                records.append({c: r[c] for c in cols})

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

                # Grid entry
                # TODO: logic to get image icon from row
                item = QListWidgetItem()
                item.setText(str(rec))
                grid_widget.addItem(item)

        stack.addWidget(table_widget)
        stack.addWidget(grid_widget)
        layout.addWidget(stack)

        def switch_to_table() -> None:
            stack.setCurrentIndex(0)

        def switch_to_grid() -> None:
            stack.setCurrentIndex(1)

        table_btn.clicked.connect(switch_to_table)
        grid_btn.clicked.connect(switch_to_grid)

        # Determine which processes reference this table
        processes_for_table = set()
        for proc in self._related_processes:
            for ds in proc.data_structures:  # Ensure correct matching by TABLE_NAME
                if getattr(ds, "TABLE_NAME", "") == table_name:
                    processes_for_table.add(proc.__name__)
                    break

        # Register widget for later filtering
        key = (section_type, search_name, table_name)
        self._section_widgets[key] = (container, processes_for_table)

        return container


# ****
if __name__ == "__main__":
    raise Exception("This module is not meant to be run on its own.")
