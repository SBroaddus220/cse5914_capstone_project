# -*- coding: utf-8 -*-

"""
View module for viewing a specific piece of data.
"""

# **** IMPORTS ****
import sqlite3
import logging
from typing import List, Dict, Any
from PIL import ImageQt

from PyQt6.QtCore import QSize, Qt, QEvent

from PyQt6.QtGui import QPixmap, QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QCheckBox, QStackedWidget,
    QPushButton, QTableWidget, QAbstractItemView, QTableWidgetItem, QListWidget, QListWidgetItem, QDialog, QHeaderView
)
from PyQt6.QtWidgets import QSplitter, QSizePolicy

from tagsense import registry
from tagsense.searches.search import Search
from tagsense.processes.process import Process
from tagsense.widgets import CustomGridTableWidget
from tagsense.data_structures.data_structure import DataStructure
from tagsense.data_structures.manual_data_structure import ManualDataStructure

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class DataViewWindow(QMainWindow):
    """Window for viewing individual data records."""
    
    def __init__(self, current_search: Search, record_idx: int, parent=None) -> None:
        super().__init__(parent=parent)
        logger.info("Initializing data view window...")

        # Store attributes
        self.current_search = current_search
        self.record_idx = record_idx
        self.record = current_search.fetch_results()[record_idx]
        
        # ****
        # Initialize the UI
        self.init_ui()
        self.update_with_record(self.current_search, self.record_idx)
        
    def init_ui(self):
        # ****
        # Main window setup
        self.setWindowTitle("Data Viewer")
        self.showMaximized()
        
        self._main_widget = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self._main_widget)
        
        # ****
        # Left sidebar
        self._left_sidebar_widget = FocusableWidget()
        self._left_sidebar_layout = QVBoxLayout(self._left_sidebar_widget)
        self._left_scroll_area = QScrollArea()

        def resize_scroll_area_event(event):
            width = self._left_scroll_area.viewport().width()
            self._left_sidebar_widget.setFixedWidth(width)
            QScrollArea.resizeEvent(self._left_scroll_area, event)

        self._left_scroll_area.resizeEvent = resize_scroll_area_event
        self._left_scroll_area.setWidgetResizable(True)
        self._left_scroll_area.setWidget(self._left_sidebar_widget)

        # ****
        # Center container
        self._center_splitter = QSplitter(Qt.Orientation.Vertical)
        self._center_scroll_area = QScrollArea()
        self._center_scroll_area.setWidgetResizable(True)
        self._center_scroll_area.setWidget(self._center_splitter)
        
        self._main_widget.addWidget(self._left_scroll_area)
        self._main_widget.addWidget(self._center_scroll_area)
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Handle left/right arrow key presses for navigating records
        logger.debug(f"Key pressed: {event.key()}")
        if event.key() == Qt.Key.Key_Left:
            self.prev_record()
        elif event.key() == Qt.Key.Key_Right:
            self.next_record()
        else:
            super().keyPressEvent(event)
    
    def prev_record(self) -> None:
        """Moves to the previous record."""
        if self.record_idx > 0:
            self.record_idx -= 1
            self.update_with_record(self.current_search, self.record_idx)
    
    def next_record(self) -> None:
        """Moves to the next record."""
        if self.record_idx < len(self.current_search.fetch_results()) - 1:
            self.record_idx += 1
            self.update_with_record(self.current_search, self.record_idx)

    def _reset_left_sidebar(self):
        # Remove and delete all items/widgets in the layout
        while self._left_sidebar_layout.count():
            item = self._left_sidebar_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                # If it’s not a widget, it could be a sub-layout
                sub_layout = item.layout()
                if sub_layout is not None:
                    # Recursively clear sub-layout
                    while sub_layout.count():
                        sub_item = sub_layout.takeAt(0)
                        sub_widget = sub_item.widget()
                        if sub_widget is not None:
                            sub_widget.deleteLater()
        
    def _populate_left_sidebar(self) -> None:
        logger.debug("Resetting left sidebar...")
        self._reset_left_sidebar()
        logger.debug("Populating left sidebar...")
        
        # ****
        # Add thumbnail
        thumbnail = self.current_search.generate_thumbnail(self.record)
        pixmap = QPixmap.fromImage(ImageQt.ImageQt(thumbnail))

        # Create label
        thumbnail_label = QLabel()
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setScaledContents(False)  # We'll scale manually to preserve aspect ratio
        thumbnail_label.original_pixmap = pixmap  # Save original pixmap

        # Override resize event using a subclass or lambda
        def resize_event(event):
            container_width = thumbnail_label.width()
            original_pixmap = thumbnail_label.original_pixmap
            scaled_pixmap = original_pixmap.scaledToWidth(container_width, Qt.TransformationMode.SmoothTransformation)
            thumbnail_label.setPixmap(scaled_pixmap)

        # Dynamically bind the resizeEvent
        thumbnail_label.resizeEvent = resize_event

        # Add to layout
        self._left_sidebar_layout.addWidget(thumbnail_label)
        
        # ****
        # Populate searches
        self._searches = set()
        self._search_checkboxes = []
        
        # Current search
        self._searches.add(self.current_search)
        
        # Related searches
        for relation, data in self.related_data.items():
            for search in data["searches"]:
                self._searches.add(search)
        
        self._left_sidebar_layout.addWidget(QLabel("Searches:"))
        for search in self._searches:
            search: Search
            checkbox = QCheckBox(search.name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_search_checkbox_toggled)
            self._left_sidebar_layout.addWidget(checkbox)
            self._search_checkboxes.append(checkbox)
            
        # ****
        # Populate Data Structures
        self._data_structures = set()
        self._data_structure_checkboxes = []
        for search in self._searches:
            self._data_structures.add(search.data_structure)
            
        self._left_sidebar_layout.addWidget(QLabel("Data Structures:"))
        for data_structure in self._data_structures:
            data_structure: DataStructure
            checkbox = QCheckBox(data_structure.uid)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_data_structure_checkbox_toggled)
            self._left_sidebar_layout.addWidget(checkbox)
            self._data_structure_checkboxes.append(checkbox)
            
        # ****
        # Populate Processes
        self._processes = set()
        self._process_checkboxes = []
        for relation, data in self.related_data.items():
            self._processes.add(data["process"])
        
        self._left_sidebar_layout.addWidget(QLabel("Processes:"))
        for process in self._processes:
            process: Process
            checkbox = QCheckBox(process.uid)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_process_checkbox_toggled)
            self._left_sidebar_layout.addWidget(checkbox)
            self._process_checkboxes.append(checkbox)
            
        self._left_sidebar_layout.addStretch()

    def update_with_record(self, current_search: Search, record_idx: int) -> None:
        """Updates the window with a new record and search."""
        self.current_search = current_search
        self.record_idx = record_idx
        self.record = current_search.fetch_results()[record_idx]
        
        # ****
        # Find parent & child records

        # For every search, for every record, we need to record the related processes and data structures for sorting purposes
        self.parent_data: list[dict] = {}
        self.children_data: list[dict] = {}

        # e.g.
        # [
        #     (DataStructure, record_key_01): {
        #         "searches": {search_01, search_02},
        #         "process": process,
        #     }
        # ]

        # Flip search registry to be a dictionary of data structures to searches
        data_structure_to_searches = {}
        for search in registry.search_registry:
            if search.data_structure not in data_structure_to_searches:
                data_structure_to_searches[search.data_structure] = set()
            data_structure_to_searches[search.data_structure].add(search)

        # Find children
        for process in registry.installed_processes:
            # Filter any process that can't have the current record as input
            if not process.input == current_search.data_structure:
                continue
            
            # Check if the output data structure contains a reference to the current record
            output_data_structure = process.output
            child = output_data_structure.read_by_input_key(
                current_search.data_structure.fetch_entry_key_from_entry(self.record)
            )
            if not child:
                continue
            child = dict(child)

            # Check if child record already exists
            child_entry_key = output_data_structure.fetch_entry_key_from_entry(child)
            if (output_data_structure, child_entry_key) in self.children_data:
                raise ValueError("Child record already exists. Should not happen.")

            # Add child record
            self.children_data[(output_data_structure, child_entry_key)] = {
                "searches": data_structure_to_searches[output_data_structure],
                "process": process,
            }

        # Find parent
        parent_data_structure = registry.fetch_data_structure_by_uid(
            current_search.data_structure.fetch_input_data_structure_uid_from_entry(self.record)
        )
        if parent_data_structure and not parent_data_structure.uid == ManualDataStructure.uid:
            self.parent_data[
                (
                    parent_data_structure,
                    current_search.data_structure.fetch_input_data_key_from_entry(self.record)
                )
                ] = {
                    "searches": data_structure_to_searches[parent_data_structure],
                    "process": registry.fetch_process_by_uid(
                        current_search.data_structure.fetch_process_uid_from_entry(self.record),
                    )
                }
            
        # Create combined dictionary for sorting
        self.related_data = {**self.parent_data, **self.children_data}

        # ****
        self._populate_left_sidebar()
        self._populate_center_container()
        
    def _on_search_checkbox_toggled(self, state: int) -> None:
        logger.debug("Search checkbox toggled.")
        self._populate_center_container()
        
    def _on_data_structure_checkbox_toggled(self, state: int) -> None:
        logger.debug("Data structure checkbox toggled.")
        self._populate_center_container()
        
    def _on_process_checkbox_toggled(self, state: int) -> None:
        logger.debug("Process checkbox toggled.")
        self._populate_center_container()
        
    def update_center_container(self, filtered_parents, filtered_children, current_search) -> None:
        """
        Updates the center container with filtered parent and child data along with the current search.

        Args:
            filtered_parents (dict): Filtered parent data in the format {parent_key: {"searches": set}}.
            filtered_children (dict): Filtered child data in the format {child_key: {"searches": set}}.
            current_search (str): The current search to display.
        """
        logger.debug("Updating center container...")

        # Clear existing widgets from the layout
        while self._center_splitter.count():
            widget = self._center_splitter.widget(0)
            self._center_splitter.widget(0).setParent(None)
            widget.deleteLater()
                
        # ****
        # Filter records based on checkboxes
        valid_data_structures = set()
        valid_searches = set()
        valid_processes = set()
        
        for checkbox in self._data_structure_checkboxes:
            if checkbox.isChecked():
                valid_data_structures.add(
                    registry.fetch_data_structure_by_uid(checkbox.text())
                )
        
        for checkbox in self._search_checkboxes:
            if checkbox.isChecked():
                valid_searches.add(
                    registry.fetch_search_by_name(checkbox.text())
                )

        for checkbox in self._process_checkboxes:
            if checkbox.isChecked():
                valid_processes.add(
                    registry.fetch_process_by_uid(checkbox.text())
                )
                
        filtered_parents = self.filter_records(filtered_parents, valid_data_structures, valid_searches, valid_processes)
        filtered_children = self.filter_records(filtered_children, valid_data_structures, valid_searches, valid_processes)
        parent_entry_keys = [key for _, key in filtered_parents.keys()]
        child_entry_keys = [key for _, key in filtered_children.keys()]

        # ****
        # Populate current search section
        current_search_widget = CustomGridTableWidget(
            [current_search], 
            parent=self, 
            window_class=self.__class__,
            entry_whitelist=self.current_search.data_structure.fetch_entry_key_from_entry(self.record)
            )
        self._center_splitter.addWidget(current_search_widget)

        # ****
        # Populate parent section
        parent_widget_container = QWidget()
        parent_widget_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        parent_widget_container_layout = QVBoxLayout(parent_widget_container)

        if parent_entry_keys:
            parents_label = QLabel("Parents:")
            parent_widget_container_layout.addWidget(parents_label)
        if filtered_parents:
            for (parent_ds, parent_entry_key), data in filtered_parents.items():
                parent_widget = CustomGridTableWidget(
                    list(data["searches"]),
                    parent=self,
                    window_class=self.__class__,
                    entry_whitelist=parent_entry_keys
                )
                parent_widget_container_layout.addWidget(parent_widget)

        self._center_splitter.addWidget(parent_widget_container)

        # ****
        # Populate children section
        children_widget_container = QWidget()
        children_widget_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        children_widget_container_layout = QVBoxLayout(children_widget_container)

        if child_entry_keys:
            children_label = QLabel("Children:")
            children_widget_container_layout.addWidget(children_label)
        for (child_ds, child_entry_key), data in filtered_children.items():
            child_widget = CustomGridTableWidget(
                list(data["searches"]),
                parent=self,
                window_class=self.__class__,
                entry_whitelist=child_entry_keys
            )
            children_widget_container_layout.addWidget(child_widget)

        self._center_splitter.addWidget(children_widget_container)
            
    def _populate_center_container(self) -> None:
        logger.debug("Populating center container...")
        self.update_center_container(self.parent_data, self.children_data, self.current_search)

    def filter_records(self, records, valid_data_structures, valid_searches, valid_processes):
        """
        Filters records based on valid data structures, searches, and processes.

        Args:
            records (list): A list of records to filter following the format of `self.related_data`.
            valid_data_structures (set): A set of allowed data structures.
            valid_searches (set): A set of allowed searches.
            valid_processes (set): A set of allowed processes.

        Returns:
            dict: A dictionary of filtered records.
        """
        filtered_records = {}

        for (data_structure, record_key), record_data in records.items():
            # Check if the data structure is valid
            if data_structure not in valid_data_structures:
                continue

            # Check if any of the searches are valid
            if not record_data["searches"].intersection(valid_searches):
                continue

            # Check if the process is valid
            if record_data["process"] not in valid_processes:
                continue

            # If all conditions are met, keep the record
            filtered_records[(data_structure, record_key)] = record_data

        return filtered_records

class FocusableWidget(QWidget):
    """A widget that can receive focus."""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event):
        """Focus widget when empty space is clicked."""
        logger.debug("Focusable widget clicked.")
        self.setFocus()
        super().mousePressEvent(event)
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if window := self.window():
            logger.debug(f"Forwarding key press to parent window: {window} with event: {event}")
            window.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

# ****
if __name__ == "__main__":
    raise Exception("This module is not meant to be run on its own.")
