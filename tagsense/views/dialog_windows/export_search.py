# -*- coding: utf-8 -*-

"""
Dialog window for exporting search results.
"""

# **** IMPORTS ****
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QComboBox, QPushButton, QFileDialog
)

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class ExportSearch(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Search")
        self.setGeometry(100, 100, 400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Checkbox for including metadata
        self.metadata_checkbox = QCheckBox("Include metadata", self)
        layout.addWidget(self.metadata_checkbox)

        # Dropdown for selecting export file type
        self.file_type_dropdown = QComboBox(self)
        self.file_type_dropdown.addItems(["CSV", "JSON"])
        layout.addWidget(self.file_type_dropdown)

        # Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.open_save_dialog)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    #TODO (get details from user selections, etc)
    def build_file_to_save(self):
       ... 

    #TODO (finish)
    def open_save_dialog(self):

        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Save File")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        
        if file_dialog.exec():
           selected_file = file_dialog.selectedFiles()[0]
           print("Selected File for Saving:", selected_file)
           self.accept() # this automatically closes the dialog window

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
