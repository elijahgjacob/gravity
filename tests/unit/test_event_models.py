"""Unit tests for Graphiti event models."""

from datetime import datetime
import pytest
from pydantic import ValidationError
from src.api.models.events import (
    CampaignImpression,
    QueryEvent,
    UserSession,
    GraphitiEpisode
)


class TestCampaignImpression:
    """Test CampaignImpression model."""
    
    def test_valid_campaign_impression(self):
        """Test creating a valid campaign impression."""
        impression = CampaignImpression(
            campaign_id="camp_123",
            position=0,
            relevance_score=0.95,
            category="running_shoes"
        )
        
        assert impression.campaign_id == "camp_123"
        assert impression.position == 0
        assert impression.relevance_score == 0.95
        assert impression.category == "running_shoes"
    
    def test_campaign_impression_position_validation(self):
        """Test that position must be non-negative."""
        with pytest.raises(ValidationError) as exc_info:
            CampaignImpression(
                campaign_id="camp_123",
                position=-1,
                relevance_score=0.95,
                category="running_shoes"
            )
        
        assert "position" in str(exc_info.value)
    
    def test_campaign_impression_relevance_score_bounds(self):
        """Test that relevance_score must be between 0.0 and 1.0."""
        # Test lower bound
        with pytest.raises(ValidationError) as exc_info:
            CampaignImpression(
                campaign_id="camp_123",
                position=0,
                relevance_score=-0.1,
                category="running_shoes"
            )
        assert "relevance_score" in str(exc_info.value)
        
        # Test upper bound
        with pytest.raises(ValidationError) as exc_info:
            CampaignImpression(
                campaign_id="camp_123",
                position=0,
                relevance_score=1.1,
                category="running_shoes"
            )
        assert "relevance_score" in str(exc_info.value)
    
    def test_campaign_impression_serialization(self):
        """Test that campaign impression can be serialized to dict."""
        impression = CampaignImpression(
            campaign_id="camp_123",
            position=0,
            relevance_score=0.95,
            category="running_shoes"
        )
        
        data = impression.model_dump()
        
        assert data["campaign_id"] == "camp_123"
        assert data["position"] == 0
        assert data["relevance_score"] == 0.95
        assert data["category"] == "running_shoes"


class TestQueryEvent:
    """Test QueryEvent model."""
    
    def test_valid_query_event(self):
        """Test creating a valid query event."""
        event = QueryEvent(
            query="running shoes for marathon",
            context={"age": 30, "gender": "male"},
            eligibility=0.95,
            categories=["running_shoes", "marathon_gear"]
        )
        
        assert event.query == "running shoes for marathon"
        assert event.context == {"age": 30, "gender": "male"}
        assert event.eligibility == 0.95
        assert event.categories == ["running_shoes", "marathon_gear"]
        assert isinstance(event.timestamp, datetime)
        assert event.session_id is None
        assert event.campaigns == []
    
    def test_query_event_with_campaigns(self):
        """Test query event with campaign impressions."""
        campaigns = [
            CampaignImpression(
                campaign_id="camp_123",
                position=0,
                relevance_score=0.95,
                category="running_shoes"
            ),
            CampaignImpression(
                campaign_id="camp_456",
                position=1,
                relevance_score=0.90,
                category="marathon_gear"
            )
        ]
        
        event = QueryEvent(
            query="running shoes",
            eligibility=0.95,
            categories=["running_shoes"],
            campaigns=campaigns
        )
        
        assert len(event.campaigns) == 2
        assert event.campaigns[0].campaign_id == "camp_123"
        assert event.campaigns[1].campaign_id == "camp_456"
    
    def test_query_event_with_session_id(self):
        """Test query event with session ID."""
        event = QueryEvent(
            query="running shoes",
            eligibility=0.95,
            categories=["running_shoes"],
            session_id="sess_abc123"
        )
        
        assert event.session_id == "sess_abc123"
    
    def test_query_event_query_length_validation(self):
        """Test that query must be between 1 and 500 characters."""
        # Test empty query
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="",
                eligibility=0.95,
                categories=["general"]
            )
        assert "query" in str(exc_info.value)
        
        # Test query too long
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="a" * 501,
                eligibility=0.95,
                categories=["general"]
            )
        assert "query" in str(exc_info.value)
    
    def test_query_event_eligibility_bounds(self):
        """Test that eligibility must be between 0.0 and 1.0."""
        # Test lower bound
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="test",
                eligibility=-0.1,
                categories=["general"]
            )
        assert "eligibility" in str(exc_info.value)
        
        # Test upper bound
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="test",
                eligibility=1.1,
                categories=["general"]
            )
        assert "eligibility" in str(exc_info.value)
    
    def test_query_event_categories_validation(self):
        """Test that categories must have 1-10 items."""
        # Test empty categories
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="test",
                eligibility=0.95,
                categories=[]
            )
        assert "categories" in str(exc_info.value)
        
        # Test too many categories
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="test",
                eligibility=0.95,
                categories=[f"cat_{i}" for i in range(11)]
            )
        assert "categories" in str(exc_info.value)
    
    def test_query_event_campaigns_max_length(self):
        """Test that campaigns list is limited to 10 items."""
        campaigns = [
            CampaignImpression(
                campaign_id=f"camp_{i}",
                position=i,
                relevance_score=0.9,
                category="test"
            )
            for i in range(11)
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            QueryEvent(
                query="test",
                eligibility=0.95,
                categories=["test"],
                campaigns=campaigns
            )
        assert "campaigns" in str(exc_info.value)
    
    def test_query_event_serialization(self):
        """Test that query event can be serialized to dict."""
        event = QueryEvent(
            query="running shoes",
            context={"age": 30},
            eligibility=0.95,
            categories=["running_shoes"]
        )
        
        data = event.model_dump()
        
        assert data["query"] == "running shoes"
        assert data["context"] == {"age": 30}
        assert data["eligibility"] == 0.95
        assert data["categories"] == ["running_shoes"]
        assert "timestamp" in data


class TestUserSession:
    """Test UserSession model."""
    
    def test_valid_user_session(self):
        """Test creating a valid user session."""
        session = UserSession(
            session_id="sess_123",
            user_id="user_456"
        )
        
        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
        assert isinstance(session.start_time, datetime)
        assert session.end_time is None
        assert session.query_count == 0
        assert session.queries == []
    
    def test_user_session_with_queries(self):
        """Test user session with queries."""
        queries = ["running shoes", "marathon training", "running watch"]
        
        session = UserSession(
            session_id="sess_123",
            query_count=3,
            queries=queries
        )
        
        assert session.query_count == 3
        assert session.queries == queries
    
    def test_user_session_query_count_validation(self):
        """Test that query_count must be non-negative."""
        with pytest.raises(ValidationError) as exc_info:
            UserSession(
                session_id="sess_123",
                query_count=-1
            )
        assert "query_count" in str(exc_info.value)
    
    def test_user_session_serialization(self):
        """Test that user session can be serialized to dict."""
        session = UserSession(
            session_id="sess_123",
            user_id="user_456",
            query_count=2,
            queries=["query1", "query2"]
        )
        
        data = session.model_dump()
        
        assert data["session_id"] == "sess_123"
        assert data["user_id"] == "user_456"
        assert data["query_count"] == 2
        assert data["queries"] == ["query1", "query2"]


class TestGraphitiEpisode:
    """Test GraphitiEpisode model."""
    
    def test_valid_graphiti_episode(self):
        """Test creating a valid Graphiti episode."""
        episode = GraphitiEpisode(
            name="query_123",
            episode_body="User searched for running shoes"
        )
        
        assert episode.name == "query_123"
        assert episode.episode_body == "User searched for running shoes"
        assert episode.source_description == "Ad Retrieval Query"
        assert isinstance(episode.reference_time, datetime)
    
    def test_graphiti_episode_custom_source(self):
        """Test Graphiti episode with custom source description."""
        episode = GraphitiEpisode(
            name="query_123",
            episode_body="Test episode",
            source_description="Test Source"
        )
        
        assert episode.source_description == "Test Source"
    
    def test_graphiti_episode_empty_body_validation(self):
        """Test that episode_body cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            GraphitiEpisode(
                name="query_123",
                episode_body=""
            )
        assert "episode_body" in str(exc_info.value)
    
    def test_graphiti_episode_serialization(self):
        """Test that Graphiti episode can be serialized to dict."""
        episode = GraphitiEpisode(
            name="query_123",
            episode_body="User searched for running shoes"
        )
        
        data = episode.model_dump()
        
        assert data["name"] == "query_123"
        assert data["episode_body"] == "User searched for running shoes"
        assert data["source_description"] == "Ad Retrieval Query"
        assert "reference_time" in data


class TestEventModelIntegration:
    """Test integration between event models."""
    
    def test_query_event_with_full_data(self):
        """Test creating a complete query event with all fields."""
        campaigns = [
            CampaignImpression(
                campaign_id=f"camp_{i}",
                position=i,
                relevance_score=0.9 - (i * 0.05),
                category="running_shoes"
            )
            for i in range(5)
        ]
        
        event = QueryEvent(
            query="best running shoes for marathon training",
            context={
                "age": 30,
                "gender": "male",
                "location": "San Francisco, CA",
                "interests": ["fitness", "running", "health"]
            },
            eligibility=0.95,
            categories=["running_shoes", "marathon_gear", "athletic_footwear"],
            campaigns=campaigns,
            session_id="sess_abc123"
        )
        
        assert event.query == "best running shoes for marathon training"
        assert event.context["age"] == 30
        assert event.eligibility == 0.95
        assert len(event.categories) == 3
        assert len(event.campaigns) == 5
        assert event.session_id == "sess_abc123"
        
        # Verify campaigns are properly ordered
        for i, campaign in enumerate(event.campaigns):
            assert campaign.position == i
            assert campaign.relevance_score == 0.9 - (i * 0.05)
