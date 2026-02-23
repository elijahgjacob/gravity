"""Unit tests for SessionStateRepository."""

import time
from datetime import datetime, timedelta
import pytest
from src.repositories.session_state_repository import SessionStateRepository


class TestSessionStateRepository:
    """Test session state repository functionality."""
    
    def test_repository_initialization(self):
        """Test repository can be initialized."""
        repo = SessionStateRepository(ttl_minutes=30)
        assert repo.ttl == timedelta(minutes=30)
        assert repo.get_active_session_count() == 0
    
    def test_add_and_retrieve_queries(self):
        """Test adding and retrieving queries from session."""
        repo = SessionStateRepository()
        session_id = "test_session_1"
        
        # Add first query
        query1 = {
            'query': 'running shoes',
            'timestamp': datetime.now(),
            'eligibility': 0.75
        }
        repo.add_query(session_id, query1)
        
        # Add second query
        query2 = {
            'query': 'marathon training',
            'timestamp': datetime.now(),
            'eligibility': 0.80
        }
        repo.add_query(session_id, query2)
        
        # Retrieve queries
        queries = repo.get_session_queries(session_id)
        
        assert len(queries) == 2
        assert queries[0]['query'] == 'running shoes'
        assert queries[1]['query'] == 'marathon training'
    
    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session returns empty list."""
        repo = SessionStateRepository()
        queries = repo.get_session_queries("nonexistent_session")
        
        assert queries == []
    
    def test_multiple_sessions(self):
        """Test managing multiple sessions simultaneously."""
        repo = SessionStateRepository()
        
        # Add queries to session 1
        repo.add_query("session_1", {'query': 'query1', 'timestamp': datetime.now()})
        repo.add_query("session_1", {'query': 'query2', 'timestamp': datetime.now()})
        
        # Add queries to session 2
        repo.add_query("session_2", {'query': 'query3', 'timestamp': datetime.now()})
        
        # Verify sessions are separate
        session1_queries = repo.get_session_queries("session_1")
        session2_queries = repo.get_session_queries("session_2")
        
        assert len(session1_queries) == 2
        assert len(session2_queries) == 1
        assert repo.get_active_session_count() == 2
    
    def test_session_info(self):
        """Test retrieving session metadata."""
        repo = SessionStateRepository()
        session_id = "test_session"
        
        # Add queries
        repo.add_query(session_id, {'query': 'query1', 'timestamp': datetime.now()})
        repo.add_query(session_id, {'query': 'query2', 'timestamp': datetime.now()})
        
        # Get session info
        info = repo.get_session_info(session_id)
        
        assert info is not None
        assert info['session_id'] == session_id
        assert info['query_count'] == 2
        assert 'created_at' in info
        assert 'last_accessed' in info
        assert info['age_minutes'] >= 0
    
    def test_session_info_nonexistent(self):
        """Test getting info for non-existent session."""
        repo = SessionStateRepository()
        info = repo.get_session_info("nonexistent")
        
        assert info is None
    
    def test_session_ttl_expiration(self):
        """Test sessions expire after TTL."""
        repo = SessionStateRepository(ttl_minutes=0)  # Immediate expiration
        
        # Add query
        repo.add_query("test_session", {'query': 'test', 'timestamp': datetime.now()})
        
        # Manually set last_accessed to past
        with repo._lock:
            repo.sessions["test_session"]['last_accessed'] = datetime.now() - timedelta(minutes=1)
        
        # Cleanup
        removed = repo.cleanup_expired_sessions()
        
        assert removed == 1
        assert repo.get_active_session_count() == 0
    
    def test_cleanup_keeps_active_sessions(self):
        """Test cleanup doesn't remove active sessions."""
        repo = SessionStateRepository(ttl_minutes=30)
        
        # Add active session
        repo.add_query("active_session", {'query': 'test', 'timestamp': datetime.now()})
        
        # Cleanup
        removed = repo.cleanup_expired_sessions()
        
        assert removed == 0
        assert repo.get_active_session_count() == 1
    
    def test_clear_specific_session(self):
        """Test clearing a specific session."""
        repo = SessionStateRepository()
        
        repo.add_query("session_1", {'query': 'test1', 'timestamp': datetime.now()})
        repo.add_query("session_2", {'query': 'test2', 'timestamp': datetime.now()})
        
        # Clear session 1
        result = repo.clear_session("session_1")
        
        assert result is True
        assert repo.get_active_session_count() == 1
        assert repo.get_session_queries("session_1") == []
        assert len(repo.get_session_queries("session_2")) == 1
    
    def test_clear_nonexistent_session(self):
        """Test clearing non-existent session."""
        repo = SessionStateRepository()
        result = repo.clear_session("nonexistent")
        
        assert result is False
    
    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        repo = SessionStateRepository()
        
        repo.add_query("session_1", {'query': 'test1', 'timestamp': datetime.now()})
        repo.add_query("session_2", {'query': 'test2', 'timestamp': datetime.now()})
        repo.add_query("session_3", {'query': 'test3', 'timestamp': datetime.now()})
        
        count = repo.clear_all_sessions()
        
        assert count == 3
        assert repo.get_active_session_count() == 0
    
    def test_concurrent_session_access(self):
        """Test thread-safe concurrent access."""
        import threading
        
        repo = SessionStateRepository()
        session_id = "concurrent_test"
        
        def add_queries(start_idx):
            for i in range(start_idx, start_idx + 10):
                repo.add_query(session_id, {
                    'query': f'query_{i}',
                    'timestamp': datetime.now()
                })
        
        # Create multiple threads
        threads = [
            threading.Thread(target=add_queries, args=(i * 10,))
            for i in range(5)
        ]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify all queries were added
        queries = repo.get_session_queries(session_id)
        assert len(queries) == 50
    
    def test_session_query_ordering(self):
        """Test queries are returned in order added."""
        repo = SessionStateRepository()
        session_id = "order_test"
        
        # Add queries with slight delay
        for i in range(5):
            repo.add_query(session_id, {
                'query': f'query_{i}',
                'timestamp': datetime.now(),
                'order': i
            })
            time.sleep(0.01)
        
        queries = repo.get_session_queries(session_id)
        
        # Verify order preserved
        for i, query in enumerate(queries):
            assert query['order'] == i
    
    def test_session_with_optional_fields(self):
        """Test storing queries with optional fields."""
        repo = SessionStateRepository()
        session_id = "optional_test"
        
        # Add query with minimal fields
        repo.add_query(session_id, {
            'query': 'test query',
            'timestamp': datetime.now()
        })
        
        # Add query with all fields
        repo.add_query(session_id, {
            'query': 'detailed query',
            'timestamp': datetime.now(),
            'eligibility': 0.85,
            'categories': ['running_shoes', 'athletic_footwear'],
            'campaign_count': 1000
        })
        
        queries = repo.get_session_queries(session_id)
        
        assert len(queries) == 2
        assert 'eligibility' not in queries[0]
        assert queries[1]['eligibility'] == 0.85
        assert len(queries[1]['categories']) == 2
