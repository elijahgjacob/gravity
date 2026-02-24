"""Unit tests for dependency injection."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.core.dependencies import (
    init_dependencies,
    get_retrieval_controller,
    get_dependencies_status,
    shutdown_dependencies
)


class TestDependencyInitialization:
    """Test dependency initialization."""
    
    @pytest.mark.asyncio
    async def test_init_dependencies_without_graphiti(self, monkeypatch):
        """Test initializing dependencies with Graphiti disabled."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "false")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings):
            await init_dependencies()
        
        status = get_dependencies_status()
        assert status["initialized"] is True
        assert status["repositories"]["graphiti"] is False
        
        # Cleanup
        await shutdown_dependencies()
    
    @pytest.mark.asyncio
    async def test_init_dependencies_with_graphiti_enabled(self, monkeypatch):
        """Test initializing dependencies with Graphiti enabled."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "true")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings), \
             patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti_instance = MagicMock()
            mock_graphiti_instance.is_initialized = True
            mock_graphiti.return_value = mock_graphiti_instance
            
            await init_dependencies()
        
        status = get_dependencies_status()
        assert status["initialized"] is True
        # Graphiti initialization is mocked, so it should be initialized
        
        # Cleanup
        await shutdown_dependencies()
    
    @pytest.mark.asyncio
    async def test_init_dependencies_graphiti_fails_gracefully(self, monkeypatch):
        """Test that system continues when Graphiti initialization fails."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "true")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings), \
             patch('graphiti_core.Graphiti', side_effect=Exception("Neo4j connection failed")), \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            # Should not raise exception
            await init_dependencies()
        
        status = get_dependencies_status()
        assert status["initialized"] is True
        assert status["repositories"]["graphiti"] is False
        
        # Cleanup
        await shutdown_dependencies()


class TestGetRetrievalController:
    """Test retrieval controller creation."""
    
    @pytest.mark.asyncio
    async def test_get_controller_without_graphiti(self, monkeypatch):
        """Test getting controller when Graphiti is disabled."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "false")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        deps.get_retrieval_controller.cache_clear()
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings):
            await init_dependencies()
        
        controller = get_retrieval_controller()
        
        assert controller is not None
        assert controller.eligibility_service is not None
        assert controller.category_service is not None
        assert controller.embedding_service is not None
        assert controller.search_service is not None
        assert controller.ranking_service is not None
        assert controller.graphiti_service is None
        
        # Cleanup
        await shutdown_dependencies()
    
    @pytest.mark.asyncio
    async def test_get_controller_with_graphiti(self, monkeypatch):
        """Test getting controller when Graphiti is enabled."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "true")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        deps.get_retrieval_controller.cache_clear()
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings), \
             patch('graphiti_core.Graphiti') as mock_graphiti, \
             patch('graphiti_core.llm_client.OpenAIClient'):
            
            mock_graphiti_instance = MagicMock()
            mock_graphiti_instance.is_initialized = True
            mock_graphiti.return_value = mock_graphiti_instance
            
            await init_dependencies()
        
        controller = get_retrieval_controller()
        
        assert controller is not None
        assert controller.graphiti_service is not None
        
        # Cleanup
        await shutdown_dependencies()
    
    def test_get_controller_before_init_raises_error(self):
        """Test that getting controller before initialization raises error."""
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps.get_retrieval_controller.cache_clear()
        
        with pytest.raises(RuntimeError) as exc_info:
            get_retrieval_controller()
        
        assert "not initialized" in str(exc_info.value)


class TestDependenciesStatus:
    """Test dependencies status reporting."""
    
    @pytest.mark.asyncio
    async def test_status_before_initialization(self):
        """Test status before dependencies are initialized."""
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        
        status = get_dependencies_status()
        
        assert status["initialized"] is False
        assert status["repositories"]["graphiti"] is False
        assert status["stats"] == {}
    
    @pytest.mark.asyncio
    async def test_status_after_initialization(self, monkeypatch):
        """Test status after dependencies are initialized."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "false")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings):
            await init_dependencies()
        
        status = get_dependencies_status()
        
        assert status["initialized"] is True
        assert status["repositories"]["blocklist"] is True
        assert status["repositories"]["taxonomy"] is True
        assert status["repositories"]["vector"] is True
        assert status["repositories"]["campaign"] is True
        assert status["repositories"]["graphiti"] is False
        assert "blocklist_size" in status["stats"]
        
        # Cleanup
        await shutdown_dependencies()


class TestShutdownDependencies:
    """Test dependency shutdown."""
    
    @pytest.mark.asyncio
    async def test_shutdown_without_graphiti(self, monkeypatch):
        """Test shutdown when Graphiti is not initialized."""
        monkeypatch.setenv("GRAPHITI_ENABLED", "false")
        
        # Reset global state
        import src.core.dependencies as deps
        deps._repositories_initialized = False
        deps._graphiti_repo = None
        
        # Reload settings
        from src.core.config import Settings
        settings = Settings()
        
        with patch('src.core.dependencies.settings', settings):
            await init_dependencies()
        
        assert deps._repositories_initialized is True
        
        await shutdown_dependencies()
        
        assert deps._repositories_initialized is False
        assert deps._graphiti_repo is None
    
    @pytest.mark.asyncio
    async def test_shutdown_with_graphiti(self):
        """Test shutdown when Graphiti is initialized."""
        import src.core.dependencies as deps
        
        # Create a mock Graphiti repository
        mock_repo = MagicMock()
        mock_repo.is_initialized = True
        mock_repo.shutdown = AsyncMock()
        
        # Set it as the global Graphiti repo
        deps._graphiti_repo = mock_repo
        deps._repositories_initialized = True
        
        # Shutdown
        await shutdown_dependencies()
        
        # Verify shutdown was called
        mock_repo.shutdown.assert_called_once()
        assert deps._repositories_initialized is False
        assert deps._graphiti_repo is None
