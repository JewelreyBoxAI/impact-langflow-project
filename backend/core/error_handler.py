"""
Enhanced Error Handling and Logging System for AI/ML Pipeline Components
Provides comprehensive error tracking, logging, and recovery mechanisms
"""

import logging
import traceback
import functools
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import asyncio
from pathlib import Path

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    MODEL_INFERENCE = "model_inference"
    VECTOR_DB = "vector_db"
    MEMORY = "memory"
    FILE_UPLOAD = "file_upload"
    NETWORK = "network"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for errors"""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AIError:
    """Structured error information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: str
    context: ErrorContext
    traceback: Optional[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None

class ErrorTracker:
    """Track and analyze errors across the system"""

    def __init__(self, log_file: str = "errors.json"):
        self.log_file = Path(log_file)
        self.errors: List[AIError] = []
        self._load_errors()

    def _load_errors(self):
        """Load existing errors from file"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    # Convert dict back to AIError objects
                    for error_dict in data:
                        error = AIError(
                            error_id=error_dict['error_id'],
                            timestamp=datetime.fromisoformat(error_dict['timestamp']),
                            severity=ErrorSeverity(error_dict['severity']),
                            category=ErrorCategory(error_dict['category']),
                            message=error_dict['message'],
                            details=error_dict['details'],
                            context=ErrorContext(**error_dict['context']),
                            traceback=error_dict.get('traceback'),
                            resolved=error_dict.get('resolved', False),
                            resolution_notes=error_dict.get('resolution_notes')
                        )
                        self.errors.append(error)
        except Exception as e:
            logging.warning(f"Failed to load error history: {e}")

    def _save_errors(self):
        """Save errors to file"""
        try:
            error_dicts = []
            for error in self.errors:
                error_dict = {
                    'error_id': error.error_id,
                    'timestamp': error.timestamp.isoformat(),
                    'severity': error.severity.value,
                    'category': error.category.value,
                    'message': error.message,
                    'details': error.details,
                    'context': {
                        'component': error.context.component,
                        'operation': error.context.operation,
                        'user_id': error.context.user_id,
                        'session_id': error.context.session_id,
                        'request_id': error.context.request_id,
                        'metadata': error.context.metadata
                    },
                    'traceback': error.traceback,
                    'resolved': error.resolved,
                    'resolution_notes': error.resolution_notes
                }
                error_dicts.append(error_dict)

            with open(self.log_file, 'w') as f:
                json.dump(error_dicts, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save error history: {e}")

    def add_error(self, error: AIError):
        """Add a new error to tracking"""
        self.errors.append(error)
        # Keep only last 1000 errors to prevent file bloat
        if len(self.errors) > 1000:
            self.errors = self.errors[-1000:]
        self._save_errors()

    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e.timestamp > cutoff]

        stats = {
            'total_errors': len(recent_errors),
            'by_severity': {},
            'by_category': {},
            'by_component': {},
            'resolved_count': sum(1 for e in recent_errors if e.resolved),
            'time_range_hours': hours
        }

        for error in recent_errors:
            # By severity
            severity = error.severity.value
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

            # By category
            category = error.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            # By component
            component = error.context.component
            stats['by_component'][component] = stats['by_component'].get(component, 0) + 1

        return stats

class EnhancedLogger:
    """Enhanced logging with structured data and context"""

    def __init__(self, name: str, error_tracker: Optional[ErrorTracker] = None):
        self.logger = logging.getLogger(name)
        self.error_tracker = error_tracker or ErrorTracker()

    def log_error(self,
                  message: str,
                  severity: ErrorSeverity,
                  category: ErrorCategory,
                  context: ErrorContext,
                  exception: Optional[Exception] = None,
                  details: Optional[str] = None) -> str:
        """Log an error with full context and tracking"""

        import uuid
        error_id = str(uuid.uuid4())

        # Capture traceback if exception provided
        error_traceback = None
        if exception:
            error_traceback = traceback.format_exc()

        # Create structured error
        error = AIError(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            details=details or str(exception) if exception else "",
            context=context,
            traceback=error_traceback
        )

        # Add to tracking
        self.error_tracker.add_error(error)

        # Log to standard logger
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.ERROR)

        log_message = f"[{error_id}] {category.value.upper()}: {message}"
        if context.component:
            log_message += f" (Component: {context.component})"
        if context.operation:
            log_message += f" (Operation: {context.operation})"

        self.logger.log(log_level, log_message)

        if error_traceback:
            self.logger.debug(f"[{error_id}] Traceback: {error_traceback}")

        return error_id

    def log_success(self, message: str, context: ErrorContext, metrics: Optional[Dict[str, Any]] = None):
        """Log successful operations with metrics"""
        log_message = f"SUCCESS: {message}"
        if context.component:
            log_message += f" (Component: {context.component})"
        if metrics:
            log_message += f" (Metrics: {metrics})"

        self.logger.info(log_message)

def retry_with_backoff(max_retries: int = 3,
                      backoff_factor: float = 1.0,
                      exceptions: tuple = (Exception,),
                      logger: Optional[EnhancedLogger] = None):
    """Decorator for retry logic with exponential backoff"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Log final failure
                        if logger:
                            context = ErrorContext(
                                component=func.__module__,
                                operation=func.__name__,
                                metadata={'attempt': attempt + 1, 'max_retries': max_retries}
                            )
                            logger.log_error(
                                f"Function {func.__name__} failed after {max_retries + 1} attempts",
                                ErrorSeverity.HIGH,
                                ErrorCategory.UNKNOWN,
                                context,
                                e
                            )
                        raise

                    # Calculate backoff delay
                    delay = backoff_factor * (2 ** attempt)
                    if logger:
                        logger.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay}s: {e}")

                    await asyncio.sleep(delay)

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Log final failure
                        if logger:
                            context = ErrorContext(
                                component=func.__module__,
                                operation=func.__name__,
                                metadata={'attempt': attempt + 1, 'max_retries': max_retries}
                            )
                            logger.log_error(
                                f"Function {func.__name__} failed after {max_retries + 1} attempts",
                                ErrorSeverity.HIGH,
                                ErrorCategory.UNKNOWN,
                                context,
                                e
                            )
                        raise

                    # Calculate backoff delay
                    delay = backoff_factor * (2 ** attempt)
                    if logger:
                        logger.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay}s: {e}")

                    time.sleep(delay)

            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def circuit_breaker(failure_threshold: int = 5,
                   recovery_timeout: int = 60,
                   logger: Optional[EnhancedLogger] = None):
    """Circuit breaker pattern implementation"""

    def decorator(func: Callable) -> Callable:
        # Circuit state
        state = {'failures': 0, 'last_failure': None, 'open': False}

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check if circuit is open
            if state['open']:
                if (datetime.now() - state['last_failure']).seconds < recovery_timeout:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
                else:
                    # Attempt to close circuit
                    state['open'] = False
                    state['failures'] = 0
                    if logger:
                        logger.logger.info(f"Circuit breaker CLOSED for {func.__name__} - attempting recovery")

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Reset failure count on success
                state['failures'] = 0
                return result

            except Exception as e:
                state['failures'] += 1
                state['last_failure'] = datetime.now()

                if state['failures'] >= failure_threshold:
                    state['open'] = True
                    if logger:
                        context = ErrorContext(
                            component=func.__module__,
                            operation=func.__name__,
                            metadata={'failure_count': state['failures']}
                        )
                        logger.log_error(
                            f"Circuit breaker OPENED for {func.__name__} after {failure_threshold} failures",
                            ErrorSeverity.CRITICAL,
                            ErrorCategory.INTEGRATION,
                            context,
                            e
                        )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check if circuit is open
            if state['open']:
                if (datetime.now() - state['last_failure']).seconds < recovery_timeout:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
                else:
                    # Attempt to close circuit
                    state['open'] = False
                    state['failures'] = 0
                    if logger:
                        logger.logger.info(f"Circuit breaker CLOSED for {func.__name__} - attempting recovery")

            try:
                result = func(*args, **kwargs)
                # Reset failure count on success
                state['failures'] = 0
                return result

            except Exception as e:
                state['failures'] += 1
                state['last_failure'] = datetime.now()

                if state['failures'] >= failure_threshold:
                    state['open'] = True
                    if logger:
                        context = ErrorContext(
                            component=func.__module__,
                            operation=func.__name__,
                            metadata={'failure_count': state['failures']}
                        )
                        logger.log_error(
                            f"Circuit breaker OPENED for {func.__name__} after {failure_threshold} failures",
                            ErrorSeverity.CRITICAL,
                            ErrorCategory.INTEGRATION,
                            context,
                            e
                        )

                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

class PerformanceMonitor:
    """Monitor performance metrics and detect anomalies"""

    def __init__(self, logger: Optional[EnhancedLogger] = None):
        self.logger = logger
        self.metrics: Dict[str, List[float]] = {}

    def measure_time(self, operation_name: str):
        """Context manager for measuring execution time"""
        return self.TimeTracker(operation_name, self)

    class TimeTracker:
        def __init__(self, operation_name: str, monitor: 'PerformanceMonitor'):
            self.operation_name = operation_name
            self.monitor = monitor
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            self.monitor.record_metric(self.operation_name, duration)

            # Log performance warning if operation is slow
            if duration > 10.0:  # 10 seconds threshold
                if self.monitor.logger:
                    context = ErrorContext(
                        component="performance_monitor",
                        operation=self.operation_name,
                        metadata={'duration': duration}
                    )
                    self.monitor.logger.log_error(
                        f"Slow operation detected: {self.operation_name} took {duration:.2f}s",
                        ErrorSeverity.MEDIUM,
                        ErrorCategory.TIMEOUT,
                        context
                    )

    def record_metric(self, metric_name: str, value: float):
        """Record a performance metric"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append(value)

        # Keep only last 100 measurements per metric
        if len(self.metrics[metric_name]) > 100:
            self.metrics[metric_name] = self.metrics[metric_name][-100:]

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics"""
        summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'recent': values[-1] if values else 0
                }

        return summary

# Global instances
error_tracker = ErrorTracker()
enhanced_logger = EnhancedLogger("ai_pipeline", error_tracker)
performance_monitor = PerformanceMonitor(enhanced_logger)

def get_error_handler() -> EnhancedLogger:
    """Get the global error handler instance"""
    return enhanced_logger

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor

def get_error_stats() -> Dict[str, Any]:
    """Get current error statistics"""
    return error_tracker.get_error_stats()

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Test error handling
    context = ErrorContext(
        component="test_component",
        operation="test_operation",
        user_id="test_user"
    )

    enhanced_logger.log_error(
        "Test error message",
        ErrorSeverity.MEDIUM,
        ErrorCategory.VALIDATION,
        context,
        details="This is a test error for demonstration"
    )

    # Test performance monitoring
    with performance_monitor.measure_time("test_operation"):
        time.sleep(0.1)  # Simulate work

    print("Error stats:", get_error_stats())
    print("Performance metrics:", performance_monitor.get_metrics_summary())