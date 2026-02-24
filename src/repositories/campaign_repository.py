"""
REPOSITORY: Data access for campaign metadata.

This repository handles loading and querying campaign data
from JSONL files for fast in-memory access.
"""

import json

import numpy as np


class CampaignRepository:
    """
    REPOSITORY: Data access for campaign metadata.

    Loads campaigns from JSONL file and provides fast in-memory access
    by index for retrieval after vector search.
    """

    def __init__(self, campaigns_path: str):
        """
        Initialize the campaign repository.

        Args:
            campaigns_path: Path to the campaigns JSONL file
        """
        self.campaigns: list[dict] = []
        self._load_campaigns(campaigns_path)

    def _load_campaigns(self, path: str) -> None:
        """
        Load campaigns from JSONL file.

        Each line in the JSONL file should be a valid JSON object
        representing a campaign with fields like:
        - campaign_id
        - title
        - description
        - category
        - subcategories
        - keywords
        - targeting
        - vertical
        - budget
        - cpc

        Args:
            path: Path to the JSONL file
        """
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        campaign = json.loads(line)
                        self.campaigns.append(campaign)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse campaign line: {e}")
                        continue

        print(f"Loaded {len(self.campaigns)} campaigns from {path}")

    def get_by_indices(self, indices: np.ndarray) -> list[dict]:
        """
        Get campaigns by index array.

        This is used after FAISS search to retrieve the actual campaign
        data for the returned indices.

        Args:
            indices: NumPy array of campaign indices

        Returns:
            List of campaign dictionaries (copies to prevent mutation)
        """
        campaigns = []
        for idx in indices:
            # Ensure index is within bounds
            if 0 <= idx < len(self.campaigns):
                # Return a copy to prevent external mutation
                campaigns.append(self.campaigns[idx].copy())
            else:
                print(
                    f"Warning: Index {idx} out of bounds (total campaigns: {len(self.campaigns)})"
                )

        return campaigns

    def get_by_id(self, campaign_id: str) -> dict | None:
        """
        Get a campaign by its campaign_id.

        Args:
            campaign_id: The campaign ID to search for

        Returns:
            Campaign dictionary if found, None otherwise
        """
        for campaign in self.campaigns:
            if campaign.get("campaign_id") == campaign_id:
                return campaign.copy()
        return None

    def get_all(self) -> list[dict]:
        """
        Get all campaigns.

        Returns:
            List of all campaign dictionaries
        """
        return self.campaigns

    def get_count(self) -> int:
        """
        Get the total number of campaigns.

        Returns:
            Count of campaigns
        """
        return len(self.campaigns)

    def get_by_category(self, category: str) -> list[dict]:
        """
        Get all campaigns in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of campaigns in the specified category
        """
        return [
            campaign.copy() for campaign in self.campaigns if campaign.get("category") == category
        ]

    def get_by_vertical(self, vertical: str) -> list[dict]:
        """
        Get all campaigns in a specific vertical.

        Args:
            vertical: Vertical name to filter by

        Returns:
            List of campaigns in the specified vertical
        """
        return [
            campaign.copy() for campaign in self.campaigns if campaign.get("vertical") == vertical
        ]
