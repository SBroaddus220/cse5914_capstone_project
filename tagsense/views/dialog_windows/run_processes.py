# -*- coding: utf-8 -*-

"""
Dialog window for running processes.
"""

# **** IMPORTS ****
import time
import logging
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, QWidget, QCheckBox,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QMessageBox, QScrollArea,
    QScrollBar
)
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QAbstractItemView

from tagsense import registry
from tagsense.config import DB_PATH
from tagsense.util import create_divider
from tagsense.data_structures.data_structure import DataStructure
from tagsense.util import CustomGridTableWidget, RunProcessesWidget

# **** LOGGER ****
# Sets up logger
logger = logging.getLogger(__name__)

# **** CLASSES ****
class RunProcesses(QDialog):
    """Dialog for running processes."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Run Processes")
        self.setGeometry(100, 100, 800, 600)
        
        # ****
        # Fetch data structures and processes
        self.data_structures: List[DataStructure] = registry.detected_data_structures
        self.processes = registry.installed_processes
        
        # ****
        # Define layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # ***
        # Combo box for selecting data structure
        self.data_structure_dropdown = QComboBox()
        # Insert a placeholder so that index 0 = "no selection"
        self.data_structure_dropdown.addItem("-- Select Data Structure --", userData=None)
        
        # Populate with actual data structures starting at index 1
        for ds in self.data_structures:
            self.data_structure_dropdown.addItem(ds.uid, ds)
        
        self.data_structure_dropdown.currentIndexChanged.connect(self.on_data_structure_selected)
        self.main_layout.addWidget(self.data_structure_dropdown)
        
        # ***
        # Selection widget & run‐processes widget
        # We keep references to them; initially, we create empty (hidden) placeholders
        self.selection_widget = QWidget(self)
        self.selection_widget.hide()
        self.main_layout.addWidget(self.selection_widget)

        self.run_processes_widget = QWidget(self)
        self.run_processes_widget.hide()
        self.main_layout.addWidget(self.run_processes_widget)

    def on_data_structure_selected(self, index: int) -> None:
        """Called whenever the user changes the combo box selection."""
        # Clear out old widgets
        if self.selection_widget is not None:
            self.main_layout.removeWidget(self.selection_widget)
            self.selection_widget.deleteLater()
            self.selection_widget = None
        
        if self.run_processes_widget is not None:
            self.main_layout.removeWidget(self.run_processes_widget)
            self.run_processes_widget.deleteLater()
            self.run_processes_widget = None

        # Remove any existing "no processes" label if present
        if hasattr(self, "no_processes_label") and self.no_processes_label is not None:
            self.main_layout.removeWidget(self.no_processes_label)
            self.no_processes_label.deleteLater()
            self.no_processes_label = None
        
        # If the user picked the placeholder (“no data structure”) or no valid index
        if index <= 0 or index >= self.data_structure_dropdown.count():
            # Just hide both widgets (or do nothing, as we have deleted them)
            self.selection_widget = QWidget(self)
            self.selection_widget.hide()
            self.main_layout.addWidget(self.selection_widget)
            
            self.run_processes_widget = QWidget(self)
            self.run_processes_widget.hide()
            self.main_layout.addWidget(self.run_processes_widget)
            
            return
        
        # ****
        # Valid data structure was selected
        data_structure: DataStructure = self.data_structure_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        
        # Filter the searches for the selected data structure
        self.searches = [
            search for search in registry.search_registry
            if search.data_structure.uid == data_structure.uid
        ]
        
        # Create a new selection widget
        self.selection_widget = SelectionGridTableWidget(
            searches=self.searches,
            parent=self,
            window_class=None,
            entry_whitelist=None,
            entry_blacklist=None
        )
        self.main_layout.addWidget(self.selection_widget)
        self.selection_widget.show()
        
        # Identify processes that can take the selected data structure
        processes = [
            proc for proc in self.processes
            if proc.input.uid == data_structure.uid
        ]

        if not processes:
            self.no_processes_label = QLabel("No processes detected for this data structure.")
            self.main_layout.addWidget(self.no_processes_label)
            return

        # Otherwise, create/run processes widget (as before)
        self.run_processes_widget = RunProcessesWidget(
            processes=processes,
            data_structures_to_entry_keys={
                data_structure: data_structure.fetch_all_entry_keys()
            },
            parent=self
        )
        self.main_layout.addWidget(self.run_processes_widget)
        self.run_processes_widget.show()
                
class SelectionGridTableWidget(CustomGridTableWidget):
    """Custom grid table widget for displaying data structure items."""
    def __init__(
        self, 
        searches: list, 
        parent=None, 
        window_class=None, 
        entry_whitelist=None, 
        entry_blacklist=None
    ):
        super().__init__(
            searches=searches,
            parent=parent,
            window_class=window_class,
            entry_whitelist=entry_whitelist,
            entry_blacklist=entry_blacklist
        )        

        # ****
        # Allow row selection
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_widget.itemClicked.connect(self.handle_table_item_click)

        self.grid_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid_widget.itemClicked.connect(self.handle_grid_item_click)

        self._selected_records = []
        
    def handle_table_item_click(self, item: QTableWidgetItem) -> None:
        row_idx = item.row()
        record = self.get_row_data(self.table_widget, row_idx)

        # Add/remove from _selected_records
        if record in self._selected_records:
            self._selected_records.remove(record)
        else:
            self._selected_records.append(record)
            
    def handle_grid_item_click(self, item: QListWidgetItem) -> None:
        row_idx = self.grid_widget.row(item)
        record = self.get_row_data(self.table_widget, row_idx)

        # Add/remove from _selected_records
        if record in self._selected_records:
            self._selected_records.remove(record)
        else:
            self._selected_records.append(record)


    def get_selected_records(self):
        """Convenience method to retrieve all currently selected records."""
        return self._selected_records

        

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run standalone.")
