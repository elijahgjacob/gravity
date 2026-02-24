"""Integration tests for GraphitiRepository.

Note: These tests use mocks as they require a running Neo4j instance.
For true integration testing with a real Neo4j database, set up a test
Neo4j instance and modify the tests accordingly.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from src.repositories.graphiti_repository import GraphitiRepository


class TestGraphitiRepositoryIntegration:
    """Integration tests for GraphitiRepository."""
    
    @pytest.mark.asyncio
    async def test_full_episode_lifecycle(self, graphiti_test_config, mock_graphiti_client):
        """Test complete episode lifecycle: init, add, shutdown."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti.return_value = mock_graphiti_client
            
            # Initialize repository
            repo = GraphitiRepository(**graphiti_test_config)
            await repo.initialize()
            
            assert repo.is_initialized
            
            # Add multiple episodes
            episodes = [
                ("episode_1", "User searched for running shoes"),
                ("episode_2", "User searched for marathon training"),
                ("episode_3", "User searched for running watch")
            ]
            
            for name, body in episodes:
                await repo.add_episode(name=name, episode_body=body)
            
            # Verify all episodes were added
            assert mock_graphiti_client.add_episode.call_count == 3
            
            # Shutdown
            await repo.shutdown()
            assert not repo.is_initialized
    
    @pytest.mark.asyncio
    async def test_concurrent_episode_additions(self, graphiti_test_config, mock_graphiti_client):
        """Test adding multiple episodes concurrently."""
        import asyncio
        
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti.return_value = mock_graphiti_client
            
            repo = GraphitiRepository(**graphiti_test_config)
            await repo.initialize()
            
            # Add episodes concurrently
            tasks = [
                repo.add_episode(
                    name=f"episode_{i}",
                    episode_body=f"Test episode {i}"
                )
                for i in range(10)
            ]
            
            await asyncio.gather(*tasks)
            
            # Verify all episodes were added
            assert mock_graphiti_client.add_episode.call_count == 10
            
            await repo.shutdown()
    
    @pytest.mark.asyncio
    async def test_episode_with_rich_context(self, graphiti_test_config, mock_graphiti_client, sample_query_event):
        """Test adding episode with rich query event context."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti.return_value = mock_graphiti_client
            
            repo = GraphitiRepository(**graphiti_test_config)
            await repo.initialize()
            
            # Build rich episode body
            event = sample_query_event
            episode_body = f"""
            User Query: {event['query']}
            Context: {event['context']}
            Ad Eligibility: {event['eligibility']}
            Categories: {', '.join(event['categories'])}
            Top Campaign: {event['campaigns'][0]['campaign_id']} (score: {event['campaigns'][0]['relevance_score']})
            """
            
            await repo.add_episode(
                name="query_rich_context",
                episode_body=episode_body,
                source_description="Ad Retrieval Query"
            )
            
            # Verify episode was added with correct data
            mock_graphiti_client.add_episode.assert_called_once()
            call_args = mock_graphiti_client.add_episode.call_args
            assert "running shoes for marathon" in call_args.kwargs["episode_body"]
            assert "0.95" in call_args.kwargs["episode_body"]
            
            await repo.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, graphiti_test_config):
        """Test that repository can recover from errors."""
        with patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            # Setup mock to fail first time, succeed second time
            mock_client = MagicMock()
            call_count = 0
            
            async def add_episode_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Temporary network error")
                return None
            
            mock_client.add_episode = AsyncMock(side_effect=add_episode_side_effect)
            mock_graphiti.return_value = mock_client
            
            repo = GraphitiRepository(**graphiti_test_config)
            await repo.initialize()
            
            # First attempt should fail
            with pytest.raises(Exception) as exc_info:
                await repo.add_episode(
                    name="episode_1",
                    episode_body="Test episode"
                )
            assert "Temporary network error" in str(exc_info.value)
            
            # Second attempt should succeed
            await repo.add_episode(
                name="episode_2",
                episode_body="Test episode 2"
            )
            
            assert call_count == 2
            
            await repo.shutdown()


class TestGraphitiRepositoryConfiguration:
    """Test different configuration scenarios."""
    
    @pytest.mark.asyncio
    async def test_different_llm_models(self):
        """Test initialization with different LLM models."""
        models = [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4",
            "google/gemini-pro",
            "meta-llama/llama-3-70b-instruct"
        ]
        
        for model in models:
            with patch('graphiti_core.Graphiti') as mock_graphiti, \
                 patch('graphiti_core.llm_client.OpenAIClient') as mock_llm:
                
                mock_graphiti.return_value = MagicMock()
                
                repo = GraphitiRepository(
                    neo4j_uri="bolt://localhost:7687",
                    neo4j_user="neo4j",
                    neo4j_password="password",
                    openrouter_api_key="sk-test-key",
                    llm_model=model
                )
                
                await repo.initialize()
                
                # Verify correct model was used
                mock_llm.assert_called_once()
                assert mock_llm.call_args.kwargs["model"] == model
                
                await repo.shutdown()
    
    @pytest.mark.asyncio
    async def test_different_namespaces(self):
        """Test initialization with different namespaces."""
        namespaces = ["production", "staging", "test", "dev"]
        
        for namespace in namespaces:
            with patch('graphiti_core.Graphiti') as mock_graphiti, \
                 patch('graphiti_core.llm_client.OpenAIClient'):
                
                mock_graphiti.return_value = MagicMock()
                
                repo = GraphitiRepository(
                    neo4j_uri="bolt://localhost:7687",
                    neo4j_user="neo4j",
                    neo4j_password="password",
                    openrouter_api_key="sk-test-key",
                    llm_model="anthropic/claude-3.5-sonnet",
                    namespace=namespace
                )
                
                assert repo.namespace == namespace
                
                await repo.initialize()
                await repo.shutdown()
