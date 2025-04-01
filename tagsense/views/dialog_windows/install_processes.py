# -*- coding: utf-8 -*-

"""
Dialog window for installing processes.
"""

# **** IMPORTS ****
import traceback
import logging
from typing import List, Any, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QPushButton,
    QLabel, QGroupBox, QPlainTextEdit, QMessageBox, QDialogButtonBox
)

from tagsense import registry
from tagsense.widgets import RunProcessesWidget, ProcessWorkerBase

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class InstallProcessesDialog(QDialog):
    """Dialog that allows users to install available processes."""
    def __init__(self, parent=None) -> None:
        # ****
        super().__init__(parent)
        self.setWindowTitle("Install Processes")
        self.setGeometry(100, 100, 600, 400)

        # ****
        # Fetch processes to install
        self.processes = registry.process_registry - registry.installed_processes
        
        # ****
        # Define layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # ****
        self.install_processes_widget = InstallProcessesWidget(self.processes)
        self.main_layout.addWidget(self.install_processes_widget)
        
class InstallProcessWorker(ProcessWorkerBase):
    def run(self):
        try:
            self._emit_output_from_callable(self.process.install)
            self.finished.emit("Installed", {})
        except Exception as e:
            pass
        finally:
            self.finished.emit("Failed", {})

class InstallProcessesWidget(RunProcessesWidget):
    def __init__(self, processes: List, parent=None) -> None:
        super().__init__(processes, data_structures_to_entry_keys=None, parent=parent)
        self.processes = processes

    def _init_ui(self) -> None:
        super()._init_ui()
        self.process_button.setText("Install")

    def run_process(self, process):
        """Runs the install process asynchronously in a worker thread."""
        self.run_worker(InstallProcessWorker, process)
    
    def handle_process_completion(self, process, msg: str, data: dict) -> bool:
        return True

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run standalone.")
