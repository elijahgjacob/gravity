"""
SERVICE: Business logic for category extraction.

This service extracts 1-10 relevant product/service categories from user queries
using TF-IDF vectorization and keyword matching against a predefined taxonomy.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.repositories.taxonomy_repository import TaxonomyRepository


class CategoryService:
    """
    SERVICE: Business logic for category extraction.

    Extracts 1-10 relevant product/service categories from query using:
    - Keyword matching against taxonomy
    - TF-IDF similarity scoring
    - Context-based boosting (user interests)
    """

    def __init__(self, taxonomy_repo: TaxonomyRepository):
        """
        Initialize the category service.

        Args:
            taxonomy_repo: Repository for accessing category taxonomy
        """
        self.taxonomy_repo = taxonomy_repo
        self.vectorizer = TfidfVectorizer(
            max_features=100, ngram_range=(1, 3), lowercase=True, stop_words="english"
        )
        self._fit_vectorizer()

    def _fit_vectorizer(self) -> None:
        """
        Pre-fit TF-IDF vectorizer on taxonomy keywords.

        This allows us to quickly compute similarity between queries
        and category keywords at runtime.
        """
        all_keywords = []
        for category_data in self.taxonomy_repo.get_all_categories().values():
            all_keywords.extend(category_data.get("keywords", []))

        if all_keywords:
            self.vectorizer.fit(all_keywords)

    async def extract(
        self, query: str, context: dict | None = None, max_categories: int = 10
    ) -> list[str]:
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

    def _score_categories(self, query: str) -> dict[str, float]:
        """
        Score each category by keyword match.

        Uses multiple scoring signals:
        1. Exact keyword matches (highest weight)
        2. Partial keyword matches (medium weight)
        3. TF-IDF similarity (lower weight)

        Args:
            query: The user's query text

        Returns:
            Dictionary mapping category names to scores
        """
        scores = {}
        query_lower = query.lower()

        for category_name, category_data in self.taxonomy_repo.get_all_categories().items():
            score = 0.0
            keywords = category_data.get("keywords", [])

            # Signal 1: Exact keyword matches (weight: 2.0 per match)
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 2.0

            # Signal 2: Partial matches - query words in keywords (weight: 0.5 per word)
            query_words = set(query_lower.split())
            for keyword in keywords:
                keyword_words = set(keyword.lower().split())
                overlap = query_words & keyword_words
                if overlap:
                    score += 0.5 * len(overlap)

            # Signal 3: TF-IDF similarity (weight: 0-1.0)
            # This catches semantic similarity even without exact matches
            try:
                query_vec = self.vectorizer.transform([query_lower])
                keyword_vecs = self.vectorizer.transform(keywords)

                # Compute cosine similarity with each keyword
                from sklearn.metrics.pairwise import cosine_similarity

                similarities = cosine_similarity(query_vec, keyword_vecs)
                max_similarity = float(np.max(similarities)) if similarities.size > 0 else 0.0
                score += max_similarity
            except Exception:
                # If TF-IDF fails (e.g., no vocabulary overlap), skip this signal
                pass

            scores[category_name] = score

        return scores

    def _boost_by_interests(
        self, scores: dict[str, float], interests: list[str]
    ) -> dict[str, float]:
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
        interests_lower = [interest.lower() for interest in interests]

        for category_name in scores:
            category_data = self.taxonomy_repo.get_category(category_name)
            related = category_data.get("related", [])

            # Check if any user interest matches category's related terms
            if any(interest in [r.lower() for r in related] for interest in interests_lower):
                scores[category_name] *= 1.5

        return scores

    def _select_top_n(self, scores: dict[str, float], n: int) -> list[str]:
        """
        Select top N categories by score.

        Only returns categories with positive scores.

        Args:
            scores: Dictionary of category scores
            n: Maximum number of categories to return

        Returns:
            List of top N category names
        """
        # Filter out zero scores
        filtered_scores = {cat: score for cat, score in scores.items() if score > 0}

        # Sort by score (descending)
        sorted_categories = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top N category names
        return [cat for cat, score in sorted_categories[:n]]
