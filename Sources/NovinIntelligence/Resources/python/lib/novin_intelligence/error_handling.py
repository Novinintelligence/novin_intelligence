from typing import Dict, Any, Optional
import json
import time
from dataclasses import dataclass

@dataclass
class NovinAIError(Exception):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "errorCode": self.code,
            "message": self.message,
            "details": self.details or {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class ValidationError(NovinAIError):
    def __init__(self, message: str, fields: Dict[str, str]):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details={"validation_errors": fields}
        )

class RateLimitError(NovinAIError):
    def __init__(self, window_seconds: int, max_requests: int):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds",
            details={
                "window_seconds": window_seconds,
                "max_requests": max_requests,
                "retry_after": window_seconds
            }
        )

class ProcessingError(NovinAIError):
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {"original_error": str(original_error)} if original_error else None
        super().__init__(
            code="PROCESSING_ERROR",
            message=message,
            details=details
        )

class InitializationError(NovinAIError):
    def __init__(self, message: str, component: str):
        super().__init__(
            code="INITIALIZATION_ERROR",
            message=message,
            details={"component": component}
        )

class MemoryError(NovinAIError):
    def __init__(self, current_mb: float, max_mb: float):
        super().__init__(
            code="MEMORY_LIMIT_EXCEEDED",
            message=f"Memory usage ({current_mb:.1f}MB) exceeds limit ({max_mb:.1f}MB)",
            details={
                "current_mb": current_mb,
                "max_mb": max_mb
            }
        )
