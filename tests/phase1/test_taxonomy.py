"""Unit tests for taxonomy data."""

import pytest
import json
import os
from pathlib import Path


def test_taxonomy_file_exists():
    """Test that taxonomy.json file exists."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    assert taxonomy_path.exists()


def test_taxonomy_valid_json():
    """Test that taxonomy file is valid JSON."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    assert isinstance(taxonomy, dict)
    assert len(taxonomy) > 0


def test_taxonomy_structure():
    """Test that taxonomy has correct structure."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        assert isinstance(category_name, str)
        assert isinstance(category_data, dict)
        
        assert "keywords" in category_data
        assert "related" in category_data
        
        assert isinstance(category_data["keywords"], list)
        assert isinstance(category_data["related"], list)
        
        assert len(category_data["keywords"]) > 0
        assert len(category_data["related"]) > 0


def test_taxonomy_has_minimum_categories():
    """Test that taxonomy has at least 40 categories."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    assert len(taxonomy) >= 40


def test_taxonomy_keywords_are_strings():
    """Test that all keywords are strings."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        for keyword in category_data["keywords"]:
            assert isinstance(keyword, str)
            assert len(keyword) > 0


def test_taxonomy_related_are_strings():
    """Test that all related items are strings."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        for related in category_data["related"]:
            assert isinstance(related, str)
            assert len(related) > 0


def test_taxonomy_no_duplicate_keywords():
    """Test that each category has unique keywords."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        keywords = category_data["keywords"]
        assert len(keywords) == len(set(keywords))


def test_taxonomy_expected_categories():
    """Test that taxonomy includes expected core categories."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    expected_categories = [
        "running_shoes",
        "athletic_footwear",
        "marathon_gear",
        "fitness_trackers",
        "electronics",
        "smartphones",
        "travel_destinations",
        "automotive",
        "insurance",
        "credit_cards",
        "health_wellness",
        "online_courses",
        "home_furniture",
        "fashion_clothing",
    ]
    
    for category in expected_categories:
        assert category in taxonomy


def test_taxonomy_keywords_lowercase():
    """Test that keywords are in lowercase for consistent matching."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        for keyword in category_data["keywords"]:
            # Keywords should be lowercase or contain proper nouns
            # We'll check that they're not ALL CAPS
            assert keyword != keyword.upper() or len(keyword) <= 3


def test_taxonomy_related_not_empty():
    """Test that each category has at least one related interest."""
    project_root = Path(__file__).parent.parent.parent
    taxonomy_path = project_root / "data" / "taxonomy.json"
    with open(taxonomy_path, "r") as f:
        taxonomy = json.load(f)
    
    for category_name, category_data in taxonomy.items():
        assert len(category_data["related"]) >= 1
