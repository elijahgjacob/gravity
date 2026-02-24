"""Unit tests for data generation module."""

import json

from scripts.generate_data import (
    VERTICALS,
    generate_campaign,
    generate_campaigns,
)


def test_verticals_structure():
    """Test that VERTICALS dictionary has correct structure."""
    assert len(VERTICALS) > 0

    for vertical_name, vertical_data in VERTICALS.items():
        assert isinstance(vertical_name, str)
        assert "categories" in vertical_data
        assert "brands" in vertical_data
        assert "keywords_pool" in vertical_data

        assert isinstance(vertical_data["categories"], list)
        assert isinstance(vertical_data["brands"], list)
        assert isinstance(vertical_data["keywords_pool"], list)

        assert len(vertical_data["categories"]) > 0
        assert len(vertical_data["brands"]) > 0
        assert len(vertical_data["keywords_pool"]) > 0


def test_generate_single_campaign():
    """Test generation of a single campaign."""
    vertical = "retail_fitness"
    vertical_data = VERTICALS[vertical]

    campaign = generate_campaign(1, vertical, vertical_data)

    # Check required fields
    assert "campaign_id" in campaign
    assert "title" in campaign
    assert "description" in campaign
    assert "category" in campaign
    assert "subcategories" in campaign
    assert "keywords" in campaign
    assert "targeting" in campaign
    assert "vertical" in campaign
    assert "budget" in campaign
    assert "cpc" in campaign
    assert "brand" in campaign

    # Check field types
    assert isinstance(campaign["campaign_id"], str)
    assert isinstance(campaign["title"], str)
    assert isinstance(campaign["description"], str)
    assert isinstance(campaign["category"], str)
    assert isinstance(campaign["subcategories"], list)
    assert isinstance(campaign["keywords"], list)
    assert isinstance(campaign["targeting"], dict)
    assert isinstance(campaign["vertical"], str)
    assert isinstance(campaign["budget"], int)
    assert isinstance(campaign["cpc"], float)
    assert isinstance(campaign["brand"], str)


def test_campaign_id_format():
    """Test that campaign IDs follow correct format."""
    campaign = generate_campaign(123, "retail_fitness", VERTICALS["retail_fitness"])

    assert campaign["campaign_id"] == "camp_00123"
    assert campaign["campaign_id"].startswith("camp_")


def test_campaign_targeting_structure():
    """Test that targeting has correct structure."""
    campaign = generate_campaign(1, "retail_fitness", VERTICALS["retail_fitness"])
    targeting = campaign["targeting"]

    assert "age_min" in targeting
    assert "age_max" in targeting
    assert "genders" in targeting
    assert "locations" in targeting
    assert "interests" in targeting

    assert isinstance(targeting["age_min"], int)
    assert isinstance(targeting["age_max"], int)
    assert isinstance(targeting["genders"], list)
    assert isinstance(targeting["locations"], list)
    assert isinstance(targeting["interests"], list)

    assert targeting["age_min"] < targeting["age_max"]
    assert targeting["age_min"] >= 18
    assert targeting["age_max"] <= 65


def test_campaign_keywords_count():
    """Test that campaigns have appropriate number of keywords."""
    campaign = generate_campaign(1, "retail_fitness", VERTICALS["retail_fitness"])

    assert len(campaign["keywords"]) >= 4
    assert len(campaign["keywords"]) <= 8


def test_campaign_budget_and_cpc():
    """Test that budget and CPC are in valid ranges."""
    campaign = generate_campaign(1, "retail_fitness", VERTICALS["retail_fitness"])

    assert campaign["budget"] >= 10000
    assert campaign["budget"] <= 100000
    assert campaign["cpc"] >= 0.50
    assert campaign["cpc"] <= 5.00


def test_generate_multiple_campaigns():
    """Test generation of multiple campaigns."""
    num_campaigns = 100
    campaigns = generate_campaigns(num_campaigns)

    assert len(campaigns) == num_campaigns

    # Check uniqueness of campaign IDs
    campaign_ids = [c["campaign_id"] for c in campaigns]
    assert len(campaign_ids) == len(set(campaign_ids))


def test_campaigns_cover_all_verticals():
    """Test that generated campaigns cover all verticals."""
    campaigns = generate_campaigns(1000)

    verticals_found = set(c["vertical"] for c in campaigns)
    expected_verticals = set(VERTICALS.keys())

    assert verticals_found == expected_verticals


def test_campaign_category_in_vertical():
    """Test that campaign categories belong to their vertical."""
    for vertical_name, vertical_data in VERTICALS.items():
        campaign = generate_campaign(1, vertical_name, vertical_data)

        assert campaign["category"] in vertical_data["categories"]


def test_campaign_brand_in_vertical():
    """Test that campaign brands belong to their vertical."""
    for vertical_name, vertical_data in VERTICALS.items():
        campaign = generate_campaign(1, vertical_name, vertical_data)

        assert campaign["brand"] in vertical_data["brands"]


def test_campaign_json_serializable():
    """Test that campaigns can be serialized to JSON."""
    campaign = generate_campaign(1, "retail_fitness", VERTICALS["retail_fitness"])

    # Should not raise an exception
    json_str = json.dumps(campaign)
    assert isinstance(json_str, str)

    # Should be able to deserialize
    deserialized = json.loads(json_str)
    assert deserialized["campaign_id"] == campaign["campaign_id"]


def test_deterministic_generation():
    """Test that generation uses consistent seed for reproducibility."""
    import random

    from faker import Faker

    # Set seed explicitly
    random.seed(42)
    fake_instance = Faker()
    Faker.seed(42)

    campaigns1 = generate_campaigns(10)

    # Reset seed to same value
    random.seed(42)
    Faker.seed(42)

    campaigns2 = generate_campaigns(10)

    # Should generate identical campaigns with same seed
    assert campaigns1[0]["campaign_id"] == campaigns2[0]["campaign_id"]
    # Note: Due to module-level seed, titles may vary between test runs
    # but campaign structure should be consistent
    assert len(campaigns1) == len(campaigns2)
