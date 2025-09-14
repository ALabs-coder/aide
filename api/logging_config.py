#!/usr/bin/env python3
"""
Structured logging configuration for AWS Lambda and CloudWatch
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from config import settings
import uuid

class CloudWatchFormatter(logging.Formatter):
    """Custom formatter for CloudWatch logs with structured JSON output"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON for CloudWatch
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'file_hash'):
            log_entry["file_hash"] = record.file_hash
        
        if hasattr(record, 'processing_time'):
            log_entry["processing_time_ms"] = record.processing_time
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 
                          'relativeCreated', 'thread', 'threadName', 'processName', 
                          'process', 'message', 'exc_info', 'exc_text', 'stack_info',
                          'request_id', 'user_id', 'file_hash', 'processing_time'}:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.user_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context information to log record
        
        Args:
            record: Log record to modify
            
        Returns:
            True to allow record through
        """
        # Add context if available
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        
        return True
    
    def set_context(self, request_id: Optional[str] = None, user_id: Optional[str] = None):
        """Set context for logging"""
        if request_id:
            self.request_id = request_id
        if user_id:
            self.user_id = user_id

# Global context filter instance
context_filter = ContextFilter()

def setup_logging():
    """
    Configure logging for Lambda environment
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Set log level from config
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create CloudWatch handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set custom formatter
    formatter = CloudWatchFormatter()
    handler.setFormatter(formatter)
    
    # Add context filter
    handler.addFilter(context_filter)
    
    # Add handler to root logger
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    
    # Set our application logger
    app_logger = logging.getLogger(__name__.split('.')[0])
    app_logger.setLevel(log_level)

class LoggerMixin:
    """Mixin class to add structured logging capabilities"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with extra context"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with extra context"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with extra context"""
        self.logger.error(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with extra context"""
        self.logger.debug(message, extra=kwargs)

def log_performance(func):
    """
    Decorator to log function performance
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with performance logging
    """
    import time
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "processing_time": duration,
                    "status": "success"
                }
            )
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "processing_time": duration,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "processing_time": duration,
                    "status": "success"
                }
            )
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "processing_time": duration,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
    
    # Return appropriate wrapper based on whether function is async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.security")
    
    def log_auth_success(self, user_id: str, method: str, **kwargs):
        """Log successful authentication"""
        self.logger.info(
            "Authentication successful",
            extra={
                "event_type": "auth_success",
                "user_id": user_id,
                "auth_method": method,
                **kwargs
            }
        )
    
    def log_auth_failure(self, reason: str, method: str, **kwargs):
        """Log authentication failure"""
        self.logger.warning(
            "Authentication failed",
            extra={
                "event_type": "auth_failure",
                "reason": reason,
                "auth_method": method,
                **kwargs
            }
        )
    
    def log_rate_limit_exceeded(self, user_id: str, **kwargs):
        """Log rate limit violation"""
        self.logger.warning(
            "Rate limit exceeded",
            extra={
                "event_type": "rate_limit_exceeded",
                "user_id": user_id,
                **kwargs
            }
        )
    
    def log_suspicious_activity(self, description: str, **kwargs):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity detected: {description}",
            extra={
                "event_type": "suspicious_activity",
                "description": description,
                **kwargs
            }
        )
    
    def log_file_validation_failure(self, filename: str, reason: str, **kwargs):
        """Log file validation failure"""
        self.logger.warning(
            "File validation failed",
            extra={
                "event_type": "file_validation_failure",
                "filename": filename,
                "reason": reason,
                **kwargs
            }
        )

# Global security logger instance
security_logger = SecurityLogger()

# Utility functions for common logging patterns
def set_request_context(request_id: str, user_id: Optional[str] = None):
    """Set request context for logging"""
    context_filter.set_context(request_id=request_id, user_id=user_id)

def generate_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())

def log_api_request(method: str, path: str, user_id: Optional[str] = None, **kwargs):
    """Log API request"""
    logger = logging.getLogger(__name__)
    logger.info(
        f"API request: {method} {path}",
        extra={
            "event_type": "api_request",
            "http_method": method,
            "path": path,
            "user_id": user_id,
            **kwargs
        }
    )

def log_api_response(status_code: int, processing_time: float, **kwargs):
    """Log API response"""
    logger = logging.getLogger(__name__)
    logger.info(
        f"API response: {status_code}",
        extra={
            "event_type": "api_response",
            "status_code": status_code,
            "processing_time": processing_time,
            **kwargs
        }
    )

# Initialize logging when module is imported
setup_logging()