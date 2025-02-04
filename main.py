import sys
from PyQt6.QtWidgets import QApplication
from tagsense.models.model import TagExplorerModel
from tagsense.controllers.controller import TagExplorerController
from tagsense.views.main_window import TagExplorerView

def main() -> None:
    app = QApplication(sys.argv)
    model = TagExplorerModel()
    controller = TagExplorerController(model)

    def on_natural_language_query_change(text: str) -> None:
        controller.update_natural_language_query(text)

    def on_tag_search_change(text: str) -> None:
        # Example usage: fetching tags that match `text`
        # For now just pass
        pass

    def on_tag_selected(tag: str) -> None:
        # Example usage: removing or doing something with the selected tag
        pass

    view = TagExplorerView(
        on_natural_language_query_change,
        on_tag_search_change,
        on_tag_selected
    )
    view.update_normal_tag_list(["common_tag_1", "common_tag_2", "common_tag_3"])
    view.add_thumbnail("Thumbnail 1")
    view.add_thumbnail("Thumbnail 2")
    view.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
