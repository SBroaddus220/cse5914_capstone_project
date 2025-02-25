# -*- coding: utf-8 -*-

"""
Dialog window for importing files.
"""

# **** IMPORTS ****
import logging
import markdown
from PyQt6.QtWidgets import (
    QVBoxLayout, QDialog, QLabel, QTextEdit
)

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class Help(QDialog):
   def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setGeometry(100, 100, 400, 300)
        self.init_ui()

   def init_ui(self):
        layout = QVBoxLayout()

        # Help dialog window content is stored in a separate Markdwon file.
        # help_content.md
        # Edits and alterations must be made there.
        with open("tagsense/views/help_content.md", "r") as file:
            markdown_content = file.read()

        help_text = markdown.markdown(markdown_content)
        
        self.help_label = QLabel("Help Guide", self)
        self.help_content = QTextEdit(self)
        self.help_content.setHtml(help_text)
        self.help_content.setReadOnly(True)

        layout.addWidget(self.help_label)
        layout.addWidget(self.help_content)
        
        self.setLayout(layout)

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
