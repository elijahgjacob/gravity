"""Repository for managing session state in-memory."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class SessionStateRepository:
    """
    Track session state in-memory with TTL.
    
    Provides fast, thread-safe access to session query history
    for conversational context tracking.
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize the session state repository.
        
        Args:
            ttl_minutes: Time-to-live for sessions in minutes (default: 30)
        """
        self.sessions: Dict[str, Dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self._lock = Lock()
        
        logger.info(f"SessionStateRepository initialized with TTL: {ttl_minutes} minutes")
    
    def add_query(self, session_id: str, query_data: Dict) -> None:
        """
        Add a query to session history.
        
        Args:
            session_id: Session identifier
            query_data: Query data dictionary containing:
                - query: str (query text)
                - timestamp: datetime
                - eligibility: float (optional)
                - categories: List[str] (optional)
        """
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'queries': [],
                    'created_at': datetime.now(),
                    'last_accessed': datetime.now()
                }
                logger.debug(f"Created new session: {session_id}")
            
            session = self.sessions[session_id]
            session['queries'].append(query_data)
            session['last_accessed'] = datetime.now()
            
            logger.debug(
                f"Added query to session {session_id}: "
                f"{query_data.get('query', '')[:50]}... "
                f"(total queries: {len(session['queries'])})"
            )
    
    def get_session_queries(self, session_id: str) -> List[Dict]:
        """
        Get all queries in a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of query data dictionaries, ordered by timestamp
        """
        with self._lock:
            if session_id not in self.sessions:
                logger.debug(f"Session not found: {session_id}")
                return []
            
            session = self.sessions[session_id]
            session['last_accessed'] = datetime.now()
            
            queries = session['queries'].copy()
            logger.debug(f"Retrieved {len(queries)} queries from session {session_id}")
            
            return queries
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session info dict or None if session doesn't exist
        """
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            return {
                'session_id': session_id,
                'query_count': len(session['queries']),
                'created_at': session['created_at'],
                'last_accessed': session['last_accessed'],
                'age_minutes': (datetime.now() - session['created_at']).total_seconds() / 60
            }
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions older than TTL.
        
        Returns:
            Number of sessions removed
        """
        with self._lock:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                age = now - session['last_accessed']
                if age > self.ttl:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self._lock:
            return len(self.sessions)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a specific session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was found and cleared, False otherwise
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"Cleared session: {session_id}")
                return True
            return False
    
    def clear_all_sessions(self) -> int:
        """
        Clear all sessions.
        
        Returns:
            Number of sessions cleared
        """
        with self._lock:
            count = len(self.sessions)
            self.sessions.clear()
            logger.info(f"Cleared all {count} sessions")
            return count
