import sys
import markdown
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QLineEdit, QListWidget, QCheckBox, QLabel,
    QVBoxLayout, QHBoxLayout, QListWidgetItem, QComboBox, QFrame, QFileDialog, QPushButton, QDialog, QTextEdit
)

class MediaImport(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Media")
        self.resize(200, 100)
        self.init_ui()

    def init_ui(self):
      self.setWindowTitle("Import Media")
      self.setGeometry(100, 100, 400, 300)

      self.button = QPushButton("Browse Files", self)
      self.button.clicked.connect(self.openFileDialog)
      self.button.setGeometry(150, 150, 100, 30)

    def openFileDialog(self):
      file_dialog = QFileDialog(self)
      file_dialog.setWindowTitle("Import Media")
      file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
      file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

      if file_dialog.exec():
         selected_files = file_dialog.selectedFiles()
         print("Selected File:", selected_files[0])

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