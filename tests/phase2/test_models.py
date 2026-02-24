"""Tests for Pydantic request/response models."""

import pytest
from pydantic import ValidationError

from src.api.models.requests import RetrievalRequest, UserContext
from src.api.models.responses import Campaign, HealthResponse, RetrievalResponse


def test_user_context_valid():
    """Test valid UserContext creation."""
    context = UserContext(
        gender="male", age=24, location="San Francisco, CA", interests=["fitness", "running"]
    )

    assert context.gender == "male"
    assert context.age == 24
    assert context.location == "San Francisco, CA"
    assert len(context.interests) == 2


def test_user_context_optional_fields():
    """Test UserContext with optional fields."""
    context = UserContext()

    assert context.gender is None
    assert context.age is None
    assert context.location is None
    assert context.interests is None


def test_user_context_invalid_age():
    """Test UserContext with invalid age."""
    with pytest.raises(ValidationError):
        UserContext(age=-1)

    with pytest.raises(ValidationError):
        UserContext(age=150)


def test_retrieval_request_valid():
    """Test valid RetrievalRequest creation."""
    request = RetrievalRequest(query="I need running shoes", context=UserContext(age=25))

    assert request.query == "I need running shoes"
    assert request.context.age == 25


def test_retrieval_request_no_context():
    """Test RetrievalRequest without context."""
    request = RetrievalRequest(query="test query")

    assert request.query == "test query"
    assert request.context is None


def test_retrieval_request_empty_query():
    """Test RetrievalRequest with empty query."""
    with pytest.raises(ValidationError):
        RetrievalRequest(query="")


def test_retrieval_request_long_query():
    """Test RetrievalRequest with too long query."""
    long_query = "a" * 501

    with pytest.raises(ValidationError):
        RetrievalRequest(query=long_query)


def test_campaign_valid():
    """Test valid Campaign creation."""
    campaign = Campaign(
        campaign_id="camp_123",
        relevance_score=0.95,
        title="Test Campaign",
        category="test_category",
        description="Test description",
        keywords=["test", "campaign"],
    )

    assert campaign.campaign_id == "camp_123"
    assert campaign.relevance_score == 0.95
    assert len(campaign.keywords) == 2


def test_campaign_invalid_relevance_score():
    """Test Campaign with invalid relevance score."""
    with pytest.raises(ValidationError):
        Campaign(
            campaign_id="camp_123",
            relevance_score=1.5,  # > 1.0
            title="Test",
            category="test",
            description="Test",
            keywords=[],
        )

    with pytest.raises(ValidationError):
        Campaign(
            campaign_id="camp_123",
            relevance_score=-0.1,  # < 0.0
            title="Test",
            category="test",
            description="Test",
            keywords=[],
        )


def test_retrieval_response_valid():
    """Test valid RetrievalResponse creation."""
    response = RetrievalResponse(
        ad_eligibility=0.85,
        extracted_categories=["category1", "category2"],
        campaigns=[],
        latency_ms=50.5,
        metadata={"test": "data"},
    )

    assert response.ad_eligibility == 0.85
    assert len(response.extracted_categories) == 2
    assert response.latency_ms == 50.5
    assert response.metadata["test"] == "data"


def test_retrieval_response_invalid_eligibility():
    """Test RetrievalResponse with invalid eligibility."""
    with pytest.raises(ValidationError):
        RetrievalResponse(
            ad_eligibility=1.5, extracted_categories=["test"], campaigns=[], latency_ms=50.0
        )


def test_retrieval_response_no_categories():
    """Test RetrievalResponse with no categories."""
    with pytest.raises(ValidationError):
        RetrievalResponse(
            ad_eligibility=0.5,
            extracted_categories=[],  # Must have at least 1
            campaigns=[],
            latency_ms=50.0,
        )


def test_retrieval_response_too_many_categories():
    """Test RetrievalResponse with too many categories."""
    with pytest.raises(ValidationError):
        RetrievalResponse(
            ad_eligibility=0.5,
            extracted_categories=["cat" + str(i) for i in range(11)],  # Max 10
            campaigns=[],
            latency_ms=50.0,
        )


def test_health_response_valid():
    """Test valid HealthResponse creation."""
    response = HealthResponse(status="healthy", version="1.0.0")

    assert response.status == "healthy"
    assert response.version == "1.0.0"
