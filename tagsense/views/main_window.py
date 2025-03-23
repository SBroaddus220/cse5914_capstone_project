# -*- coding: utf-8 -*-

"""
View module for the main window of the application.
"""

# **** IMPORTS ****
import re
import sqlite3
import logging
from typing import List, Union

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QStackedWidget, QComboBox, QPushButton, 
    QTableWidget, QHeaderView, QTableWidgetItem, QListWidget, QListWidgetItem, QMessageBox, QLabel
)
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QAction, QKeyEvent

# **** LOCAL IMPORTS ****
from tagsense import registry
from tagsense.util import CustomGridTableWidget
from tagsense.registry import search_registry
from tagsense.searches.app_search import AppSearch

# Import dialog windows
from tagsense.views.dialog_windows.help import Help
from tagsense.views.data_view_window import DataViewWindow
from tagsense.views.dialog_windows.settings import Settings
from tagsense.views.dialog_windows.file_import import FileImport
from tagsense.views.dialog_windows.export_search import ExportSearch
from tagsense.views.dialog_windows.run_processes import RunProcesses
from tagsense.views.dialog_windows.install_processes import InstallProcessesDialog

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** CLASSES ****
class MainWindow(QMainWindow):
    """
    Main window for the application.
    """

    def __init__(self, conn: sqlite3.Connection, parent: QWidget = None) -> None:
        """
        Initializes the main window.
        """
        super().__init__(parent)
        logger.info("Initializing main window")
        self.conn = conn
        self.current_search: AppSearch

        # ****
        # Initialize menus
        logger.info("Initializing menus")
        self.init_menus()

        # ****
        # Format window
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.main_splitter)
        
        # **
        # Init left sidebar
        self.init_left_sidebar()
        
        # **
        # Init central data view
        self.init_central_data_view()
        
        self.setWindowTitle("DoomFile9000")
        self.setMinimumSize(800, 600)
        self.show()

    def init_menus(self) -> None:
        """Initializes the user interface."""
        # ****
        # Create menu bar
        menu_bar = self.menuBar()
        
        # **
        # Menus
        file_menu = menu_bar.addMenu("&File")
        help_menu = menu_bar.addMenu("&Help")
        
        # **
        # Actions
        open_dialog_action = QAction("Import Files", self)
        open_dialog_action.triggered.connect(lambda: FileImport(conn=self.conn, parent=self).exec())
        run_processes_action = QAction("Run Processes", self)
        run_processes_action.triggered.connect(lambda: RunProcesses(self).exec())
        install_processes_action = QAction("Install Processes", self)
        install_processes_action.triggered.connect(lambda: (
            QMessageBox.information(self, "No Processes", "No processes to install.")
            if not (registry.process_registry - registry.installed_processes)
            else InstallProcessesDialog(self).exec()
        ))
        export_dialog_action = QAction("Export Search", self)
        export_dialog_action.triggered.connect(lambda: ExportSearch(self).exec())
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: Settings(self).exec())
        help_action = QAction("Help", self)
        help_action.triggered.connect(lambda: Help(self).exec())

        # **
        # Add actions to menus
        file_menu.addAction(open_dialog_action)
        file_menu.addAction(run_processes_action)
        file_menu.addAction(install_processes_action)
        file_menu.addAction(export_dialog_action)
        
        help_menu.addAction(settings_action)
        help_menu.addAction(help_action)
        
    def init_central_data_view(self) -> None:
        """Initializes the central data view."""
        # ****
        # Add data view
        self.data_view = CustomGridTableWidget(
            searches=search_registry,
            parent=self,
            window_class=DataViewWindow
        )
        self.main_splitter.addWidget(self.data_view)
        
        
        
    def init_left_sidebar(self, parent: QWidget = None) -> None:
        # ****
        # Create initial widget
        self.left_sidebar_container = QWidget(parent)
        left_sidebar_layout = QVBoxLayout(self.left_sidebar_container)
        left_sidebar_layout.setContentsMargins(5, 5, 5, 5)
        left_sidebar_layout.setSpacing(10)
        self.left_sidebar_container.setLayout(left_sidebar_layout)
        self.main_splitter.addWidget(self.left_sidebar_container)
        
        # **
        # Create the natural language input
        self.natural_language_input = QLineEdit()
        self.natural_language_input.setPlaceholderText("Enter a natural language query...")
        left_sidebar_layout.addWidget(self.natural_language_input)
        
        # Natural language buttons
        natural_language_button_layout = QHBoxLayout()
        natural_language_generate_button = QPushButton("Generate")
        natural_language_process_button = QPushButton("Process")
        natural_language_button_layout.addWidget(natural_language_generate_button)
        natural_language_button_layout.addWidget(natural_language_process_button)
        left_sidebar_layout.addLayout(natural_language_button_layout)
        
        # Natural language generated tags display
        self.natural_language_tags = QListWidget()
        left_sidebar_layout.addWidget(self.natural_language_tags)
        
        # Connect signals
        natural_language_generate_button.clicked.connect(self._handle_natural_language_input_generate)
        natural_language_process_button.clicked.connect(self._handle_natural_language_input_process)
        
        # **
        # Create the explicit data search area
        explicit_data_search_line = QHBoxLayout()
        self.explicit_data_search_input = QLineEdit()
        self.explicit_data_search_input.setPlaceholderText("Enter explicit data search...")
        self.explicit_data_search_input.textChanged.connect(self._update_suggestions)
        
        # Info button
        info_button = QPushButton("?")
        info_button.setFixedWidth(30)
        info_button.clicked.connect(self._show_explicit_data_search_info)
        explicit_data_search_line.addWidget(self.explicit_data_search_input)
        explicit_data_search_line.addWidget(info_button)
        left_sidebar_layout.addLayout(explicit_data_search_line)
        
        # Create the recommendation list
        self.explicit_data_recommendation_list = QListWidget()
        self.explicit_data_recommendation_list.itemDoubleClicked.connect(self._handle_explicit_data_recommendation_item_double_click)
        left_sidebar_layout.addWidget(self.explicit_data_recommendation_list)
        
        # Create the search button
        search_button = QPushButton("Search")
        left_sidebar_layout.addWidget(search_button)
        search_button.clicked.connect(self._handle_explicit_data_search)
        
        # Add the event filter to the search input
        self._event_filter = _RowidSearchEventFilter(
            self.explicit_data_search_input,
            self.explicit_data_recommendation_list,
            search_button,
        )
        self.explicit_data_search_input.installEventFilter(self._event_filter)
        
        self._cache_all_explicit_data_items()
        self._update_suggestions("")  # Initial suggestions
        
    def get_row_data(table_widget: QTableWidget, row_idx: int) -> dict[str, str]:
        """
        Fetches all data in a given row of a QTableWidget as a dictionary.

        Args:
            table_widget (QTableWidget): The table widget.
            row_idx (int): The row index.

        Returns:
            dict[str, str]: A dictionary mapping column headers to cell values.
        """
        headers = [table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())]
        values = [table_widget.item(row_idx, col).text() if table_widget.item(row_idx, col) else "" 
                for col in range(table_widget.columnCount())]
        return dict(zip(headers, values))

    def _cache_all_explicit_data_items(self) -> None:
        """Cache all explicit data items for suggestions."""
        self.all_items = ["101", "102", "203", "305"]  # Placeholder 
        
    def _handle_natural_language_input_generate(self, query: str) -> None:
        print(f"Generating tags for query: {query}")
        
    def _handle_natural_language_input_process(self, query: str) -> None:
        print(f"Processing query: {query}")

    def _handle_explicit_data_recommendation_item_double_click(self, item: QListWidgetItem) -> None:
        """Double click to autocomplete."""
        logger.debug(f"Double clicked on item: {item.text()}")
        self._autocomplete_last_token(item)
        
    def _handle_explicit_data_search(self) -> None:
        """Handle the explicit data search."""
        typed_expr = self.explicit_data_search_input.text().strip()
        logger.debug(f"Handling explicit data search: {typed_expr}")
        expanded_expr = expand_parentheses(typed_expr)
        logger.debug(f"Expanded expression => {expanded_expr}")
        parsed_expr = parse_logical_expression(expanded_expr)
        logger.debug(f"Parsed expression => {parsed_expr}")
        # self.populate_file_views()  # TODO
        print(f"Search triggered with expression: {parsed_expr}")
        
    def _autocomplete_last_token(self, item: QListWidgetItem) -> None:
        """Autocomplete the last token in the current text with the selected string."""
        current_text = self.explicit_data_search_input.text()
        sel_str = item.text()
        new_text = autocomplete_last_token(current_text, sel_str)
        self.explicit_data_search_input.setText(new_text)
        self.explicit_data_search_input.setCursorPosition(len(new_text))
        
    def _update_suggestions(self, typed_str: str) -> None:
        """Updates the suggestion list based on the typed input string."""
        logger.debug(f"Updating suggestions with '{typed_str}'")
        self.explicit_data_recommendation_list.clear()
        suggestions = get_suggestions(typed_str, self.all_items)
        self.explicit_data_recommendation_list.addItems(suggestions)

    def _show_explicit_data_search_info(self, parent: QWidget = None) -> None:
        logger.debug("Showing explicit data search information...")
        QMessageBox.information(
            parent,
            "Explicit Data Search Information",
            (
                """
                # Searching
                ## Basic Search
                ```
                tag1 tag2
                ```
                Search for posts that contain both `tag1` and `tag2`.
                ```
                tag1 or tag2
                ```
                Search for posts that contain either `tag1`, `tag2`, or both.
                ## Exclusion
                ```
                -tag1 -tag2
                ```
                Search for posts that do not contain `tag1` or `tag2`.
                ```
                -(tag1 tag2)
                ```
                Search for posts that do not contain both `tag1` and `tag2` together (but may contain either one individually or neither).
                ## Grouping and Combinations
                ```
                (tag1 tag2) or (tag3 tag4)
                ```
                Search for posts that contain either both `tag1` and `tag2` or both `tag3` and `tag4`.
                """
            )
        )
        

class _RowidSearchEventFilter(QObject):
    """
    A helper event filter that handles:
      - the up/down arrow keys to navigate recommendations,
      - the Enter key to auto-complete if a recommendation is selected,
        otherwise perform the search,
      - the Right arrow key to auto-complete if the cursor is at the end.

    This allows multiple space-separated tokens; each token can be autocompleted.
    """

    def __init__(
        self,
        edit: QLineEdit,
        recommendation_list: QListWidget,
        search_button: QPushButton,
        
    ) -> None:
        super().__init__()
        self._edit = edit
        self._recommendation_list = recommendation_list
        self._search_button = search_button

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if source is self._edit and event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event  # type: ignore
            cursor_pos = self._edit.cursorPosition()
            text_len = len(self._edit.text())

            if key_event.key() == Qt.Key.Key_Up:
                curr = self._recommendation_list.currentRow()
                logger.debug(f"Arrow UP pressed, current row: {curr}")
                self._recommendation_list.setCurrentRow(max(curr - 1, 0))
                return True

            elif key_event.key() == Qt.Key.Key_Down:
                curr = self._recommendation_list.currentRow()
                logger.debug(f"Arrow DOWN pressed, current row: {curr}")
                self._recommendation_list.setCurrentRow(
                    min(curr + 1, self._recommendation_list.count() - 1)
                )
                return True

            elif key_event.key() == Qt.Key.Key_Right:
                # If at the end of the line, and we have a recommendation item selected, auto-complete
                if cursor_pos == text_len and self._recommendation_list.currentItem():
                    logger.debug("Right arrow at end -> auto-complete with selected recommendation.")
                    self._autocomplete_last_token(self._recommendation_list.currentItem())
                    return True

            elif key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # If there's a recommendation item selected, auto-complete the last token
                item = self._recommendation_list.currentItem()
                if item:
                    logger.debug("Enter pressed with a recommendation selected -> auto-complete.")
                    self._autocomplete_last_token(item)
                    return True
                else:
                    # No recommendation selected -> interpret as "search"
                    logger.debug("Enter pressed with no recommendation selected -> trigger search.")
                    self._search_button.click()
                    return True

        return super().eventFilter(source, event)

    def _autocomplete_last_token(self, item: QListWidgetItem) -> None:
        """
        Replaces or appends to the last token in the rowid search input with the selected recommendation.
        Ensures a trailing space is appended.
        """
        if not item:
            logger.debug("No item to auto-complete with.")
            return
        sel_str = item.text()
        logger.debug(f"Autocompleting last token with: {sel_str}")
        new_text = autocomplete_last_token(self._edit.text(), sel_str)
        self._edit.setText(new_text)
        self._edit.setCursorPosition(len(new_text))

# **** FUNCTIONS ****
def autocomplete_last_token(current_text: str, sel_str: str) -> str:
    """Autocomplete the last token in the current text with the selected string.

    This method replaces the last token in the given text with `sel_str`, 
    or appends it if the text ends with a space.

    Args:
        current_text (str): The current text where the last token should be replaced.
        sel_str (str): The string to replace the last token or append as a new token.

    Returns:
        str: The autocompleted text with `sel_str` replacing the last token or being added.

    Examples:
        ```python
        obj.autocomplete_last_token("hello wor", "world")
        # Returns: "hello world "

        obj.autocomplete_last_token("hello ", "world")
        # Returns: "hello world "

        obj.autocomplete_last_token("hello", "world")
        # Returns: "world "

        obj.autocomplete_last_token("", "world")
        # Returns: "world "
        ```
    """
    if current_text.endswith(" "):
        # Append a new token
        tokens = current_text.strip().split()
        tokens.append(sel_str)
        new_text = " ".join(tokens) + " "
    else:
        tokens = current_text.strip().split()
        if not tokens:
            # No tokens, just append the selected string
            new_text = sel_str + " "
        else:
            # Replace the last token
            tokens[-1] = sel_str
            new_text = " ".join(tokens) + " "
    return new_text

def expand_parentheses(expr: str) -> str:
    """Expands parentheses in an expression by distributing negations and flattening enclosed terms.

    This function processes an expression containing parentheses and expands them by distributing
    negations (`-`) when present. If parentheses enclose multiple space-separated tokens, they are
    extracted and placed back into the expression without parentheses. If a negation precedes the 
    parentheses, it is applied to each enclosed token individually.

    Args:
        expr (str): The input expression containing potential parentheses to be expanded.

    Returns:
        str: The expression with parentheses expanded and negations properly distributed.

    Example:
        ```python
        expand_parentheses("-(a b c)")
        # Returns: "-a -b -c"

        expand_parentheses("(x y)")
        # Returns: "x y"

        expand_parentheses("(-z w)")
        # Returns: "-z w"
        ```
    """
    text = expr
    pattern = re.compile(r'(?P<neg>-?)\(\s*(?P<body>[^)]+)\s*\)')
    
    while True:
        match = pattern.search(text)
        if not match:
            break
        is_negative = match.group('neg')
        contents = match.group('body')
        tokens = contents.strip().split()
        
        if not tokens:
            replacement = ""
        else:
            if is_negative == '-':
                replacement = " ".join(f"-{t}" for t in tokens)
            else:
                replacement = " ".join(tokens)
        
        start, end = match.span()
        text = text[:start] + replacement + text[end:]
    
    return text
        
def parse_logical_expression(expr: str) -> str:
    """Parses a logical expression by handling AND and OR conditions.

    This function processes an input expression by splitting it into logical 
    groups. It separates conditions joined by `or`, ensuring each group is 
    properly enclosed in parentheses when necessary. If no `or` conditions exist, 
    it processes the expression using `parse_and_conditions`, which handles space-separated 
    AND conditions.

    Args:
        expr (str): The input logical expression.

    Returns:
        str: The formatted logical expression with `AND` and `OR` conditions structured properly.

    Examples:
        ```python
        parse_logical_expression("a b c")
        # Returns: "a AND b AND c"

        parse_logical_expression("a b or c d")
        # Returns: "(a AND b) OR (c AND d)"

        parse_logical_expression("")
        # Returns: ""

        parse_logical_expression("x or y or z")
        # Returns: "(x) OR (y) OR (z)"

        parse_logical_expression("apple -banana orange or -grape pear")
        # Returns: "(apple AND NOT banana AND orange) OR (NOT grape AND pear)"
        ```
    """
    def parse_and_conditions(tokens: str) -> str:
        """Parses space-separated tokens into an AND-based logical expression.

        This function processes space-separated tokens and converts them into 
        an AND-based logical condition. It supports negation using `-` as a prefix, 
        meaning a token prefixed with `-` will be treated as an exclusion (`!=`), 
        while all other tokens are treated as inclusion (`=`).

        Args:
            tokens (str): A string containing space-separated tokens.

        Returns:
            str: A logical expression combining tokens with `AND` conditions.
                Returns an empty string if no valid conditions are found.

        Examples:
            ```python
            parse_and_conditions("apple banana cherry")
            # Returns: "apple AND banana AND cherry"

            parse_and_conditions("-dog cat -mouse")
            # Returns: "NOT dog AND cat AND NOT mouse"

            parse_and_conditions("123 -456 789")
            # Returns: "123 AND NOT 456 AND 789"

            parse_and_conditions("")
            # Returns: ""
            ```

        Note:
            - Tokens prefixed with `-` are treated as exclusions (`NOT token`).
            - All other tokens are treated as inclusions (`token`).
            - No special field name is required; it works generically on any text input.
        """
        parts = tokens.split()
        conditions = []

        for token in parts:
            if token.startswith('-'):
                value = token[1:].strip()
                conditions.append(f"NOT {value}")
            else:
                conditions.append(token)

        if not conditions:
            return ""

        return " AND ".join(conditions) if len(conditions) > 1 else conditions[0]
    
    if not expr:
        return ""

    or_parts = [p.strip() for p in expr.split(" or ")]

    if len(or_parts) > 1:
        conditions = []
        for part in or_parts:
            sub_cond = parse_and_conditions(part)
            if sub_cond:
                conditions.append(f"({sub_cond})")
        return " OR ".join(conditions)
    else:
        return parse_and_conditions(expr)

def get_suggestions(typed_str: str, all_items: List[Union[str, int]]) -> List[str]:
    """Returns a list of suggestions based on the typed input string.

    This function dynamically filters available items based on the input string.
    It supports:
    - Returning all items if the input is empty or ends with a space.
    - Displaying items that start with the given input.
    - Handling negations (`-`), allowing filtered negative versions of items.

    Args:
        typed_str (str): The input string typed by the user.
        all_items (List[Union[str, int]]): A list of all available items.

    Returns:
        List[str]: A list of matching suggestions.

    Examples:
        ```python
        available_items = ["101", "102", "203", "305"]

        get_suggestions("", available_items)
        # Returns: ["101", "102", "203", "305"]

        get_suggestions("10", available_items)
        # Returns: ["101", "102"]

        get_suggestions("-2", available_items)
        # Returns: ["-203"]

        get_suggestions(" ", available_items)
        # Returns: ["101", "102", "203", "305"]
        ```
    """
    typed_str = typed_str or ""
    logger.debug(f"get_suggestions called with '{typed_str}'")

    if not all_items:
        logger.debug("No available items; returning empty list.")
        return []

    if typed_str.endswith(" "):
        logger.debug("Typed string ends with space -> returning all items.")
        return [str(item) for item in all_items]

    tokens = typed_str.split()
    if not tokens:
        logger.debug("No tokens -> returning all items.")
        return [str(item) for item in all_items]

    last_token = tokens[-1]

    if last_token == "-":
        logger.debug("Last token is '-', returning negative versions of all items.")
        return [f"-{item}" for item in all_items]

    if last_token.startswith('-'):
        remainder = last_token[1:]
        if remainder.isdigit():
            logger.debug(f"Returning all negative items matching prefix '{remainder}'")
            return [f"-{item}" for item in all_items if str(item).startswith(remainder)]
        return []

    if last_token.isdigit():
        logger.debug(f"Returning all items matching prefix '{last_token}'")
        return [str(item) for item in all_items if str(item).startswith(last_token)]

    return []

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
