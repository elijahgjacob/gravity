"""
SERVICE: Business logic for category extraction.

This service extracts 1-10 relevant product/service categories from user queries
using TF-IDF vectorization and keyword matching against a predefined taxonomy.
"""

import numpy as np
from typing import Optional, List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.repositories.taxonomy_repository import TaxonomyRepository


class CategoryService:
    """
    SERVICE: Business logic for category extraction.

    Extracts 1-10 relevant product/service categories from query using:
    - Keyword matching against taxonomy
    - TF-IDF similarity scoring (pre-computed for speed)
    - Context-based boosting (user interests)
    
    Performance: ~1-3ms per query (optimized with pre-computed vectors)
    """

    def __init__(self, taxonomy_repo: TaxonomyRepository):
        """
        Initialize the category service.

        Args:
            taxonomy_repo: Repository for accessing category taxonomy
        """
        self.taxonomy_repo = taxonomy_repo
        self.vectorizer = TfidfVectorizer(
            max_features=100, ngram_range=(1, 2), lowercase=True, stop_words="english"
        )
        self._category_keyword_vectors: Dict = {}
        self._category_keywords_lower: Dict[str, List[str]] = {}
        self._fit_vectorizer()

    def _fit_vectorizer(self) -> None:
        """
        Pre-fit TF-IDF vectorizer and pre-compute category keyword vectors.

        This allows us to quickly compute similarity between queries
        and category keywords at runtime without re-vectorizing.
        """
        all_keywords = []
        for category_data in self.taxonomy_repo.get_all_categories().values():
            all_keywords.extend(category_data.get("keywords", []))

        if all_keywords:
            self.vectorizer.fit(all_keywords)
            
            # Pre-compute keyword vectors for each category
            for category_name, category_data in self.taxonomy_repo.get_all_categories().items():
                keywords = category_data.get("keywords", [])
                if keywords:
                    self._category_keyword_vectors[category_name] = self.vectorizer.transform(keywords)
                    self._category_keywords_lower[category_name] = [k.lower() for k in keywords]

    async def extract(
        self, query: str, context: Optional[Dict] = None, max_categories: int = 10
    ) -> List[str]:
        """
        Extract relevant categories from query.

        Args:
            query: The user's query text
            context: Optional user context with interests
            max_categories: Maximum number of categories to return (default 10)

        Returns:
            List of 1-10 category names (enforced)
        """
        # Score all categories by keyword similarity
        scores = self._score_categories(query)

        # Boost categories matching context interests
        if context and context.get("interests"):
            scores = self._boost_by_interests(scores, context["interests"])

        # Select top N categories with non-zero scores
        categories = self._select_top_n(scores, max_categories)

        # Enforce 1-10 range with fallback
        if len(categories) == 0:
            return ["general"]

        return categories[:10]

    def _score_categories(self, query: str) -> Dict[str, float]:
        """
        Score each category by keyword match (optimized).

        Uses multiple scoring signals:
        1. Exact keyword matches (highest weight)
        2. Partial keyword matches (medium weight)
        3. TF-IDF similarity using pre-computed vectors (fast)

        Args:
            query: The user's query text

        Returns:
            Dictionary mapping category names to scores
        """
        scores = {}
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Pre-compute query vector once
        try:
            query_vec = self.vectorizer.transform([query_lower])
        except Exception:
            query_vec = None

        for category_name, category_data in self.taxonomy_repo.get_all_categories().items():
            score = 0.0
            keywords_lower = self._category_keywords_lower.get(category_name, [])

            # Signal 1: Exact keyword matches (weight: 2.0 per match)
            for keyword in keywords_lower:
                if keyword in query_lower:
                    score += 2.0

            # Signal 2: Partial matches - query words in keywords (weight: 0.5 per word)
            for keyword in keywords_lower:
                keyword_words = set(keyword.split())
                overlap = query_words & keyword_words
                if overlap:
                    score += 0.5 * len(overlap)

            # Signal 3: TF-IDF similarity using pre-computed vectors (fast)
            if query_vec is not None and category_name in self._category_keyword_vectors:
                try:
                    keyword_vecs = self._category_keyword_vectors[category_name]
                    similarities = cosine_similarity(query_vec, keyword_vecs)
                    max_similarity = float(np.max(similarities)) if similarities.size > 0 else 0.0
                    score += max_similarity
                except Exception:
                    pass

            scores[category_name] = score

        return scores

    def _boost_by_interests(
        self, scores: Dict[str, float], interests: List[str]
    ) -> Dict[str, float]:
        """
        Boost categories that align with user interests.

        If a user's interests match a category's related terms,
        boost that category's score by 1.5x.

        Args:
            scores: Current category scores
            interests: List of user interests

        Returns:
            Updated scores with interest-based boosts
        """
        interests_lower = set(interest.lower() for interest in interests)

        for category_name in scores:
            category_data = self.taxonomy_repo.get_category(category_name)
            related = category_data.get("related", [])
            related_lower = set(r.lower() for r in related)

            # Check if any user interest matches category's related terms
            if interests_lower & related_lower:
                scores[category_name] *= 1.5

        return scores

    def _select_top_n(self, scores: Dict[str, float], n: int) -> List[str]:
        """
        Select top N categories by score.

        Only returns categories with positive scores.

        Args:
            scores: Dictionary of category scores
            n: Maximum number of categories to return

        Returns:
            List of top N category names
        """
        # Filter out zero scores and sort in one pass
        sorted_categories = sorted(
            ((cat, score) for cat, score in scores.items() if score > 0),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top N category names
        return [cat for cat, score in sorted_categories[:n]]
