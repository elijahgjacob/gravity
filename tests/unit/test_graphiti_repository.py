"""Unit tests for GraphitiRepository."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.repositories.graphiti_repository import GraphitiRepository


class TestGraphitiRepositoryInitialization:
    """Test GraphitiRepository initialization."""
    
    def test_repository_creation(self):
        """Test creating a GraphitiRepository instance."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet",
            namespace="test_namespace"
        )
        
        assert repo.neo4j_uri == "bolt://localhost:7687"
        assert repo.neo4j_user == "neo4j"
        assert repo.neo4j_password == "password"
        assert repo.openrouter_api_key == "sk-test-key"
        assert repo.llm_model == "anthropic/claude-3.5-sonnet"
        assert repo.namespace == "test_namespace"
        assert not repo.is_initialized
    
    def test_repository_default_namespace(self):
        """Test that default namespace is set correctly."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet"
        )
        
        assert repo.namespace == "ad_retrieval"
    
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization with mocked Graphiti."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient') as mock_llm_client:
            
            # Setup mocks
            mock_llm_instance = MagicMock()
            mock_llm_client.return_value = mock_llm_instance
            
            mock_graphiti_instance = MagicMock()
            mock_graphiti.return_value = mock_graphiti_instance
            
            # Create and initialize repository
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            
            await repo.initialize()
            
            # Verify LLM client was configured with OpenRouter
            mock_llm_client.assert_called_once_with(
                api_key="sk-test-key",
                base_url="https://openrouter.ai/api/v1",
                model="anthropic/claude-3.5-sonnet"
            )
            
            # Verify Graphiti was initialized
            mock_graphiti.assert_called_once_with(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password",
                llm_client=mock_llm_instance
            )
            
            assert repo.is_initialized
    
    @pytest.mark.asyncio
    async def test_initialize_import_error(self):
        """Test initialization fails gracefully when Graphiti is not installed."""
        with patch.dict('sys.modules', {'graphiti_core': None}):
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            
            with pytest.raises(ImportError) as exc_info:
                await repo.initialize()
            
            assert "graphiti-core is not installed" in str(exc_info.value)
            assert not repo.is_initialized


class TestGraphitiRepositoryEpisodes:
    """Test episode management in GraphitiRepository."""
    
    @pytest.mark.asyncio
    async def test_add_episode_success(self):
        """Test successfully adding an episode."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            # Setup mock
            mock_client = MagicMock()
            mock_client.add_episode = AsyncMock()
            mock_graphiti.return_value = mock_client
            
            # Create and initialize repository
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            await repo.initialize()
            
            # Add episode
            await repo.add_episode(
                name="test_episode",
                episode_body="Test episode content",
                source_description="Test Source"
            )
            
            # Verify episode was added
            mock_client.add_episode.assert_called_once()
            call_args = mock_client.add_episode.call_args
            assert call_args.kwargs["name"] == "test_episode"
            assert call_args.kwargs["episode_body"] == "Test episode content"
            assert call_args.kwargs["source_description"] == "Test Source"
    
    @pytest.mark.asyncio
    async def test_add_episode_with_reference_time(self):
        """Test adding an episode with custom reference time."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            # Setup mock
            mock_client = MagicMock()
            mock_client.add_episode = AsyncMock()
            mock_graphiti.return_value = mock_client
            
            # Create and initialize repository
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            await repo.initialize()
            
            # Add episode with custom time
            custom_time = datetime(2026, 2, 22, 12, 0, 0)
            await repo.add_episode(
                name="test_episode",
                episode_body="Test content",
                reference_time=custom_time
            )
            
            # Verify reference time was passed
            call_args = mock_client.add_episode.call_args
            assert call_args.kwargs["reference_time"] == custom_time
    
    @pytest.mark.asyncio
    async def test_add_episode_not_initialized(self):
        """Test that adding episode fails if repository not initialized."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await repo.add_episode(
                name="test_episode",
                episode_body="Test content"
            )
        
        assert "not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_add_episode_error_handling(self):
        """Test error handling when episode creation fails."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            # Setup mock to raise error
            mock_client = MagicMock()
            mock_client.add_episode = AsyncMock(side_effect=Exception("Neo4j connection failed"))
            mock_graphiti.return_value = mock_client
            
            # Create and initialize repository
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            await repo.initialize()
            
            # Attempt to add episode
            with pytest.raises(Exception) as exc_info:
                await repo.add_episode(
                    name="test_episode",
                    episode_body="Test content"
                )
            
            assert "Neo4j connection failed" in str(exc_info.value)


class TestGraphitiRepositoryQueries:
    """Test query methods in GraphitiRepository."""
    
    @pytest.mark.asyncio
    async def test_get_user_journey_not_initialized(self):
        """Test that get_user_journey fails if repository not initialized."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await repo.get_user_journey(user_id="user_123")
        
        assert "not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_campaign_relationships_not_initialized(self):
        """Test that get_campaign_relationships fails if repository not initialized."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await repo.get_campaign_relationships(campaign_id="camp_123")
        
        assert "not initialized" in str(exc_info.value)


class TestGraphitiRepositoryShutdown:
    """Test repository shutdown."""
    
    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti.return_value = MagicMock()
            
            repo = GraphitiRepository(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                openrouter_api_key="sk-test-key",
                llm_model="anthropic/claude-3.5-sonnet"
            )
            await repo.initialize()
            
            assert repo.is_initialized
            
            await repo.shutdown()
            
            assert not repo.is_initialized
    
    @pytest.mark.asyncio
    async def test_shutdown_when_not_initialized(self):
        """Test shutdown when repository was never initialized."""
        repo = GraphitiRepository(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password",
            openrouter_api_key="sk-test-key",
            llm_model="anthropic/claude-3.5-sonnet"
        )
        
        # Should not raise error
        await repo.shutdown()
        
        assert not repo.is_initialized
