# -*- coding: utf-8 -*-

"""
Dialog windows for application.
"""

# ****
import os
import time
import logging
import markdown
from typing import Dict, Any
import json
from PyQt6.QtWidgets import (
    QDialog,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QWidget,
    QLabel,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFileDialog

from tagsense.config import DB_PATH
from tagsense.processes.preprocessing import FilePreprocessing, ExtractFileMetadataProcess
# from tagsense.processes.grayscale.grayscale import GrayscaleImageProcess
from tagsense.processes.exampleprocesses.testprocesses import AppendTextProcess, SingleRunProcess

# **** LOGGING ****
# Set up logger
logger = logging.getLogger(__name__)

# **** Helper Functions ****
def create_divider(name: str, total_width: int = 50) -> str:
    """Creates a divider line with the given name centered among dashes."""
    prefix = "# "
    name_len = len(name)
    max_name_space = total_width - len(prefix)
    if name_len >= max_name_space:
        return f"# {name}"
    space_for_dashes = max_name_space - name_len
    left = space_for_dashes // 2
    right = space_for_dashes - left
    return prefix + ("-" * left) + name + ("-" * right)

# **** Dialog Windows ****
class MediaImport(QDialog):
    """Dialog for importing media files and running processes."""

    def __init__(self, parent=None):
        """
        Initializes the MediaImport dialog and its UI elements.
        """
        super().__init__(parent)
        self.setWindowTitle("Import Media")
        self.setGeometry(100, 100, 600, 500)

        # Core (mandatory) processes that cannot be deselected
        self.core_processes = [
            FilePreprocessing(),
            ExtractFileMetadataProcess()
        ]

        # Optional user-selectable processes
        self.user_processes = [
            # GrayscaleImageProcess(),
            AppendTextProcess(),
            SingleRunProcess()
        ]

        # Combine them for display; core first, then user
        self.process_list = self.core_processes + self.user_processes

        # Define key widgets BEFORE init_processes_ui
        self.file_path_lineedit = QLineEdit(self)
        self.file_path_lineedit.setReadOnly(True)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.open_file_dialog)

        self.file_info_text = QPlainTextEdit(self)
        self.file_info_text.setReadOnly(True)

        self.processes_group = QGroupBox("Processes")
        self.process_checkboxes = []
        self.process_lineedits = []

        # Define self.process_button so it's available when init_processes_ui calls update_process_button_state
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.run_selected_processes)

        # Define cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)

        # Now safe to call init_processes_ui
        self.init_processes_ui()

        # Define output text
        self.output_text = QPlainTextEdit(self)
        self.output_text.setReadOnly(True)

        # Finally, build the layout
        self.init_ui_layout()

    def init_ui_layout(self) -> None:
        """
        Builds the main UI layout with vertical splitters. 
        """
        # Top layout: file selection
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        top_layout.addWidget(self.file_path_lineedit)
        top_layout.addWidget(self.browse_button)
        top_layout.addStretch(1)

        # File info layout
        file_info_layout = QVBoxLayout()
        file_info_label = QLabel("File Details (dictionary):")
        file_info_layout.addWidget(file_info_label)
        file_info_layout.addWidget(self.file_info_text)

        # Combine top/browse with file info
        top_section = QWidget()
        top_section_layout = QVBoxLayout()
        top_section_layout.addLayout(top_layout)
        top_section_layout.addLayout(file_info_layout)
        top_section.setLayout(top_section_layout)

        # Processes section
        processes_section = QWidget()
        processes_section_layout = QVBoxLayout()
        processes_section_layout.addWidget(self.processes_group)
        processes_section.setLayout(processes_section_layout)

        # Output section
        output_section = QWidget()
        output_section_layout = QVBoxLayout()
        output_label = QLabel("Process Output:")
        output_section_layout.addWidget(output_label)
        output_section_layout.addWidget(self.output_text)
        output_section.setLayout(output_section_layout)

        # Use a QSplitter for vertical sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top_section)
        splitter.addWidget(processes_section)
        splitter.addWidget(output_section)
        splitter.setCollapsible(2, True)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.process_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)


    def init_processes_ui(self) -> None:
        self.process_checkboxes = []
        self.process_lineedits = []
        self.process_status_lineedits = []
        self.process_help_buttons = []
        self.process_rows = []

        self.process_start_times = {}
        self.process_end_times = {}
        self.current_process_index = None

        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_all_process_statuses)

        self.processes_scroll_area = QScrollArea()
        self.processes_scroll_area.setWidgetResizable(True)
        container = QWidget()
        v_layout = QVBoxLayout()

        select_all_widget = QWidget()
        select_all_layout = QHBoxLayout(select_all_widget)
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.clicked.connect(self.select_all_processes)
        select_all_layout.addWidget(self.select_all_checkbox)
        select_all_layout.addStretch(1)
        v_layout.addWidget(select_all_widget)

        for i, process in enumerate(self.process_list):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)

            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_process_button_state)

            lineedit = QLineEdit(process.__class__.__name__)
            status_lineedit = QLineEdit("Not Started")
            status_lineedit.setReadOnly(True)

            help_button = QPushButton("Help")
            help_button.clicked.connect(lambda checked, p=process: self.show_help(p))

            if process in self.core_processes:
                # Always checked & disabled
                checkbox.setChecked(True)
                checkbox.setDisabled(True)

            self.process_checkboxes.append(checkbox)
            self.process_lineedits.append(lineedit)
            self.process_status_lineedits.append(status_lineedit)
            self.process_help_buttons.append(help_button)
            self.process_rows.append(row_widget)

            self.process_start_times[i] = None
            self.process_end_times[i] = None

            row_layout.addWidget(checkbox)
            row_layout.addWidget(lineedit)
            row_layout.addWidget(status_lineedit)
            row_layout.addWidget(help_button)
            v_layout.addWidget(row_widget)

        container.setLayout(v_layout)
        self.processes_scroll_area.setWidget(container)

        layout = QVBoxLayout()
        layout.addWidget(self.processes_scroll_area)
        self.processes_group.setLayout(layout)

        # Update the button state after creation
        self.update_process_button_state()

    def open_file_dialog(self) -> None:
        """Opens a file selection dialog."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Import Media")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.set_file_path(selected_files[0])

    def set_file_path(self, file_path: str) -> None:
        """
        Sets the file path, resets process checkboxes, then checks if the new file
        is already in DB. If so, disables or unchecks certain processes if they're
        non-repeatable and already done, whether core or user-created.
        """
        import hashlib
        import sqlite3
        from tagsense.models.file_table import FileTable
        from tagsense.models.file_core_metadata import FileCoreMetadataTable

        logging.info("Setting file path.")
        self.file_path_lineedit.setText(file_path)

        # 1) Reset all processes to their default "unchecked + enabled" state,
        #    except core processes -> checked + disabled
        for i, process in enumerate(self.process_list):
            cb = self.process_checkboxes[i]
            lineedit = self.process_lineedits[i]
            statusedit = self.process_status_lineedits[i]

            self.process_rows[i].setStyleSheet("")
            statusedit.setText("Not Started")

            if process in self.core_processes:
                cb.setChecked(True)
                cb.setDisabled(True)
                lineedit.setText(process.__class__.__name__)
            else:
                cb.setChecked(False)
                cb.setDisabled(False)
                lineedit.setText(process.__class__.__name__)

        # 2) Display file info
        file_info = self.get_file_info(file_path)
        self.file_info_text.setPlainText(json.dumps(file_info, indent=4))

        # 3) Compute MD5 of the new file
        def _calculate_md5(path: str) -> str:
            hash_md5 = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        md5_hash = _calculate_md5(file_path)

        # 4) Check if this MD5 already exists in DB
        db_path = DB_PATH
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            f"SELECT rowid FROM {FileTable.TABLE_NAME} WHERE md5_hash = ?",
            (md5_hash,)
        ).fetchone()

        existing_rowid = None
        if row:
            existing_rowid = row[0]
            self.output_text.appendPlainText(f"File with MD5 {md5_hash} found (rowid={existing_rowid}).\n")

            # 4A) We already handle the core metadata table example:
            meta_row = conn.execute(
                f"SELECT rowid FROM {FileCoreMetadataTable.TABLE_NAME} WHERE file_id = ?",
                (existing_rowid,)
            ).fetchone()
            if meta_row:
                # It's done at least once
                for i, proc in enumerate(self.process_list):
                    if isinstance(proc, ExtractFileMetadataProcess) and not proc.can_repeat:
                        cb = self.process_checkboxes[i]
                        cb.setChecked(False)
                        cb.setDisabled(True)
                        self.process_lineedits[i].setText(
                            self.process_lineedits[i].text() + " (Already Done)"
                        )
                        self.output_text.appendPlainText(
                            "ExtractFileMetadataProcess already done, can't repeat -> disabled.\n"
                        )

            # 4B) For ANY single-use process (can_repeat=False) that defines TABLE_CLASS,
            #     check if it has an entry for this file_id
            for i, proc in enumerate(self.process_list):
                if proc.TABLE_CLASS and not proc.can_repeat:
                    # Generic table check
                    table_name = proc.TABLE_CLASS.TABLE_NAME
                    done_row = conn.execute(
                        f"SELECT rowid FROM {table_name} WHERE file_id = ?",
                        (existing_rowid,)
                    ).fetchone()
                    if done_row:
                        cb = self.process_checkboxes[i]
                        cb.setChecked(False)
                        cb.setDisabled(True)
                        self.process_lineedits[i].setText(
                            self.process_lineedits[i].text() + " (Already Done)"
                        )
                        self.output_text.appendPlainText(
                            f"{proc.__class__.__name__} already done, can't repeat -> disabled.\n"
                        )

        conn.close()

        # 5) Finally, update the button state after all changes
        self.update_process_button_state()

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Returns a dictionary of file info.

        Args:
            file_path (str): Path to the file.

        Returns:
            Dict[str, Any]: File size and type.
        """
        logging.info("Gathering file info.")
        size = os.path.getsize(file_path)
        _, ext = os.path.splitext(file_path)
        return {"filesize": size, "filetype": ext}

    def run_selected_processes(self) -> None:
        """
        Runs the selected processes in order.
        Even if a core process checkbox is disabled (but checked), we still run it.
        Processes that can't be repeated are unchecked and disabled upon completion or detection.
        """
        logging.info("Running selected processes.")

        # Count all processes that are checked (ignore whether they're disabled or not)
        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()
        ]

        if not active_indices:
            QMessageBox.information(self, "No Active Processes", "No processes selected or remaining.")
            # Do not force-disable the button; just return
            return

        reply = QMessageBox.question(
            self,
            "Confirm Processing",
            "Are you sure you want to proceed with processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        row_id = None

        self.output_text.clear()
        db_path = DB_PATH
        original_file_path = self.file_path_lineedit.text()
        if not original_file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a file first.")
            return

        process_items = list(zip(
            self.process_checkboxes,
            self.process_list,
            self.process_lineedits,
            self.process_status_lineedits,
            self.process_rows,
            range(len(self.process_checkboxes))
        ))

        def process_next(index: int) -> None:
            nonlocal row_id
            if index >= len(process_items):
                self.status_update_timer.stop()
                # Clear highlight for all processes
                for _, _, _, _, row_widget, _ in process_items:
                    row_widget.setStyleSheet("")
                return

            checkbox, process, name_edit, status_edit, row_widget, proc_index = process_items[index]
            # Run the process if it is checked (ignore isEnabled)
            if checkbox.isChecked():
                logging.info(f"Executing {name_edit.text()}.")
                self.current_process_index = proc_index
                self.process_start_times[proc_index] = time.time()
                self.process_end_times[proc_index] = None

                row_widget.setStyleSheet("background-color: #FFFACD;")
                status_edit.setText("Starting...")

                if not self.status_update_timer.isActive():
                    self.status_update_timer.start(1000)

                divider = create_divider(name_edit.text(), total_width=50)
                self.output_text.appendPlainText(divider + "\n")

                def output_callback(message: str) -> None:
                    self.output_text.appendPlainText(message)

                # First process sets row_id if returning int
                if row_id is None:
                    result = process.execute(db_path, original_file_path, output_callback)
                    if isinstance(result, int):
                        row_id = result
                    else:
                        self.output_text.appendPlainText(str(result))
                else:
                    # Subsequent processes use the row_id
                    result = process.execute(db_path, row_id, output_callback)
                    if isinstance(result, str):
                        self.output_text.appendPlainText(result)

                end_time = time.time()
                self.process_end_times[proc_index] = end_time
                duration = end_time - self.process_start_times[proc_index]

                # If process can't repeat, uncheck & disable it now
                if not process.can_repeat:
                    checkbox.setChecked(False)
                    checkbox.setDisabled(True)
                    name_edit.setText(name_edit.text() + " (Done)")

                row_widget.setStyleSheet("background-color: lightgray;")
                status_edit.setText(f"Done at {time.ctime(end_time)} (took {int(duration)}s)")
            else:
                status_edit.setText("Skipped")

            QTimer.singleShot(100, lambda: self.processes_scroll_area.verticalScrollBar().setValue(
                self.processes_scroll_area.verticalScrollBar().maximum()
            ))
            QTimer.singleShot(300, lambda: process_next(index + 1))

        process_next(0)


    def update_all_process_statuses(self) -> None:
        """
        Updates the status text of any currently running process with elapsed time.
        """
        if self.current_process_index is None:
            return

        start_time = self.process_start_times.get(self.current_process_index)
        end_time = self.process_end_times.get(self.current_process_index)
        if start_time is None or end_time is not None:
            self.current_process_index = None
            return

        elapsed = int(time.time() - start_time)
        status_lineedit = self.process_status_lineedits[self.current_process_index]
        status_lineedit.setText(
            f"Started at {time.ctime(start_time)} | Elapsed: {elapsed}s"
        )

    def show_help(self, process_obj) -> None:
        """
        Shows a small help window in markdown style (basic text here, no advanced markdown rendering).
        """
        logging.info(f"Showing help for {process_obj.__class__.__name__}.")
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(f"Help: {process_obj.__class__.__name__}")
        layout = QVBoxLayout()
        help_text = QPlainTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(f"**Help for {process_obj.__class__.__name__}**\n\n"
                               f"This process does the following:\n"
                               f"{process_obj.__doc__}\n\n"
                               "More documentation can be added here in Markdown format.")
        layout.addWidget(help_text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.close)
        layout.addWidget(close_button)
        help_dialog.setLayout(layout)
        help_dialog.exec()

    def update_elapsed_time(self) -> None:
        """Updates the time label with the time since processes started."""
        elapsed = time.time() - self.start_time
        self.process_time_label.setText(f"Elapsed: {int(elapsed)}s")

    def select_all_processes(self) -> None:
        """Select all or deselect all processes based on the header checkbox state."""
        select_state = self.select_all_checkbox.isChecked()
        for checkbox in self.process_checkboxes:
            if checkbox.isEnabled():
                checkbox.setChecked(select_state)
        self.update_process_button_state()

    def update_process_button_state(self) -> None:
        """
        Enables or disables the 'Process' button if at least one process is checked,
        regardless of whether it's enabled/disabled. This ensures core processes
        (checked + disabled) still allow the user to press "Process."
        """
        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()  # do not check cb.isEnabled()
        ]
        self.process_button.setEnabled(bool(active_indices))


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


# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
