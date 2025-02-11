"""View module for the tag-based explorer application."""

from typing import Callable
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QLineEdit, QListWidget,
    QVBoxLayout, QHBoxLayout, QListWidgetItem, QComboBox, QFrame
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSize

from tagsense.views.dialog_windows import MediaImport, ExportSearch, Settings, Help

def _create_vlines_wrapped_widget(widget: QWidget) -> QWidget:
    """
    Wraps the given widget with vertical lines on each side.
    
    Args:
        widget (QWidget): The widget to wrap.
    
    Returns:
        QWidget: A new widget containing the original widget with two vertical lines.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    left_line = QFrame()
    left_line.setFrameShape(QFrame.Shape.VLine)
    left_line.setFrameShadow(QFrame.Shadow.Sunken)

    right_line = QFrame()
    right_line.setFrameShape(QFrame.Shape.VLine)
    right_line.setFrameShadow(QFrame.Shadow.Sunken)

    layout.addWidget(left_line)
    layout.addWidget(widget)
    layout.addWidget(right_line)
    return container

class TagExplorerView(QMainWindow):
    """Main window for the tag-based explorer."""

    def __init__(
        self,
        on_natural_language_query_change: Callable[[str], None],
        on_tag_search_change: Callable[[str], None],
        on_tag_selected: Callable[[str], None],
        parent: QWidget = None
    ) -> None:
        """
        Initializes the TagExplorerView.

        Args:
            on_natural_language_query_change (Callable[[str], None]): Callback for natural language input changes.
            on_tag_search_change (Callable[[str], None]): Callback for tag input changes.
            on_tag_selected (Callable[[str], None]): Callback when a tag is selected.
            parent (QWidget, optional): Optional parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.init_ui()

        # Main horizontal splitter for left (controls) and right (thumbnails)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side big splitter
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top spacer for adjustable empty space
        self.top_spacer = QWidget()

        # Middle splitter holds the four sections:
        #   1) Natural language search
        #   2) Tag search
        #   3) System tag area (+dropdown)
        #   4) Normal tag area (+dropdown)
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)

        # Bottom spacer for adjustable empty space
        self.bottom_spacer = QWidget()

        # Natural language search section
        self.natural_language_input = QLineEdit()
        self.natural_language_input.setPlaceholderText("Enter natural language query...")

        # Tag search section
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter tag search query...")

        # System tags
        self.system_widget = QWidget()
        self.system_layout = QVBoxLayout(self.system_widget)
        self.system_sort_dropdown = QComboBox()
        self.system_sort_dropdown.addItems(["System Sort A", "System Sort B"])
        self.system_tag_list = QListWidget()
        self.system_layout.addWidget(self.system_sort_dropdown)
        self.system_layout.addWidget(self.system_tag_list)

        # Normal tags
        self.normal_widget = QWidget()
        self.normal_layout = QVBoxLayout(self.normal_widget)
        self.normal_sort_dropdown = QComboBox()
        self.normal_sort_dropdown.addItems(["Normal Sort A", "Normal Sort B"])
        self.normal_tag_list = QListWidget()
        self.normal_layout.addWidget(self.normal_sort_dropdown)
        self.normal_layout.addWidget(self.normal_tag_list)

        # Wrap each of the four sections with vertical lines
        wrapped_natural_language_input = _create_vlines_wrapped_widget(self.natural_language_input)
        wrapped_tag_input = _create_vlines_wrapped_widget(self.tag_input)
        wrapped_system_widget = _create_vlines_wrapped_widget(self.system_widget)
        wrapped_normal_widget = _create_vlines_wrapped_widget(self.normal_widget)

        self.content_splitter.addWidget(wrapped_natural_language_input)
        self.content_splitter.addWidget(wrapped_tag_input)
        self.content_splitter.addWidget(wrapped_system_widget)
        self.content_splitter.addWidget(wrapped_normal_widget)
        for i in range(self.content_splitter.count()):
            self.content_splitter.setCollapsible(i, False)

        self.left_splitter.addWidget(self.top_spacer)
        self.left_splitter.addWidget(self.content_splitter)
        self.left_splitter.addWidget(self.bottom_spacer)

        # Let top_spacer and bottom_spacer be collapsible, center always visible
        self.left_splitter.setCollapsible(0, True)
        self.left_splitter.setCollapsible(1, False)
        self.left_splitter.setCollapsible(2, True)

        # Explicitly set initial sizes so top is collapsed by default
        self.left_splitter.setSizes([0, 1, 0])

        # Right side for thumbnails
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(self.thumbnail_list.ViewMode.IconMode)
        self.thumbnail_list.setFlow(self.thumbnail_list.Flow.LeftToRight)
        self.thumbnail_list.setResizeMode(self.thumbnail_list.ResizeMode.Adjust)
        self.thumbnail_list.setIconSize(QSize(128, 128))
        self.thumbnail_list.setGridSize(QSize(150, 150))
        right_layout.addWidget(self.thumbnail_list)

        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.right_widget)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 4)

        container_layout = QHBoxLayout()
        container_layout.addWidget(self.main_splitter)
        container = QWidget()
        container.setLayout(container_layout)
        self.setCentralWidget(container)

        # Connect signals
        self.natural_language_input.textChanged.connect(self.handle_natural_language_input)
        self.tag_input.textChanged.connect(self.handle_tag_input)
        self.system_tag_list.itemClicked.connect(self.handle_tag_list_click)
        self.normal_tag_list.itemClicked.connect(self.handle_tag_list_click)

    def init_ui(self):
        # Create menu bar (encompasses menus)
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        help_settings_menu = menu_bar.addMenu("Help")

        # Create menu item actions
        open_dialog_action = QAction("Import Media", self)
        open_dialog_action.triggered.connect(lambda: MediaImport(self).exec())
        export_dialog_action = QAction("Export Search", self)
        export_dialog_action.triggered.connect(lambda: ExportSearch(self).exec())

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: Settings(self).exec())
        help_action = QAction("Help", self)
        help_action.triggered.connect(lambda: Help(self).exec())

        # Add all actions to their respective menus
        file_menu.addAction(open_dialog_action)
        file_menu.addAction(export_dialog_action)
        help_settings_menu.addAction(settings_action)
        help_settings_menu.addAction(help_action)

    def handle_natural_language_input(self, text: str) -> None:
        """
        Handles updates to the natural language input.

        Args:
            text (str): Updated text for the natural language query.
        """
        self.on_natural_language_query_change(text)

    def handle_tag_input(self, text: str) -> None:
        """
        Handles updates to the tag input.

        Args:
            text (str): Updated text for the tag query.
        """
        self.on_tag_search_change(text)

    def handle_tag_list_click(self, item: QListWidgetItem) -> None:
        """
        Handles clicks on items in either tag list.

        Args:
            item (QListWidgetItem): The clicked tag list item.
        """
        self.on_tag_selected(item.text())

    def update_system_tag_list(self, tags: list[str]) -> None:
        """
        Updates the system tag list with the specified tags.

        Args:
            tags (list[str]): New system tags to display.
        """
        self.system_tag_list.clear()
        for tag in tags:
            self.system_tag_list.addItem(tag)

    def update_normal_tag_list(self, tags: list[str]) -> None:
        """
        Updates the normal tag list with the specified tags.

        Args:
            tags (list[str]): New normal tags to display.
        """
        self.normal_tag_list.clear()
        for tag in tags:
            self.normal_tag_list.addItem(tag)

    def add_thumbnail(self, file_name: str) -> None:
        """
        Adds a new thumbnail item to the thumbnail list.

        Args:
            file_name (str): The file name or path to represent in the list.
        """
        self.thumbnail_list.addItem(QListWidgetItem(file_name))

    def clear_thumbnails(self) -> None:
        """
        Removes all thumbnail items from the thumbnail list.
        """
        self.thumbnail_list.clear()
