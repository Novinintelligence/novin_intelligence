import time
import psutil
import threading
import logging
from typing import Dict, Any, Optional
from .config import SecurityConfig
from .error_handling import MemoryError

class PerformanceMonitor:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.start_time = time.time()
        self.process = psutil.Process()
        self.request_times: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger("NovinAI.Performance")
        
        # Initialize metrics
        self.metrics = {
            "requests_processed": 0,
            "errors": 0,
            "avg_processing_time": 0.0,
            "peak_memory_mb": 0.0,
            "initialization_time": 0.0
        }
    
    def start_request(self, request_id: str) -> None:
        """Records the start time of a request."""
        with self.lock:
            self.request_times[request_id] = time.time()
    
    def end_request(self, request_id: str, success: bool = True) -> Optional[float]:
        """
        Records the end of a request and updates metrics.
        Returns the processing time in seconds.
        """
        with self.lock:
            if request_id not in self.request_times:
                return None
            
            start_time = self.request_times.pop(request_id)
            processing_time = time.time() - start_time
            
            # Update metrics
            self.metrics["requests_processed"] += 1
            if not success:
                self.metrics["errors"] += 1
            
            # Update average processing time
            total_time = (self.metrics["avg_processing_time"] * 
                         (self.metrics["requests_processed"] - 1) + 
                         processing_time)
            self.metrics["avg_processing_time"] = (
                total_time / self.metrics["requests_processed"]
            )
            
            return processing_time
    
    def check_memory(self) -> None:
        """
        Checks current memory usage against limits.
        Raises MemoryError if limits are exceeded.
        """
        current_mb = self.process.memory_info().rss / 1024 / 1024
        self.metrics["peak_memory_mb"] = max(
            self.metrics["peak_memory_mb"], 
            current_mb
        )
        
        if current_mb > self.config.max_memory_mb:
            raise MemoryError(
                current_mb=current_mb,
                max_mb=self.config.max_memory_mb
            )
        
        # Log warning if approaching limit
        if current_mb > self.config.gc_threshold_mb:
            self.logger.warning(
                f"Memory usage ({current_mb:.1f}MB) approaching limit "
                f"({self.config.max_memory_mb}MB)"
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Returns current performance metrics."""
        with self.lock:
            current_mb = self.process.memory_info().rss / 1024 / 1024
            uptime = time.time() - self.start_time
            
            return {
                **self.metrics,
                "current_memory_mb": current_mb,
                "uptime_seconds": uptime,
                "requests_per_second": (
                    self.metrics["requests_processed"] / uptime if uptime > 0 else 0
                ),
                "error_rate": (
                    self.metrics["errors"] / self.metrics["requests_processed"]
                    if self.metrics["requests_processed"] > 0 else 0
                ),
                "current_requests": len(self.request_times)
            }
    
    def log_metrics(self) -> None:
        """Logs current performance metrics."""
        metrics = self.get_metrics()
        self.logger.info(
            "Performance Metrics: "
            f"Requests: {metrics['requests_processed']}, "
            f"Avg Time: {metrics['avg_processing_time']*1000:.1f}ms, "
            f"Memory: {metrics['current_memory_mb']:.1f}MB, "
            f"Error Rate: {metrics['error_rate']*100:.1f}%"
        )
