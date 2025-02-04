from typing import List

class TagExplorerModel:
    def __init__(self) -> None:
        self.tags: List[str] = []
        self.natural_language_query: str = ""

    def add_tag(self, tag: str) -> None:
        self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        if tag in self.tags:
            self.tags.remove(tag)

    def set_natural_language_query(self, query: str) -> None:
        self.natural_language_query = query

    def get_tags(self) -> List[str]:
        return self.tags

    def get_natural_language_query(self) -> str:
        return self.natural_language_query
