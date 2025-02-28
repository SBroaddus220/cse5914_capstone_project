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

from tagsense import registry
from tagsense.config import DB_PATH
from tagsense.util import create_divider

# **** LOGGER ****
# Sets up logger
logger = logging.getLogger(__name__)

# **** CLASSES ****
class RunProcesses(QDialog):
    """
    Dialog for running user processes that do not rely on file inputs. 
    This mirrors the process logic seen in FileImport, but excludes file-based logic.
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the ProcessOnlyDialog and its UI elements.
        
        Args:
            parent: The parent widget for this dialog, if any.
        """
        super().__init__(parent)
        self.setWindowTitle("Run Processes Without Files")
        self.setGeometry(100, 100, 600, 500)

        # Fetch all user processes
        self.process_list = list(registry.installed_processes)

        # Define key widgets
        self.param_label = QLabel("Parameter (optional):")
        self.param_lineedit = QLineEdit()
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)

        self.processes_group = QGroupBox("Processes")
        self.process_checkboxes: List[QCheckBox] = []
        self.process_lineedits: List[QLineEdit] = []
        self.process_status_lineedits: List[QLineEdit] = []
        self.process_rows: List[QWidget] = []

        # Buttons
        self.process_button = QPushButton("Run Selected Processes")
        self.process_button.clicked.connect(self.run_selected_processes)
        self.cancel_button = QPushButton("Close")
        self.cancel_button.clicked.connect(self.close)

        # Internal tracking
        self.process_start_times: Dict[int, Optional[float]] = {}
        self.process_end_times: Dict[int, Optional[float]] = {}
        self.current_process_index: Optional[int] = None

        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_all_process_statuses)

        self.init_processes_ui()
        self.init_ui_layout()

    def init_ui_layout(self) -> None:
        """
        Builds the main UI layout.
        """
        # Parameter layout
        param_layout = QHBoxLayout()
        param_layout.addWidget(self.param_label)
        param_layout.addWidget(self.param_lineedit)

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

        # Use a QSplitter for the main center area
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(processes_section)
        splitter.addWidget(output_section)
        splitter.setCollapsible(1, True)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.process_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(param_layout)
        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def init_processes_ui(self) -> None:
        """
        Initializes the checkboxes, line edits, and help buttons for each process.
        """
        self.processes_scroll_area = QScrollArea()
        self.processes_scroll_area.setWidgetResizable(True)
        container = QWidget()
        v_layout = QVBoxLayout()

        # "Select All" widget
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

            lineedit = QLineEdit(process.__name__)
            status_lineedit = QLineEdit("Not Started")
            status_lineedit.setReadOnly(True)

            help_button = QPushButton("Help")
            help_button.clicked.connect(lambda _, p=process: self.show_help(p))

            self.process_checkboxes.append(checkbox)
            self.process_lineedits.append(lineedit)
            self.process_status_lineedits.append(status_lineedit)
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

        self.update_process_button_state()

    def run_selected_processes(self) -> None:
        """
        Runs the selected processes in order, passing the parameter from param_lineedit.
        """
        logger.info("Running selected processes.")

        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()
        ]
        if not active_indices:
            QMessageBox.information(self, "No Active Processes", "No processes selected.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Processing",
            "Are you sure you want to proceed with processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.output_text.clear()
        db_path = DB_PATH
        param_text = self.param_lineedit.text()

        process_items = list(zip(
            self.process_checkboxes,
            self.process_list,
            self.process_lineedits,
            self.process_status_lineedits,
            self.process_rows,
            range(len(self.process_checkboxes))
        ))

        def process_next(index: int) -> None:
            if index >= len(process_items):
                self.status_update_timer.stop()
                for _, _, _, _, row_widget, _ in process_items:
                    row_widget.setStyleSheet("")
                return

            checkbox, process, name_edit, status_edit, row_widget, proc_index = process_items[index]
            if checkbox.isChecked():
                logger.info(f"Executing {name_edit.text()}.")
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

                try:
                    result = process.execute(db_path, param_text, output_callback)
                    if isinstance(result, str):
                        self.output_text.appendPlainText(result)
                except Exception as exc:
                    error_msg = f"Error executing {name_edit.text()}: {exc}"
                    logger.error(error_msg)
                    self.output_text.appendPlainText(error_msg)

                end_time = time.time()
                self.process_end_times[proc_index] = end_time
                duration = end_time - self.process_start_times[proc_index]

                if not process.can_repeat:
                    checkbox.setChecked(False)
                    checkbox.setDisabled(True)
                    name_edit.setText(name_edit.text() + " (Done)")

                row_widget.setStyleSheet("background-color: lightgray;")
                status_edit.setText(f"Done at {time.ctime(end_time)} (took {int(duration)}s)")
            else:
                status_edit.setText("Skipped")

            # Scroll to bottom
            QTimer.singleShot(100, lambda: self._scroll_to_bottom())
            QTimer.singleShot(300, lambda: process_next(index + 1))

        process_next(0)

    def _scroll_to_bottom(self) -> None:
        """
        Scrolls the process scroll area to the bottom.
        """
        bar: QScrollBar = self.processes_scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

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

    def show_help(self, process_obj: Any) -> None:
        """
        Shows a small help window for the selected process.

        Args:
            process_obj (Any): The process object for which to show help.
        """
        logger.info(f"Showing help for {process_obj.__name__}.")
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(f"Help: {process_obj.__name__}")
        layout = QVBoxLayout()
        help_text = QPlainTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(
            f"**Help for {process_obj.__name__}**\n\n"
            f"{process_obj.__doc__}\n"
            "This process does not require a file-based parameter.\n"
        )
        layout.addWidget(help_text)
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_dialog.close)
        layout.addWidget(close_button)
        help_dialog.setLayout(layout)
        help_dialog.exec()

    def select_all_processes(self) -> None:
        """
        Selects or deselects all processes based on the 'Select All' checkbox.
        """
        select_state = self.select_all_checkbox.isChecked()
        for checkbox in self.process_checkboxes:
            if checkbox.isEnabled():
                checkbox.setChecked(select_state)
        self.update_process_button_state()

    def update_process_button_state(self) -> None:
        """
        Enables or disables the 'Run Selected Processes' button if at least one 
        process is checked.
        """
        active_indices = [
            i for i, cb in enumerate(self.process_checkboxes)
            if cb.isChecked()
        ]
        self.process_button.setEnabled(bool(active_indices))

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run standalone.")
