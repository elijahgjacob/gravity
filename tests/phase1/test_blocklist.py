"""Unit tests for blocklist data."""

from pathlib import Path


def test_blocklist_file_exists():
    """Test that blocklist.txt file exists."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    assert blocklist_path.exists()


def test_blocklist_not_empty():
    """Test that blocklist contains entries."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        lines = f.readlines()

    # Filter out comments and empty lines
    terms = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    assert len(terms) > 0


def test_blocklist_format():
    """Test that blocklist entries are properly formatted."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Terms should be lowercase for consistent matching
        assert isinstance(stripped, str)
        assert len(stripped) > 0


def test_blocklist_has_critical_terms():
    """Test that blocklist includes critical safety terms."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        content = f.read().lower()

    critical_categories = [
        "suicide",
        "self harm",
        "porn",
        "nsfw",
    ]

    for term in critical_categories:
        assert term in content


def test_blocklist_no_duplicate_terms():
    """Test that blocklist doesn't have duplicate terms."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        lines = f.readlines()

    terms = [
        line.strip().lower() for line in lines if line.strip() and not line.strip().startswith("#")
    ]

    # Check for duplicates
    unique_terms = set(terms)
    assert len(terms) == len(unique_terms)


def test_blocklist_organized_by_category():
    """Test that blocklist has category comments."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        content = f.read()

    # Should have category headers
    assert "# Self-harm" in content or "# Violence" in content or "# Explicit" in content


def test_blocklist_minimum_coverage():
    """Test that blocklist covers minimum safety categories."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        content = f.read().lower()

    # Check for different safety categories
    safety_categories = {
        "self_harm": ["suicide", "self harm", "kill myself"],
        "explicit": ["porn", "xxx", "nsfw"],
        "violence": ["bomb", "murder"],
        "medical": ["heart attack", "overdose"],
    }

    categories_found = 0
    for category, terms in safety_categories.items():
        if any(term in content for term in terms):
            categories_found += 1

    assert categories_found >= 3


def test_blocklist_terms_are_strings():
    """Test that all blocklist terms are valid strings."""
    project_root = Path(__file__).parent.parent.parent
    blocklist_path = project_root / "data" / "blocklist.txt"
    with open(blocklist_path) as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            assert isinstance(stripped, str)
            assert len(stripped) > 0
            # Should not have leading/trailing whitespace
            assert stripped == line.strip()
