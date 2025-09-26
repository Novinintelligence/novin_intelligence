from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SecurityConfig:
    # Rate limiting settings
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 60     # seconds
    burst_allowance: int = 20       # concurrent requests
    
    # Memory management
    max_memory_mb: int = 50
    gc_threshold_mb: int = 40
    
    # Performance thresholds
    max_processing_time: float = 0.1  # seconds
    initialization_timeout: float = 1.0  # seconds
    
    # Error handling
    max_retries: int = 3
    retry_delay: float = 0.1  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rate_limiting": {
                "requests_per_window": self.rate_limit_requests,
                "window_seconds": self.rate_limit_window,
                "burst_allowance": self.burst_allowance
            },
            "memory": {
                "max_mb": self.max_memory_mb,
                "gc_threshold_mb": self.gc_threshold_mb
            },
            "performance": {
                "max_processing_time": self.max_processing_time,
                "initialization_timeout": self.initialization_timeout
            },
            "error_handling": {
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay
            }
        }
