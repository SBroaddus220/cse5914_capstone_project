# -*- coding: utf-8 -*-

"""
Base foundation for searches.
"""

# **** IMPORTS ****
from PIL import Image
from PIL.Image import Image as PILImage
from typing import Optional, List, Tuple

from tagsense.data_structures.data_structure import DataStructure

# **** CLASS ****
class Search:
    """Represents a search operation."""
    name: str
    data_structure: DataStructure
    
    @classmethod
    def fetch_results(cls, entry_whitelist: Optional[List[str]] = None, entry_blacklist: Optional[List[str]] = None) -> list[dict]:
        """Fetches search results."""
        results = cls.data_structure.list_all()
        return cls.filter_results(results, entry_whitelist, entry_blacklist)
    
    @classmethod
    def filter_results(self, results: List[dict], entry_whitelist: Optional[List[str]] = None, entry_blacklist: Optional[List[str]] = None) -> list[dict]:
        """Filters search results."""
        filtered_results = []
        for result in results:
            result_entry_key = self.data_structure.fetch_entry_key_from_entry(result)
            if entry_blacklist and result_entry_key in entry_blacklist:
                continue
            if entry_whitelist and result_entry_key not in entry_whitelist:
                continue
            filtered_results.append(result)
        return filtered_results

    @classmethod
    def generate_all_possible_tags(cls) -> list[str]:
        """Generates all possible tags for the search."""
        all_tags = set()
        results = cls.fetch_results()
        for entry_idx in range(len(results)):
            tags = cls.generate_tags_for_entry(results, entry_idx)
            all_tags = all_tags.union(tags)
        return cls.sort_all_tags(list(all_tags))
    
    @classmethod
    def sort_all_tags(cls, tags: list[str]) -> list[str]:
        """Sorts tags."""
        return sorted(tags)
    
    @classmethod
    def generate_tags_for_entry(cls, results: list[dict], entry_idx: int) -> list[str]:
        """Generates tags for a single entry."""
        return [str(entry_idx + 1)]

    @classmethod
    def generate_entry_filters_by_tags(cls, tag_whitelist: Optional[List[str]] = None, tag_blacklist: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
        """Logic to handle tag filters for entry search results."""
        results = cls.fetch_results()
        # Generate tags for each entry
        entry_keys_to_tags = {}
        for entry_idx in range(len(results)):
            entry_key = cls.data_structure.fetch_entry_key_from_entry(results[entry_idx])
            tags = cls.generate_tags_for_entry(results, entry_idx)
            entry_keys_to_tags[entry_key] = tags
        # Filter entries by tags
        entry_whitelist = []
        entry_blacklist = []
        for entry_key, tags in entry_keys_to_tags.items():
            if tag_blacklist and any(tag in tags for tag in tag_blacklist):
                entry_blacklist.append(entry_key)
            if tag_whitelist and all(tag in tags for tag in tag_whitelist):
                entry_whitelist.append(entry_key)
        return entry_whitelist, entry_blacklist

    @classmethod
    def handle_natural_language_query(cls, query: str) -> list[dict]:
        raise NotImplementedError("Subclasses must implement this method.")
    
    @classmethod
    def generate_thumbnail(cls, result: dict, thumbnail_size=(100,100)) -> PILImage:
        return Image.new("RGB", size=thumbnail_size, color=(200,200,200))
        

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
