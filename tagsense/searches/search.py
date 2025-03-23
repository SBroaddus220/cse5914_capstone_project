# -*- coding: utf-8 -*-

"""
Base foundation for searches.
"""

# **** IMPORTS ****
from PIL import Image
from PIL.Image import Image as PILImage

from tagsense.data_structures.data_structure import DataStructure

# **** CLASS ****
class Search:
    """Represents a search operation."""
    name: str
    data_structure: DataStructure
    
    @classmethod
    def fetch_results(cls) -> list[dict]:
        """Fetches search results."""
        return cls.data_structure.list_all()

    @classmethod
    def handle_natural_language_query(cls, query: str) -> list[dict]:
        raise NotImplementedError("Subclasses must implement this method.")
    
    @classmethod
    def handle_explicit_query(cls, query: str) -> list[dict]:
        raise NotImplementedError("Subclasses must implement this method.")
    
    @classmethod
    def generate_thumbnail(cls, result: dict, thumbnail_size=(100,100)) -> PILImage:
        return Image.new("RGB", size=thumbnail_size, color=(200,200,200))
        

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
