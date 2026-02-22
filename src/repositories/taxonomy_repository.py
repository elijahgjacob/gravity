"""
REPOSITORY: Data access for category taxonomy.

This repository handles loading and querying the category taxonomy
used for extracting relevant categories from user queries.
"""

import json
from typing import Dict


class TaxonomyRepository:
    """
    REPOSITORY: Data access for category taxonomy.
    
    Loads category definitions with keywords and related terms from JSON,
    providing fast lookup for category extraction.
    """
    
    def __init__(self, taxonomy_path: str):
        """
        Initialize the taxonomy repository.
        
        Args:
            taxonomy_path: Path to the taxonomy JSON file
        """
        self.taxonomy: Dict[str, Dict] = {}
        self._load_taxonomy(taxonomy_path)
    
    def _load_taxonomy(self, path: str) -> None:
        """
        Load taxonomy from JSON file.
        
        Expected format:
        {
            "category_name": {
                "keywords": ["keyword1", "keyword2", ...],
                "related": ["interest1", "interest2", ...]
            },
            ...
        }
        
        Args:
            path: Path to the taxonomy JSON file
        """
        with open(path, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)
        print(f"Loaded {len(self.taxonomy)} categories from taxonomy")
    
    def get_all_categories(self) -> Dict[str, Dict]:
        """
        Get all categories with their metadata.
        
        Returns:
            Dictionary mapping category names to their data
        """
        return self.taxonomy
    
    def get_category(self, category_name: str) -> Dict:
        """
        Get specific category data.
        
        Args:
            category_name: Name of the category to retrieve
            
        Returns:
            Category data dictionary, or empty dict if not found
        """
        return self.taxonomy.get(category_name, {})
    
    def get_category_count(self) -> int:
        """
        Get the number of categories in the taxonomy.
        
        Returns:
            Count of categories
        """
        return len(self.taxonomy)
