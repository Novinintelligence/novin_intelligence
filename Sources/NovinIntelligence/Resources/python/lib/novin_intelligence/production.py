"""
Production-ready enhancements for the NovinAI system.
This module provides monitoring, error handling, and performance optimization.
"""

import time
import logging
import threading
import json
from typing import Dict, Any, Optional, Callable
from functools import wraps

from .config import SecurityConfig
from .error_handling import NovinAIError, ProcessingError, ValidationError
from .performance import PerformanceMonitor
from .rate_limiter import RateLimiter

class ProductionManager:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.performance = PerformanceMonitor(config)
        self.rate_limiter = RateLimiter(config)
        self.logger = logging.getLogger("NovinAI.Production")
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configures production-grade logging."""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            'novin_ai.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            'novin_ai_errors.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def wrap_request(self, func: Callable) -> Callable:
        """
        Decorator to wrap request processing with production enhancements.
        Adds:
        - Rate limiting
        - Performance monitoring
        - Error handling
        - Logging
        - Memory checks
        """
        @wraps(func)
        def wrapper(request_json: str, client_id: str, *args, **kwargs) -> str:
            request_id = f"{client_id}:{time.time()}"
            
            try:
                # Start monitoring
                self.performance.start_request(request_id)
                self.logger.info(f"Processing request {request_id}")
                
                # Check rate limits
                self.rate_limiter.check_rate_limit(client_id, request_id)
                
                # Check memory
                self.performance.check_memory()
                
                # Validate JSON
                try:
                    json.loads(request_json)
                except json.JSONDecodeError as e:
                    raise ValidationError(
                        message="Invalid JSON format",
                        fields={"json_error": str(e)}
                    )
                
                # Process request
                result = func(request_json, client_id, *args, **kwargs)
                
                # Record success
                self.performance.end_request(request_id, success=True)
                self.rate_limiter.complete_request(client_id, request_id)
                
                return result
                
            except NovinAIError as e:
                # Handle known errors
                self.logger.warning(
                    f"Request {request_id} failed: {e.code} - {e.message}"
                )
                self.performance.end_request(request_id, success=False)
                
                return json.dumps({
                    "requestId": request_id,
                    "clientId": client_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                    **e.to_dict()
                })
                
            except Exception as e:
                # Handle unexpected errors
                self.logger.error(
                    f"Unexpected error processing request {request_id}",
                    exc_info=True
                )
                self.performance.end_request(request_id, success=False)
                
                error = ProcessingError(
                    message="Internal processing error",
                    original_error=e
                )
                return json.dumps({
                    "requestId": request_id,
                    "clientId": client_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                    **error.to_dict()
                })
            
            finally:
                # Log metrics periodically
                if self.performance.metrics["requests_processed"] % 100 == 0:
                    self.performance.log_metrics()
        
        return wrapper
    
    def get_health_check(self) -> Dict[str, Any]:
        """Returns comprehensive health check data."""
        return {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            "metrics": {
                "performance": self.performance.get_metrics(),
                "rate_limiting": self.rate_limiter.get_metrics("global")
            }
        }
    
    def monitor_memory(self) -> None:
        """
        Starts a background thread to monitor memory usage.
        Logs warnings when approaching limits.
        """
        def _monitor():
            while True:
                try:
                    self.performance.check_memory()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error("Memory monitoring failed", exc_info=True)
        
        thread = threading.Thread(
            target=_monitor,
            name="memory_monitor",
            daemon=True
        )
        thread.start()