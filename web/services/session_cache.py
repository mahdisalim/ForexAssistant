"""
Session Cache Service
Persistent session storage to maintain user sessions across server restarts.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)


class SessionCache:
    """
    Persistent session cache that survives server restarts.
    Stores session data in a JSON file.
    """
    
    SESSION_EXPIRY_DAYS = 30  # Sessions expire after 30 days
    
    def __init__(self, cache_file: str = "data/sessions.json"):
        self.cache_file = Path(cache_file)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ensure_file_exists()
        self._load_sessions()
        self._cleanup_expired()
    
    def _ensure_file_exists(self):
        """Ensure cache directory and file exist"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.cache_file.exists():
            with open(self.cache_file, 'w') as f:
                json.dump({}, f)
    
    def _load_sessions(self):
        """Load sessions from file"""
        try:
            with open(self.cache_file, 'r') as f:
                self._sessions = json.load(f)
            logger.info(f"Loaded {len(self._sessions)} sessions from cache")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self._sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = []
        
        for token, session in self._sessions.items():
            expires_at = session.get("expires_at")
            if expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at)
                    if now > expiry:
                        expired.append(token)
                except:
                    pass
        
        if expired:
            for token in expired:
                del self._sessions[token]
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def create_session(self, token: str, user_email: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session for a user.
        
        Args:
            token: Authentication token
            user_email: User's email
            user_data: Additional user data to store
            
        Returns:
            Session data
        """
        with self._lock:
            expires_at = datetime.now() + timedelta(days=self.SESSION_EXPIRY_DAYS)
            
            session = {
                "user_email": user_email,
                "user_data": user_data,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            self._sessions[token] = session
            self._save_sessions()
            
            logger.info(f"Created session for user: {user_email}")
            return session
    
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get session by token.
        
        Args:
            token: Authentication token
            
        Returns:
            Session data or None if not found/expired
        """
        with self._lock:
            session = self._sessions.get(token)
            
            if not session:
                return None
            
            # Check expiry
            expires_at = session.get("expires_at")
            if expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at)
                    if datetime.now() > expiry:
                        del self._sessions[token]
                        self._save_sessions()
                        return None
                except:
                    pass
            
            # Update last activity
            session["last_activity"] = datetime.now().isoformat()
            self._save_sessions()
            
            return session
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by token.
        
        Args:
            token: Authentication token
            
        Returns:
            User data or None
        """
        session = self.get_session(token)
        if session:
            return {
                "email": session.get("user_email"),
                **session.get("user_data", {})
            }
        return None
    
    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate/delete a session.
        
        Args:
            token: Authentication token
            
        Returns:
            True if session was found and deleted
        """
        with self._lock:
            if token in self._sessions:
                del self._sessions[token]
                self._save_sessions()
                return True
            return False
    
    def invalidate_user_sessions(self, user_email: str) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_email: User's email
            
        Returns:
            Number of sessions invalidated
        """
        with self._lock:
            tokens_to_remove = [
                token for token, session in self._sessions.items()
                if session.get("user_email") == user_email
            ]
            
            for token in tokens_to_remove:
                del self._sessions[token]
            
            if tokens_to_remove:
                self._save_sessions()
            
            return len(tokens_to_remove)
    
    def extend_session(self, token: str, days: int = None) -> bool:
        """
        Extend session expiry.
        
        Args:
            token: Authentication token
            days: Number of days to extend (default: SESSION_EXPIRY_DAYS)
            
        Returns:
            True if session was found and extended
        """
        if days is None:
            days = self.SESSION_EXPIRY_DAYS
        
        with self._lock:
            if token in self._sessions:
                new_expiry = datetime.now() + timedelta(days=days)
                self._sessions[token]["expires_at"] = new_expiry.isoformat()
                self._save_sessions()
                return True
            return False
    
    def get_active_sessions_count(self) -> int:
        """Get count of active (non-expired) sessions"""
        self._cleanup_expired()
        return len(self._sessions)


# Global session cache instance
_session_cache: Optional[SessionCache] = None


def get_session_cache() -> SessionCache:
    """Get or create the global session cache instance"""
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCache()
    return _session_cache
