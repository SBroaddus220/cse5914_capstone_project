# -*- coding: utf-8 -*-

"""
Dialog window for application settings.
"""

# **** IMPORTS ****
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton
)

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class Settings(QDialog):
   def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 300, 150)
        self.init_ui()
        
   def init_ui(self):
        layout = QVBoxLayout()

        # Placeholder switches
        self.switch1 = QCheckBox("Enable Feature 1", self)
        self.switch2 = QCheckBox("Enable Feature 2", self)
        layout.addWidget(self.switch1)
        layout.addWidget(self.switch2)

        # Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)  # Closes the dialog
        layout.addWidget(self.save_button)

        self.setLayout(layout)

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
