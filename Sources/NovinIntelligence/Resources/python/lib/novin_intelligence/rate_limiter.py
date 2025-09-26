import time
from typing import Dict, Set
import threading
from collections import deque
from .config import SecurityConfig
from .error_handling import RateLimitError

class RateLimiter:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests: Dict[str, deque] = {}  # client_id -> timestamps
        self.active_requests: Dict[str, Set[str]] = {}  # client_id -> request_ids
        self.lock = threading.Lock()
    
    def check_rate_limit(self, client_id: str, request_id: str) -> None:
        """
        Checks if the request is allowed under current rate limits.
        Raises RateLimitError if limits are exceeded.
        """
        with self.lock:
            now = time.time()
            
            # Initialize if first request from this client
            if client_id not in self.requests:
                self.requests[client_id] = deque()
                self.active_requests[client_id] = set()
            
            # Clean up old requests
            while (self.requests[client_id] and 
                   self.requests[client_id][0] < now - self.config.rate_limit_window):
                self.requests[client_id].popleft()
            
            # Check request count in window
            if len(self.requests[client_id]) >= self.config.rate_limit_requests:
                raise RateLimitError(
                    window_seconds=self.config.rate_limit_window,
                    max_requests=self.config.rate_limit_requests
                )
            
            # Check concurrent requests (burst)
            if len(self.active_requests[client_id]) >= self.config.burst_allowance:
                raise RateLimitError(
                    window_seconds=1,  # Burst window is 1 second
                    max_requests=self.config.burst_allowance
                )
            
            # Record the request
            self.requests[client_id].append(now)
            self.active_requests[client_id].add(request_id)
    
    def complete_request(self, client_id: str, request_id: str) -> None:
        """Marks a request as completed, freeing up the burst allowance."""
        with self.lock:
            if client_id in self.active_requests:
                self.active_requests[client_id].discard(request_id)
    
    def get_metrics(self, client_id: str) -> Dict[str, int]:
        """Returns current rate limiting metrics for a client."""
        with self.lock:
            if client_id not in self.requests:
                return {
                    "requests_in_window": 0,
                    "active_requests": 0,
                    "remaining_requests": self.config.rate_limit_requests,
                    "remaining_burst": self.config.burst_allowance
                }
            
            now = time.time()
            # Clean up old requests first
            while (self.requests[client_id] and 
                   self.requests[client_id][0] < now - self.config.rate_limit_window):
                self.requests[client_id].popleft()
            
            return {
                "requests_in_window": len(self.requests[client_id]),
                "active_requests": len(self.active_requests[client_id]),
                "remaining_requests": self.config.rate_limit_requests - len(self.requests[client_id]),
                "remaining_burst": self.config.burst_allowance - len(self.active_requests[client_id])
            }
