"""Unit tests for GraphitiService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.services.graphiti_service import GraphitiService
from src.repositories.graphiti_repository import GraphitiRepository


class TestGraphitiServiceInitialization:
    """Test GraphitiService initialization."""
    
    def test_service_creation(self):
        """Test creating a GraphitiService instance."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        service = GraphitiService(repository=mock_repo)
        
        assert service.repository == mock_repo


class TestGraphitiServiceRecordQueryEvent:
    """Test query event recording."""
    
    @pytest.mark.asyncio
    async def test_record_simple_query_event(self):
        """Test recording a simple query event."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        await service.record_query_event(
            query="running shoes",
            context=None,
            eligibility=0.95,
            categories=["running_shoes"],
            campaigns=[]
        )
        
        # Verify episode was added
        mock_repo.add_episode.assert_called_once()
        call_args = mock_repo.add_episode.call_args
        
        assert "query_" in call_args.kwargs["name"]
        assert "running shoes" in call_args.kwargs["episode_body"]
        assert call_args.kwargs["source_description"] == "Ad Retrieval Query"
    
    @pytest.mark.asyncio
    async def test_record_query_event_with_context(self):
        """Test recording query event with user context."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        context = {
            "age": 30,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness", "running"]
        }
        
        await service.record_query_event(
            query="best marathon shoes",
            context=context,
            eligibility=0.95,
            categories=["running_shoes", "marathon_gear"],
            campaigns=[]
        )
        
        call_args = mock_repo.add_episode.call_args
        episode_body = call_args.kwargs["episode_body"]
        
        assert "30 years old" in episode_body
        assert "male" in episode_body
        assert "San Francisco, CA" in episode_body
        assert "fitness" in episode_body
        assert "running" in episode_body
    
    @pytest.mark.asyncio
    async def test_record_query_event_with_campaigns(self):
        """Test recording query event with campaigns."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        campaigns = [
            {
                "campaign_id": "camp_123",
                "title": "Nike Running Shoes",
                "category": "running_shoes",
                "relevance_score": 0.94
            },
            {
                "campaign_id": "camp_456",
                "title": "Adidas Marathon Trainers",
                "category": "marathon_gear",
                "relevance_score": 0.90
            }
        ]
        
        await service.record_query_event(
            query="running shoes",
            context=None,
            eligibility=0.95,
            categories=["running_shoes"],
            campaigns=campaigns
        )
        
        call_args = mock_repo.add_episode.call_args
        episode_body = call_args.kwargs["episode_body"]
        
        assert "Nike Running Shoes" in episode_body
        assert "0.94" in episode_body
        assert "Adidas Marathon Trainers" in episode_body
    
    @pytest.mark.asyncio
    async def test_record_query_event_with_session_id(self):
        """Test recording query event with session ID."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        await service.record_query_event(
            query="running shoes",
            context=None,
            eligibility=0.95,
            categories=["running_shoes"],
            campaigns=[],
            session_id="sess_abc123"
        )
        
        call_args = mock_repo.add_episode.call_args
        episode_name = call_args.kwargs["name"]
        
        assert "sess_abc123" in episode_name
    
    @pytest.mark.asyncio
    async def test_record_query_event_error_handling(self):
        """Test error handling when recording fails."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock(side_effect=Exception("Neo4j connection failed"))
        
        service = GraphitiService(repository=mock_repo)
        
        with pytest.raises(Exception) as exc_info:
            await service.record_query_event(
                query="running shoes",
                context=None,
                eligibility=0.95,
                categories=["running_shoes"],
                campaigns=[]
            )
        
        assert "Neo4j connection failed" in str(exc_info.value)


class TestGraphitiServiceBuildEpisode:
    """Test episode building logic."""
    
    def test_build_episode_simple(self):
        """Test building a simple episode."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        service = GraphitiService(repository=mock_repo)
        
        episode = service._build_episode(
            query="running shoes",
            context=None,
            eligibility=0.95,
            categories=["running_shoes"],
            campaigns=[]
        )
        
        assert "running shoes" in episode
        assert "0.95" in episode
        assert "highly appropriate" in episode
        assert "running_shoes" in episode
    
    def test_build_episode_with_full_context(self):
        """Test building episode with complete context."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        service = GraphitiService(repository=mock_repo)
        
        context = {
            "age": 30,
            "gender": "male",
            "location": "San Francisco, CA",
            "interests": ["fitness", "running", "health"]
        }
        
        campaigns = [
            {
                "campaign_id": "camp_123",
                "title": "Nike Running Shoes",
                "category": "running_shoes",
                "relevance_score": 0.94
            }
        ]
        
        episode = service._build_episode(
            query="best running shoes",
            context=context,
            eligibility=0.95,
            categories=["running_shoes", "athletic_footwear"],
            campaigns=campaigns
        )
        
        assert "best running shoes" in episode
        assert "30 years old" in episode
        assert "male" in episode
        assert "San Francisco, CA" in episode
        assert "fitness" in episode
        assert "Nike Running Shoes" in episode
        assert "running_shoes" in episode
        assert "athletic_footwear" in episode
    
    def test_build_episode_eligibility_descriptions(self):
        """Test that eligibility scores get appropriate descriptions."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        service = GraphitiService(repository=mock_repo)
        
        # High eligibility
        episode_high = service._build_episode(
            query="test", context=None, eligibility=0.9,
            categories=["test"], campaigns=[]
        )
        assert "highly appropriate" in episode_high
        
        # Medium eligibility
        episode_medium = service._build_episode(
            query="test", context=None, eligibility=0.6,
            categories=["test"], campaigns=[]
        )
        assert "moderately appropriate" in episode_medium
        
        # Low eligibility
        episode_low = service._build_episode(
            query="test", context=None, eligibility=0.3,
            categories=["test"], campaigns=[]
        )
        assert "not appropriate" in episode_low
    
    def test_build_episode_truncates_campaigns(self):
        """Test that only first 3 campaigns are included in detail."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        service = GraphitiService(repository=mock_repo)
        
        campaigns = [
            {"campaign_id": f"camp_{i}", "title": f"Campaign {i}",
             "category": "test", "relevance_score": 0.9}
            for i in range(5)
        ]
        
        episode = service._build_episode(
            query="test",
            context=None,
            eligibility=0.95,
            categories=["test"],
            campaigns=campaigns
        )
        
        assert "Campaign 0" in episode
        assert "Campaign 1" in episode
        assert "Campaign 2" in episode
        assert "and 2 more campaigns" in episode


class TestGraphitiServiceRecordCampaignClick:
    """Test campaign click recording."""
    
    @pytest.mark.asyncio
    async def test_record_campaign_click(self):
        """Test recording a campaign click event."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        await service.record_campaign_click(
            query="running shoes",
            campaign_id="camp_123",
            campaign_title="Nike Running Shoes",
            position=0
        )
        
        mock_repo.add_episode.assert_called_once()
        call_args = mock_repo.add_episode.call_args
        
        assert "click_" in call_args.kwargs["name"]
        assert "camp_123" in call_args.kwargs["name"]
        assert "Nike Running Shoes" in call_args.kwargs["episode_body"]
        assert "running shoes" in call_args.kwargs["episode_body"]
        assert "Position in results: 0" in call_args.kwargs["episode_body"]
        assert call_args.kwargs["source_description"] == "Campaign Click"
    
    @pytest.mark.asyncio
    async def test_record_campaign_click_with_session(self):
        """Test recording campaign click with session ID."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock()
        
        service = GraphitiService(repository=mock_repo)
        
        await service.record_campaign_click(
            query="running shoes",
            campaign_id="camp_123",
            campaign_title="Nike Running Shoes",
            position=0,
            session_id="sess_abc123"
        )
        
        call_args = mock_repo.add_episode.call_args
        episode_name = call_args.kwargs["name"]
        
        assert "sess_abc123" in episode_name
    
    @pytest.mark.asyncio
    async def test_record_campaign_click_error_handling(self):
        """Test error handling when click recording fails."""
        mock_repo = MagicMock(spec=GraphitiRepository)
        mock_repo.add_episode = AsyncMock(side_effect=Exception("Connection error"))
        
        service = GraphitiService(repository=mock_repo)
        
        with pytest.raises(Exception) as exc_info:
            await service.record_campaign_click(
                query="running shoes",
                campaign_id="camp_123",
                campaign_title="Nike Running Shoes",
                position=0
            )
        
        assert "Connection error" in str(exc_info.value)
