# -*- coding: utf-8 -*-

"""
Dialog window for importing files.
"""

# **** IMPORTS ****
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Set, Optional
from collections import deque

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QSplitter, QGroupBox, QWidget, QCheckBox,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox,
    QScrollArea
)

from tagsense import registry
from tagsense.widgets import RunProcessesWidget
from tagsense.util import sort_processes
from tagsense.data_structures.manual_data_structure import ManualDataStructure
from tagsense.processes.process import Process

from tagsense.processes.processes.file_system_integration.file_system_integration import FileSystemIntegration

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class FileImport(QDialog):
    """Dialog for importing files and running processes."""

    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:
        """Initializes window and its UI elements."""
        super().__init__(parent)
        self.setWindowTitle("Import Files")
        self.setGeometry(100, 100, 1200, 750)
        self.conn = conn
        
        # Fetch processes
        self.processes = registry.fetch_installed_processes()

        # Sort processes to ensure dependencies are run first
        # TODO: Identify dependencies and determine good way to inform user
        self.processes: List[Process] = sort_processes(self.processes)
        
        # Ensure file system integration is present and in the first position
        # Find the correct FileSystemIntegration class from the process list
        FileSystemIntegration = next(
            (proc for proc in self.processes if getattr(proc, "name", None) == "file_system_integration"),
            None  # Default to None if not found
        )

        # If the process is missing, raise an error
        if FileSystemIntegration is None:
            raise Exception("File System Integration process is required.")
        self.processes.remove(FileSystemIntegration)
        self.processes.insert(0, FileSystemIntegration)

        # ****
        # Build the layout
        self.init_ui_layout()

    def init_ui_layout(self) -> None:
        """Initializes the layout for the UI."""
        # ****
        # File selection
        self.file_path_lineedit = QLineEdit(self)
        self.file_path_lineedit.setReadOnly(True)
        
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.open_file_dialog)

        # ****
        # Top layout: file selection
        file_selection_widget = QWidget()
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(self.file_path_lineedit)
        file_selection_layout.addWidget(self.browse_button)
        file_selection_layout.addStretch(1)
        file_selection_widget.setLayout(file_selection_layout)

        # ****
        # Processes
        self.run_selected_processes_widget = RunFileProcessesWidget(self.processes, None, self)

        # ****
        # Splitter for vertical sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(file_selection_widget)
        splitter.addWidget(self.run_selected_processes_widget)
        
        # ****
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def open_file_dialog(self) -> None:
        """Opens a file selection dialog."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Import Media")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        # Select files
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                for file in selected_files:
                    self.set_file_path(file)

    def set_file_path(self, file_path: Path) -> None:
        """Performs necessary checks and sets the file path."""
        logger.info(f"Selected file: {file_path}")
        self.file_path_lineedit.setText(str(file_path))
        self.run_selected_processes_widget.update_file_path(file_path)
        self.run_selected_processes_widget.reset_processes()

class RunFileProcessesWidget(RunProcessesWidget):
    def __init__(self, processes: List, file_path: Optional[Path], parent: QWidget) -> None:
        # ****
        # Creates manual data structure entry for file path
        self.data_structures_to_entry_keys = {}
        if file_path:
            self.update_file_path(file_path)
        super().__init__(processes, self.data_structures_to_entry_keys, parent)
        
    def update_file_path(self, file_path: Path) -> None:
        """Updates the file path for the manual data structure."""
        manual_entry_data = {
            "file_path": file_path
        }
        manual_entry_key = ManualDataStructure.create_entry(manual_entry_data)
        if ManualDataStructure in self.data_structures_to_entry_keys:
            self.data_structures_to_entry_keys[ManualDataStructure].append(manual_entry_key)
        else:
            self.data_structures_to_entry_keys[ManualDataStructure] = [manual_entry_key]
        

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")


