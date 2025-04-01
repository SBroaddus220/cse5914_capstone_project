# -*- coding: utf-8 -*-

"""
Widgets for the application.
"""

# **** IMPORTS ****
import os
import io
import sys
import time
import threading
import logging
import contextlib
import traceback
from PIL import ImageQt
from typing import List, Optional, Any, Dict, Tuple

from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QSize, QObject, QThread
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton,
    QTableWidget, QStackedWidget, QListWidget, QTableWidgetItem, QLabel,
    QHeaderView, QAbstractItemView, QListWidgetItem, QGroupBox, QPlainTextEdit,
    QScrollArea, QCheckBox, QLineEdit, QDialog, QMessageBox
)

# **** LOCAL IMPORTS ****
from tagsense.util import create_divider
from tagsense.searches.search import Search

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class CustomGridTableWidget(QWidget):
    search_dropdown_changed: pyqtSignal = pyqtSignal(object)
    
    def __init__(
        self, 
        searches: list, 
        parent: QWidget = None, 
        window_class = None, 
        entry_whitelist: Optional[list] = None, 
        entry_blacklist: Optional[list] = None
        ):
        """Initializes the CustomGridTableWidget.

        Args:
            searches (list): List of searches to display.
            parent (QWidget, optional): Parent for widget. Defaults to None.
            window_class (_type_, optional): Window to open upon item select. Defaults to None.
            entry_whitelist (Optional[list], optional): Entry whitelist for every search in widget. Defaults to None.
            entry_blacklist (Optional[list], optional): Entry blacklist for every search in widget. Defaults to None.
        """
        super().__init__(parent)
        self.searches = searches
        self.window_class = window_class
        self.entry_whitelist = entry_whitelist
        self.entry_blacklist = entry_blacklist
        self._detail_windows = []  # Keep references to avoid segfaults
        
        # Initialize the UI
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # **
        # Top controls layout
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setContentsMargins(0, 0, 0, 0)

        # *
        # Left controls
        self.search_dropdown = QComboBox()
        for index, search in enumerate(self.searches):
            self.search_dropdown.addItem(search.name)
            self.search_dropdown.setItemData(index, search, Qt.ItemDataRole.UserRole)
        self.search_dropdown.currentIndexChanged.connect(self.handle_search_dropdown_change)

        self.info_button = QPushButton("Info")
        self.info_button.clicked.connect(self.show_search_info)

        left_controls_layout = QHBoxLayout()
        left_controls_layout.addWidget(self.search_dropdown)
        left_controls_layout.addWidget(self.info_button)
        left_controls_layout.addStretch()

        # *
        # Right controls
        self.table_view_button = QPushButton("Table View")
        self.grid_view_button = QPushButton("Grid View")
        self.table_view_button.clicked.connect(self.switch_to_table_view)
        self.grid_view_button.clicked.connect(self.switch_to_grid_view)

        right_controls_layout = QHBoxLayout()
        right_controls_layout.addWidget(self.table_view_button)
        right_controls_layout.addWidget(self.grid_view_button)
        right_controls_layout.addStretch()

        top_controls_layout.addLayout(left_controls_layout)
        top_controls_layout.addLayout(right_controls_layout)

        # **
        # Data view
        self.data_view = QStackedWidget()

        # *
        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.itemDoubleClicked.connect(self.handle_table_item_double_click)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.data_view.addWidget(self.table_widget)

        # *
        # Grid widget
        self.grid_widget = QListWidget()
        self.grid_widget.setViewMode(self.grid_widget.ViewMode.IconMode)
        self.grid_widget.setFlow(self.grid_widget.Flow.LeftToRight)
        self.grid_widget.setResizeMode(self.grid_widget.ResizeMode.Adjust)
        self.grid_widget.setIconSize(QSize(128, 128))
        self.grid_widget.setGridSize(QSize(150, 150))
        self.grid_widget.setDragEnabled(False)
        self.grid_widget.setMovement(self.grid_widget.Movement.Static)
        self.grid_widget.itemDoubleClicked.connect(self.handle_grid_item_double_click)
        self.data_view.addWidget(self.grid_widget)

        main_layout.addLayout(top_controls_layout)
        main_layout.addWidget(self.data_view)

        self.current_search: Search = next(iter(self.searches), None)
        self.populate_data_view()

    def switch_to_table_view(self) -> None:
        """Switches the stacked widget to show the table view. """
        self.data_view.setCurrentIndex(0)

    def switch_to_grid_view(self) -> None:
        """Switches the stacked widget to show the thumbnail (grid) view. """
        self.data_view.setCurrentIndex(1)

    def populate_data_view(self) -> None:
        if not self.current_search:
            return

        # ****
        # Reset table and grid
        self.grid_widget.clear()
        self.table_widget.clear()
        self.table_widget.setRowCount(0)

        # ****
        # Fetch results
        self.results = self.current_search.fetch_results(self.entry_whitelist, self.entry_blacklist)
        
        # ****
        # Check if there are any results
        if not self.results:
            self.table_widget.setColumnCount(0)
            return
        for item in self.results:  # Add preview key to each item
            item["preview"] = ""

        # ****
        # Prepare table
        columns = list(self.results[0].keys())
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Allow user to resize columns manually but also stretch the last one
        for col_idx in range(len(columns)):
            self.table_widget.horizontalHeader().setSectionResizeMode(
                col_idx,
                QHeaderView.ResizeMode.Interactive if col_idx < len(columns)-1
                else QHeaderView.ResizeMode.Stretch
            )
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # ****
        # Populate data view
        for row_idx, record in enumerate(self.results):
            # ****
            # Table view
            self.table_widget.insertRow(row_idx)
            for col_idx, col_key in enumerate(columns):
                item_value = str(record.get(col_key, ""))
                self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(item_value))

            # ****
            # Grid view
            pixmap = QPixmap.fromImage(ImageQt.ImageQt(self.current_search.generate_thumbnail(record)))
            thumbnail_item = QListWidgetItem(f"idx: {row_idx}")
            if pixmap.isNull():
                thumbnail_item.setText(f"idx: {row_idx}\nNo thumbnail")
            else:
                scaled_pix = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumbnail_item.setIcon(QIcon(scaled_pix))

            thumbnail_item.setData(Qt.ItemDataRole.UserRole, row_idx)
            self.grid_widget.addItem(thumbnail_item)

            # Add image preview to table view
            preview_label = QLabel()
            scaled_pixmap = pixmap.scaledToHeight(self.table_widget.rowHeight(row_idx))
            preview_label.setPixmap(scaled_pixmap)
            preview_label.setScaledContents(False)  # Keeps aspect ratio without distortion
            if scaled_pixmap.isNull():
                preview_label.setText("No file preview")
            self.table_widget.setCellWidget(row_idx, col_idx, preview_label)

    def handle_table_item_double_click(self, item: QTableWidgetItem) -> None:
        """Opens detail window when a user double-clicks a table cell."""
        if not self.current_search:
            return
        row_idx = item.row()
        item_data = self.results[row_idx]
        entry_key = item_data.get('entry_key')
        search_results = self.current_search.fetch_results()
        item_index = next(i for i, d in enumerate(search_results) if d.get('entry_key') == entry_key)
        self.open_detail_window(self.current_search, item_index)

    def handle_grid_item_double_click(self, item: QListWidgetItem) -> None:
        """Opens detail window when a user double-clicks a thumbnail item."""
        row_idx = self.grid_widget.row(item)
        item_data = self.results[row_idx]
        entry_key = item_data.get('entry_key')
        search_results = self.current_search.fetch_results()
        item_index = next(i for i, d in enumerate(search_results) if d.get('entry_key') == entry_key)
        self.open_detail_window(self.current_search, item_index)

    def open_detail_window(self, search: Search, record_idx: int) -> None:
        """Opens a window for details on a specific data item."""
        if not self.window_class:
            return
        window = self.window_class(search, record_idx, self.parent())
        window.show()
        self._detail_windows.append(window)  # Keep reference to avoid segfaults

    def handle_search_dropdown_change(self) -> None:
        index = self.search_dropdown.currentIndex()
        self.current_search = self.search_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        self.populate_data_view()
        # Emit signal to update other widgets
        self.search_dropdown_changed.emit(self.current_search)
        
    def show_search_info(self) -> None:
        """Displays the help text of the current search in a QMessageBox."""
        QMessageBox.information(self, "Search Info", self.current_search.get_help_text())

    @staticmethod
    def get_row_data(table_widget: QTableWidget, row_idx: int) -> dict[str, str]:
        """Fetches all data in a given row of a QTableWidget as a dictionary.

        Args:
            table_widget (QTableWidget): The table widget.
            row_idx (int): The row index.

        Returns:
            dict[str, str]: A dictionary mapping column headers to cell values.
        """
        headers = [table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())]
        values = [
            table_widget.item(row_idx, col).text() if table_widget.item(row_idx, col) else ""
            for col in range(table_widget.columnCount())
        ]
        return dict(zip(headers, values))

class OutputRouter(QObject):
    output_ready = pyqtSignal(str)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OutputRouter, cls).__new__(cls)
            super(OutputRouter, cls._instance).__init__()
        return cls._instance

    def write(self, message):
        if message.strip():  # ignore empty lines
            self.output_ready.emit(message)

    def flush(self):
        pass  # Required for file-like compatibility

class ProcessWorkerBase(QObject):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(str, dict)

    def __init__(self, process):
        super().__init__()
        self.process = process

    def _emit_output_from_callable(self, callable_fn):
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            try:
                result = callable_fn()
            except Exception as e:
                self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
                raise

        out_lines = stdout_buffer.getvalue().splitlines()
        err_lines = stderr_buffer.getvalue().splitlines()

        for line in out_lines:
            self.output.emit(f"{line}")
        for line in err_lines:
            self.output.emit(f"{line}")

        return result

class ExecuteProcessWorker(ProcessWorkerBase):
    def __init__(self, process, input_keys: list[str]):
        super().__init__(process)
        self.input_keys = input_keys

    def run(self):
        try:
            final_msg, final_data = None, None
            for key in self.input_keys:
                msg, data = self._emit_output_from_callable(
                    lambda: self.process.execute(input_data_key=key)
                )
                final_msg, final_data = msg, data  # could be overwritten multiple times
            self.finished.emit(final_msg, final_data)
        except Exception as e:
            pass  # Error already emitted in base class

class RunProcessesWidget(QWidget):
    def __init__(self, processes: List, data_structures_to_entry_keys: Dict[Any, List], parent=None):
        super().__init__(parent)
        self.processes = processes
        self.data_structures_to_entry_keys = data_structures_to_entry_keys
        
        self._init_ui()
        self._init_processes_ui()

        router = OutputRouter()
        router.output_ready.connect(self.output_text.appendPlainText)
        sys.stdout = router
        sys.stderr = router
        
        
    def _init_ui(self) -> None:
        # ****
        # Main layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # ****
        # Processes section
        self.processes_group = QGroupBox("Processes")
        processes_section_layout = QVBoxLayout()
        processes_section_layout.addWidget(self.processes_group)
        main_layout.addLayout(processes_section_layout)

        # ****
        # Output section
        self.output_text = QPlainTextEdit(self)
        self.output_text.setReadOnly(True)
        output_section = QWidget()
        output_section_layout = QVBoxLayout(output_section)
        output_label = QLabel("Output:")
        output_section_layout.addWidget(output_label)
        output_section_layout.addWidget(self.output_text)
        main_layout.addWidget(output_section)

        # ****
        # Buttons
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.parent().close if self.parent() else self.close)
        
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.run_selected_processes)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.process_button)
        main_layout.addLayout(button_layout)
        
    def _init_processes_ui(self) -> None:
        """Initializes the UI for the processes."""
        # ****
        # Setup process records
        self.process_checkboxes = []
        self.process_lineedits = []
        self.process_status_lineedits = []
        self.process_help_buttons = []
        self.process_rows = []
        self.process_start_times = {}
        self.process_end_times = {}
        self.current_process = None
        self.current_process_index = None

        # Timer to time process execution
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_all_process_statuses)

        # ****
        # Scroll area for processes
        self.processes_scroll_area = QScrollArea()
        self.processes_scroll_area.setWidgetResizable(True)
        
        # Containers for processes
        process_container = QWidget()
        process_layout = QVBoxLayout(process_container)

        # Select all option
        select_all_widget = QWidget()
        select_all_layout = QHBoxLayout(select_all_widget)
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.clicked.connect(self.select_all_processes)
        select_all_layout.addWidget(self.select_all_checkbox)
        select_all_layout.addStretch(1)
        process_layout.addWidget(select_all_widget)

        # Populate rows for each process
        for process_idx, process in enumerate(self.processes):
            process_row = QWidget()
            process_row_layout = QHBoxLayout(process_row)
            
            # Checkbox
            process_checkbox = QCheckBox()
            process_checkbox.clicked.connect(self.update_process_button_state)
            
            # Process name and status
            process_name_line_edit = QLineEdit(process.name)
            process_name_line_edit.setReadOnly(True)
            process_status_line_edit = QLineEdit("Not Started")
            process_status_line_edit.setReadOnly(True)
            
            # Help button
            process_help_button = QPushButton("?")
            process_help_button.clicked.connect(lambda checked, process=process: self.show_help(process))
            
            # Add to lists
            self.process_checkboxes.append(process_checkbox)
            self.process_lineedits.append(process_name_line_edit)
            self.process_status_lineedits.append(process_status_line_edit)
            self.process_help_buttons.append(process_help_button)
            self.process_rows.append(process_row)
            
            # Make room for the process times
            self.process_start_times[process_idx] = None
            self.process_end_times[process_idx] = None
            
            # Add to layout
            process_row_layout.addWidget(process_checkbox)
            process_row_layout.addWidget(process_name_line_edit)
            process_row_layout.addWidget(process_status_line_edit)
            process_row_layout.addWidget(process_help_button)
            process_layout.addWidget(process_row)
            
        # Add to scroll area
        process_container.setLayout(process_layout)
        self.processes_scroll_area.setWidget(process_container)
        
        # Create layout for processes group
        process_group_layout = QVBoxLayout()
        process_group_layout.addWidget(self.processes_scroll_area)
        self.processes_group.setLayout(process_group_layout)
        
        # Update button state after creation
        self.update_process_button_state()
        
    def reset_processes(self) -> None:
        """Resets the processes for a new run."""
        for process_idx in range(len(self.processes)):
            self.process_checkboxes[process_idx].setChecked(False)
            self.process_status_lineedits[process_idx].setText("Not Started")
            self.process_start_times[process_idx] = None
            self.process_end_times[process_idx] = None
        self.update_process_button_state()
        
    def update_process_button_state(self) -> None:
        """
        Enables or disables the 'Process' button if at least one process is checked.
        """
        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()
        ]
        self.process_button.setEnabled(bool(active_indices))
        
    def select_all_processes(self) -> None:
        """Select all or deselect all processes based on the header checkbox state."""
        select_state = self.select_all_checkbox.isChecked()
        for checkbox in self.process_checkboxes:
            checkbox: QCheckBox
            if checkbox.isEnabled():
                checkbox.setChecked(select_state)
        self.update_process_button_state()
        
    def run_selected_processes(self) -> None:
        """Runs the selected processes in order asynchronously."""
        logger.info("Running selected processes.")
        
        # Find checked processes
        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()
        ]

        if not active_indices:
            QMessageBox.information(self, "No Active Processes", "No processes selected or remaining. You should not see this window.")
            return

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Processing",
            "Are you sure you want to proceed with processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        # Prep for processing
        self.output_text.clear()
        self.current_process_item_index = 0

        # Store selected process items
        self.process_items = list(zip(
            self.process_checkboxes,
            self.processes,
            self.process_lineedits,
            self.process_status_lineedits,
            self.process_rows,
            range(len(self.process_checkboxes))
        ))

        # Filter to selected only
        self.process_items = [item for item in self.process_items if item[0].isChecked()]

        # Start processing the first item
        self._process_next()

    def _process_next(self) -> None:
        """Runs the next process in the queue (if any)."""
        index = self.current_process_item_index

        # Done
        if index >= len(self.process_items):
            self.status_update_timer.stop()
            for _, _, _, _, row_widget, _ in self.process_items:
                row_widget.setStyleSheet("")
            self.current_process = None
            self.current_process_index = None
            return

        # Unpack next item
        checkbox, process, name_edit, status_edit, row_widget, process_idx = self.process_items[index]

        # Track process
        self.current_process = process
        self.current_process_index = process_idx

        # Setup UI state
        logger.info(f"Executing process: {name_edit.text()}")
        self.process_start_times[process_idx] = time.time()
        self.process_end_times[process_idx] = None
        row_widget.setStyleSheet("background-color: #FFFACD;")
        status_edit.setText("Processing...")

        if not self.status_update_timer.isActive():
            self.status_update_timer.start(1000)

        divider = create_divider(name_edit.text(), total_width=50)
        self.output_text.appendPlainText(divider + "\n")

        # Run process (async)
        self.run_process(process)



    def run_process(self, process: Any):
        """Runs the process asynchronously using a worker thread."""
        if process.input not in self.data_structures_to_entry_keys:
            error_msg = f"Error: Missing input data for {process.name}."
            self.handle_error(error_msg)
            self.handle_finished(error_msg, None)
            return

        input_keys = self.data_structures_to_entry_keys[process.input]
        self.run_worker(ExecuteProcessWorker, process, input_keys)
    
    def run_worker(self, worker_class, *args):
        self.thread = QThread()
        self.worker = worker_class(*args)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.output.connect(self.handle_output)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.handle_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def handle_output(self, text):
        print(text)

    def handle_error(self, text):
        print("Error:", text)

    def handle_finished(self, msg, data):
        print("Done:", msg, data)
        
        # Call process completion
        if hasattr(self, "current_process") and self.current_process is not None:
            process = self.current_process
            process_idx = self.current_process_index

            # UI elements
            status_edit = self.process_status_lineedits[process_idx]
            checkbox = self.process_checkboxes[process_idx]
            row_widget = self.process_rows[process_idx]

            # Mark end time
            end_time = time.time()
            self.process_end_times[process_idx] = end_time
            duration = end_time - self.process_start_times[process_idx]

            # Handle completion logic
            success = self.handle_process_completion(process, msg, data)

            if process.deterministic and success:
                checkbox.setChecked(False)
                checkbox.setDisabled(True)

            if success:
                status_edit.setText("Completed")
            else:
                status_edit.setText("Failed")

            row_widget.setStyleSheet("background-color: lightgray;")
            status_edit.setText(f"Done at {time.ctime(end_time)} (took {int(duration)}s)")

            # Scroll to keep the latest in view
            QTimer.singleShot(100, lambda: self.processes_scroll_area.verticalScrollBar().setValue(
                self.processes_scroll_area.verticalScrollBar().maximum()
            ))

            # Continue to next process in the filtered list
            self.current_process_item_index += 1
            QTimer.singleShot(300, self._process_next)

    
    def handle_process_completion(self, process, msg, data) -> bool:
        # Record data for subsequent processes if successful
        success = bool(data)
        if success:
            if self.data_structures_to_entry_keys.get(process.output):
                self.data_structures_to_entry_keys[process.output].append(process.output.fetch_entry_key_from_entry(data))
            else:
                self.data_structures_to_entry_keys[process.output] = [process.output.fetch_entry_key_from_entry(data)]
            self.output_text.appendPlainText(f"Successful {process.name}: {data}")
        else:  # Failure. Log and skip
            self.output_text.appendPlainText(f"Process failed: {msg}") 
        return success
        
    def update_all_process_statuses(self) -> None:
        """Updates the status text of any currently running process with elapsed time."""
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
            
    def show_help(self, process) -> None:
        """Shows a small help window in basic text."""
        logging.info(f"Showing help for {process.name}.")
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(f"Help: {process.name}")
        layout = QVBoxLayout()
        help_text = QPlainTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(f"**Help for {process.name}**\n\n"
                               f"This process does the following:\n"
                               f"{process.__doc__}\n\n"
                               "More documentation can be added here in Markdown format.")
        layout.addWidget(help_text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.close)
        layout.addWidget(close_button)
        help_dialog.setLayout(layout)
        help_dialog.exec()

# ****
if __name__ == "__main__":
    raise Exception("This script is not meant to be run directly.")
