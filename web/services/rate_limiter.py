"""
Rate Limiting Service
Prevents brute force attacks and API abuse.
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int = 100  # Maximum requests allowed
    window_seconds: int = 60  # Time window in seconds
    block_seconds: int = 300  # Block duration after limit exceeded


@dataclass
class RequestRecord:
    """Record of requests from a client"""
    timestamps: list = field(default_factory=list)
    blocked_until: Optional[float] = None


class RateLimiter:
    """
    In-memory rate limiter.
    For production, consider using Redis for distributed rate limiting.
    """
    
    # Default configurations for different endpoints
    CONFIGS = {
        "default": RateLimitConfig(max_requests=100, window_seconds=60),
        "auth": RateLimitConfig(max_requests=5, window_seconds=60, block_seconds=600),
        "api": RateLimitConfig(max_requests=60, window_seconds=60),
        "analysis": RateLimitConfig(max_requests=10, window_seconds=60),
    }
    
    def __init__(self):
        self._records: Dict[str, Dict[str, RequestRecord]] = defaultdict(lambda: defaultdict(RequestRecord))
        self._lock = Lock()
    
    def _get_config(self, endpoint_type: str) -> RateLimitConfig:
        """Get rate limit config for endpoint type"""
        return self.CONFIGS.get(endpoint_type, self.CONFIGS["default"])
    
    def _clean_old_timestamps(self, record: RequestRecord, window_seconds: int) -> None:
        """Remove timestamps outside the current window"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        record.timestamps = [ts for ts in record.timestamps if ts > cutoff]
    
    def is_allowed(self, client_id: str, endpoint_type: str = "default") -> bool:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Unique identifier for client (IP, user ID, etc.)
            endpoint_type: Type of endpoint for different limits
            
        Returns:
            True if request is allowed, False if rate limited
        """
        config = self._get_config(endpoint_type)
        current_time = time.time()
        
        with self._lock:
            record = self._records[endpoint_type][client_id]
            
            # Check if client is blocked
            if record.blocked_until and current_time < record.blocked_until:
                return False
            elif record.blocked_until:
                # Unblock if time has passed
                record.blocked_until = None
                record.timestamps = []
            
            # Clean old timestamps
            self._clean_old_timestamps(record, config.window_seconds)
            
            # Check if limit exceeded
            if len(record.timestamps) >= config.max_requests:
                # Block the client
                record.blocked_until = current_time + config.block_seconds
                logger.warning(f"Rate limit exceeded for {client_id} on {endpoint_type}")
                return False
            
            # Record this request
            record.timestamps.append(current_time)
            return True
    
    def get_remaining(self, client_id: str, endpoint_type: str = "default") -> int:
        """Get remaining requests for client"""
        config = self._get_config(endpoint_type)
        
        with self._lock:
            record = self._records[endpoint_type][client_id]
            self._clean_old_timestamps(record, config.window_seconds)
            return max(0, config.max_requests - len(record.timestamps))
    
    def get_reset_time(self, client_id: str, endpoint_type: str = "default") -> int:
        """Get seconds until rate limit resets"""
        config = self._get_config(endpoint_type)
        
        with self._lock:
            record = self._records[endpoint_type][client_id]
            
            if record.blocked_until:
                return int(record.blocked_until - time.time())
            
            if not record.timestamps:
                return 0
            
            oldest = min(record.timestamps)
            return int(oldest + config.window_seconds - time.time())
    
    def reset(self, client_id: str, endpoint_type: Optional[str] = None) -> None:
        """Reset rate limit for client"""
        with self._lock:
            if endpoint_type:
                if client_id in self._records[endpoint_type]:
                    del self._records[endpoint_type][client_id]
            else:
                for ep_type in self._records:
                    if client_id in self._records[ep_type]:
                        del self._records[ep_type][client_id]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_rate_limit(client_id: str, endpoint_type: str = "default") -> bool:
    """Convenience function to check rate limit"""
    return get_rate_limiter().is_allowed(client_id, endpoint_type)
