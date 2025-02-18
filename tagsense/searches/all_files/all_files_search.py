# -*- coding: utf-8 -*-

"""
Search that shows core metadata for all files.
"""

# **** IMPORTS ****
import re
import logging
logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMessageBox
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import QObject



from tagsense.searches.base_file_search import FileSearchBase

# **** CLASS ****

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
        search: 'AllFilesSearch',
        edit: QLineEdit,
        recommendation_list: QListWidget,
        search_button: QPushButton
    ) -> None:
        super().__init__()
        self._search = search
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
                    self._search._autocomplete_last_token(self._recommendation_list.currentItem())
                    return True

            elif key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # If there's a recommendation item selected, auto-complete the last token
                item = self._recommendation_list.currentItem()
                if item:
                    logger.debug("Enter pressed with a recommendation selected -> auto-complete.")
                    self._search._autocomplete_last_token(item)
                    return True
                else:
                    # No recommendation selected -> interpret as "search"
                    logger.debug("Enter pressed with no recommendation selected -> trigger search.")
                    self._search_button.click()
                    return True

        return super().eventFilter(source, event)

    def _autocomplete_with_current_item(self) -> None:
        """
        Replaces or appends to the last token in the rowid search input with the selected recommendation.
        Ensures a trailing space is appended.
        """
        item = self._recommendation_list.currentItem()
        if not item:
            logger.debug("No item to auto-complete with.")
            return

        sel_str = item.text()
        logger.debug(f"Autocompleting last token with: {sel_str}")

        current_text = self._edit.text()
        # If the user has typed a trailing space, we append a new token
        # instead of overwriting the last token
        if current_text.endswith(" "):
            tokens = current_text.strip().split()
            tokens.append(sel_str)
            new_text = " ".join(tokens) + " "
        else:
            tokens = current_text.strip().split()
            if not tokens:
                new_text = sel_str + " "
            else:
                tokens[-1] = sel_str
                new_text = " ".join(tokens) + " "

        self._edit.setText(new_text)
        # Move cursor to end
        self._edit.setCursorPosition(len(new_text))





class AllFilesSearch(FileSearchBase):
    """
    Search that selects from file_table with rowid-based searching.
    Includes multi-token logic, parentheses, negative tokens, 
    plus a recommendation list. The rowid can be literal or comma-delimited (demo).
    """

    def __init__(self) -> None:
        super().__init__()
        self._sql_condition: str = ""
        self._all_rowids: list[int] = []
        self._event_filter: _RowidSearchEventFilter | None = None

    def get_sql(self) -> str:
        if self._sql_condition:
            logger.debug(f"AllFilesSearch get_sql with condition: {self._sql_condition}")
            return f"SELECT * FROM file_table WHERE {self._sql_condition}"
        logger.debug("AllFilesSearch get_sql with no condition.")
        return "SELECT * FROM file_table"

    def get_left_sidebar_widget(self, parent: QWidget = None) -> QWidget:
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        natural_language_input = QLineEdit()
        natural_language_input.setPlaceholderText("Enter natural language query (no-op)...")
        layout.addWidget(natural_language_input)

        rowid_search_line = QHBoxLayout()
        self.rowid_search_input = QLineEdit()
        self.rowid_search_input.setPlaceholderText("Enter rowid search (AND/OR/NOT syntax, parentheses)...")

        info_button = QPushButton("?")
        info_button.setFixedWidth(30)
        def _show_info():
            logger.debug("Showing rowid query info message box.")
            QMessageBox.information(
                parent,
                "Rowid Query Info",
                (
                    "Rowid-based searching with AND/OR/NOT, parentheses, etc.\n"
                    "Multiple tokens are space-separated.\n"
                    "Negative tokens exclude matches.\n"
                    "If rowid is comma-delimited in the DB, '4 5' can match '4,5'."
                )
            )
        info_button.clicked.connect(_show_info)

        rowid_search_line.addWidget(self.rowid_search_input)
        rowid_search_line.addWidget(info_button)
        layout.addLayout(rowid_search_line)

        self.recommendation_list = QListWidget()
        # Remove the 10 item limit for recommendations:
        # We'll let it list all matches
        self.recommendation_list.itemDoubleClicked.connect(self._on_rec_list_item_doubleclick)
        layout.addWidget(self.recommendation_list)

        search_button = QPushButton("Search")
        layout.addWidget(search_button)

        def _perform_search() -> None:
            typed_expr = self.rowid_search_input.text().strip()
            logger.debug(f"User typed rowid search: '{typed_expr}'")

            expanded_expr = self._expand_parentheses(typed_expr)
            logger.debug(f"Parentheses expanded => '{expanded_expr}'")

            self._sql_condition = self._parse_rowid_expr(expanded_expr)
            logger.info(f"Updated rowid condition: {self._sql_condition}")

            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            for w in app.topLevelWidgets():
                if hasattr(w, "populate_file_views"):
                    logger.debug("Triggering main window re-population.")
                    w.populate_file_views()

        search_button.clicked.connect(_perform_search)

        self.rowid_search_input.textChanged.connect(self._update_recommendations)
        self._event_filter = _RowidSearchEventFilter(
            self, self.rowid_search_input, self.recommendation_list, search_button
        )
        self.rowid_search_input.installEventFilter(self._event_filter)

        self._cache_all_rowids(parent)
        self._update_recommendations("")  # Show recommendations initially

        return container

    def get_help_text(self) -> str:
        return (
            "Usage Instructions for AllFilesSearch:\n\n"
            "1) Provide an optional natural language search (no-op).\n"
            "2) Provide rowid tokens with AND/OR/NOT grouping.\n"
            "3) Use negative tokens to exclude.\n"
            "4) Parentheses for grouping.\n"
            "5) Press 'Search' or Enter with no recommendation selected to run.\n"
        )

    def _autocomplete_last_token(self, item: QListWidgetItem) -> None:
        """
        Inserts or replaces the last token in the rowid_search_input 
        with the item's text, then appends a space.
        This is used by both the event filter (Right arrow / Enter) 
        and double-clicking in the list.
        """
        sel_str = item.text()
        logger.debug(f"Autocompleting with item: {sel_str}")

        current_text = self.rowid_search_input.text()
        if current_text.endswith(" "):
            # We append a new token
            tokens = current_text.strip().split()
            tokens.append(sel_str)
            new_text = " ".join(tokens) + " "
        else:
            tokens = current_text.strip().split()
            if not tokens:
                new_text = sel_str + " "
            else:
                tokens[-1] = sel_str
                new_text = " ".join(tokens) + " "

        self.rowid_search_input.setText(new_text)
        self.rowid_search_input.setCursorPosition(len(new_text))

    def _on_rec_list_item_doubleclick(self, item: QListWidgetItem) -> None:
        """
        Double-click to auto-complete. Should use the same logic 
        as Right arrow / Enter in the event filter.
        """
        logger.debug(f"Double-clicked recommended rowid: {item.text()}")
        self._autocomplete_last_token(item)

    def _expand_parentheses(self, expr: str) -> str:
        # Same parentheses expansion logic as before
        import re
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

    def _parse_rowid_expr(self, expr: str) -> str:
        # Same simplified parser
        if not expr:
            return ""
        or_parts = [p.strip() for p in expr.split(" or ")]
        if len(or_parts) > 1:
            conditions = []
            for part in or_parts:
                sub_cond = self._parse_and_tokens(part)
                if sub_cond:
                    conditions.append(f"({sub_cond})")
            return " OR ".join(conditions)
        else:
            return self._parse_and_tokens(expr)

    def _parse_and_tokens(self, tokens: str) -> str:
        # AND-based logic for space-separated tokens
        parts = tokens.split()
        conds = []
        for t in parts:
            if t.startswith('-'):
                val = t[1:].strip()
                if val.isdigit():
                    conds.append(f"rowid != {val}")
            else:
                if t.isdigit():
                    conds.append(f"rowid = {t}")
        if not conds:
            return ""
        if len(conds) == 1:
            return conds[0]
        return " AND ".join(conds)

    def _cache_all_rowids(self, parent: QWidget) -> None:
        import sqlite3
        from PyQt6.QtWidgets import QApplication

        db_path = None
        app = QApplication.instance()
        for w in app.topLevelWidgets():
            if hasattr(w, "db_path"):
                db_path = w.db_path
                break

        if not db_path:
            logger.warning("Could not find DB path in top-level widgets.")
            return

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT rowid FROM file_table ORDER BY rowid")
            rows = c.fetchall()
            self._all_rowids = [r[0] for r in rows]
            conn.close()
            logger.debug(f"Cached {len(self._all_rowids)} rowids for recommendations.")
        except Exception as e:
            logger.exception(f"Failed to fetch rowids for recommendations: {e}")
            self._all_rowids = []

    def _update_recommendations(self, typed_str: str) -> None:
        """
        Removes the 10-item limit. Will show all matching.
        """
        typed_str = typed_str or ""
        logger.debug(f"_update_recommendations called with '{typed_str}'")
        self.recommendation_list.clear()

        if not self._all_rowids:
            logger.debug("No cached rowids available; can't show recommendations.")
            return

        if typed_str.endswith(" "):
            logger.debug("Typed string ends with space -> show all rowids.")
            for rid in self._all_rowids:
                self.recommendation_list.addItem(QListWidgetItem(str(rid)))
            return

        tokens = typed_str.split()
        if not tokens:
            logger.debug("No tokens -> show all rowids.")
            for rid in self._all_rowids:
                self.recommendation_list.addItem(QListWidgetItem(str(rid)))
            return

        last_token = tokens[-1]
        if last_token == "-":
            logger.debug("Last token is '-', show negative version of all rowids.")
            for rid in self._all_rowids:
                self.recommendation_list.addItem(QListWidgetItem(f"-{rid}"))
            return

        if last_token.startswith('-'):
            remainder = last_token[1:]
            if remainder.isdigit():
                logger.debug(f"Showing all negative rowids matching prefix '{remainder}'")
                matching = [rid for rid in self._all_rowids if str(rid).startswith(remainder)]
                for m in matching:
                    self.recommendation_list.addItem(QListWidgetItem(f"-{m}"))
            return
        if last_token.isdigit():
            logger.debug(f"Showing all rowids matching prefix '{last_token}'")
            matching = [rid for rid in self._all_rowids if str(rid).startswith(last_token)]
            for m in matching:
                self.recommendation_list.addItem(QListWidgetItem(str(m)))


class AllFileMetadataSearch(FileSearchBase):
    """Concrete example that selects all data from file_core_metadata."""
    
    def get_sql(self) -> str:
        return "SELECT * FROM file_core_metadata"

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
