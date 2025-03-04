from typing import List
from ..models.model import TagExplorerModel
from ..natural_language_processing.tag_generater import get_tags_from_text

class TagExplorerController:
    def __init__(self, model: TagExplorerModel) -> None:
        self.model = model

    def add_tag(self, tag: str) -> None:
        self.model.add_tag(tag)

    def remove_tag(self, tag: str) -> None:
        self.model.remove_tag(tag)

    def update_natural_language_query(self, query: str) -> None:
        self.model.set_natural_language_query(query)

    def fetch_tags(self) -> List[str]:
        return self.model.get_tags()

    def fetch_natural_language_query(self) -> str:
        return self.model.get_natural_language_query()

    def process_natural_language(self, query: str) -> List[str]:
        tags = get_tags_from_text(query)
        for tag in tags:
            self.model.add_tag(tag)
        return tags