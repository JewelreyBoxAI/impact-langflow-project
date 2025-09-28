"""
Production Readiness Module for AI/ML Pipeline Components
Comprehensive production optimizations, monitoring, and deployment features
"""

import asyncio
import psutil
import threading
import time
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
import gc
import sys
import os

from .config_manager import get_config
from .error_handler import get_error_handler, ErrorSeverity, ErrorCategory, ErrorContext

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: float

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: datetime
    requests_per_minute: int
    active_connections: int
    cache_hit_rate: float
    error_rate: float
    avg_response_time: float
    database_connections: int
    queue_size: int

class ResourceMonitor:
    """Monitor system and application resources"""

    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.system_metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[ApplicationMetrics] = []
        self.start_time = time.time()
        self.request_counter = 0
        self.response_times: List[float] = []
        self.active_connections = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self._monitoring = False
        self._monitor_thread = None

    def start_monitoring(self):
        """Start resource monitoring in background thread"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)

                # Collect application metrics
                app_metrics = self._collect_app_metrics()
                self.app_metrics_history.append(app_metrics)

                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.system_metrics_history = [
                    m for m in self.system_metrics_history if m.timestamp > cutoff_time
                ]
                self.app_metrics_history = [
                    m for m in self.app_metrics_history if m.timestamp > cutoff_time
                ]

                # Check for alerts
                self._check_alerts(system_metrics, app_metrics)

                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                process_count=len(psutil.pids()),
                uptime_seconds=time.time() - self.start_time
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                memory_available_mb=0,
                disk_usage_percent=0,
                network_io={},
                process_count=0,
                uptime_seconds=time.time() - self.start_time
            )

    def _collect_app_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        # Calculate requests per minute
        rpm = self.request_counter  # Will be reset every minute
        self.request_counter = 0

        # Calculate average response time
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            self.response_times = []  # Reset for next period

        # Calculate cache hit rate
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests) if total_cache_requests > 0 else 0

        return ApplicationMetrics(
            timestamp=datetime.now(),
            requests_per_minute=rpm,
            active_connections=self.active_connections,
            cache_hit_rate=cache_hit_rate,
            error_rate=0,  # Will be calculated from error tracker
            avg_response_time=avg_response_time,
            database_connections=0,  # Placeholder for DB monitoring
            queue_size=0  # Placeholder for queue monitoring
        )

    def _check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check for alert conditions"""
        error_handler = get_error_handler()

        # High CPU usage alert
        if system_metrics.cpu_percent > 80:
            error_handler.log_error(
                f"High CPU usage detected: {system_metrics.cpu_percent}%",
                ErrorSeverity.MEDIUM,
                ErrorCategory.UNKNOWN,
                ErrorContext(component="resource_monitor", operation="cpu_check")
            )

        # High memory usage alert
        if system_metrics.memory_percent > 85:
            error_handler.log_error(
                f"High memory usage detected: {system_metrics.memory_percent}%",
                ErrorSeverity.HIGH,
                ErrorCategory.UNKNOWN,
                ErrorContext(component="resource_monitor", operation="memory_check")
            )

        # Low disk space alert
        if system_metrics.disk_usage_percent > 90:
            error_handler.log_error(
                f"Low disk space: {system_metrics.disk_usage_percent}% used",
                ErrorSeverity.HIGH,
                ErrorCategory.UNKNOWN,
                ErrorContext(component="resource_monitor", operation="disk_check")
            )

    def record_request(self):
        """Record a new request"""
        self.request_counter += 1

    def record_response_time(self, response_time: float):
        """Record response time for a request"""
        self.response_times.append(response_time)

    def increment_active_connections(self):
        """Increment active connection count"""
        self.active_connections += 1

    def decrement_active_connections(self):
        """Decrement active connection count"""
        self.active_connections = max(0, self.active_connections - 1)

    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics"""
        latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None

        return {
            "system": latest_system.__dict__ if latest_system else {},
            "application": latest_app.__dict__ if latest_app else {},
            "monitoring_active": self._monitoring
        }

class CacheManager:
    """Intelligent caching with TTL and memory management"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.resource_monitor = None

    def set_resource_monitor(self, monitor: ResourceMonitor):
        """Set resource monitor for cache hit/miss tracking"""
        self.resource_monitor = monitor

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            if self.resource_monitor:
                self.resource_monitor.record_cache_miss()
            return None

        entry = self.cache[key]
        if self._is_expired(entry):
            del self.cache[key]
            del self.access_times[key]
            if self.resource_monitor:
                self.resource_monitor.record_cache_miss()
            return None

        self.access_times[key] = time.time()
        if self.resource_monitor:
            self.resource_monitor.record_cache_hit()
        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        self.access_times[key] = time.time()

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry['expires_at']

    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        del self.cache[lru_key]
        del self.access_times[lru_key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if self._is_expired(entry))

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "memory_usage_mb": sys.getsizeof(self.cache) / 1024 / 1024,
            "hit_rate": getattr(self.resource_monitor, 'cache_hits', 0) /
                       max(1, getattr(self.resource_monitor, 'cache_hits', 0) +
                           getattr(self.resource_monitor, 'cache_misses', 0))
        }

class ConnectionPool:
    """Connection pool for database and external API connections"""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 30):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.active_connections: Dict[str, Any] = {}
        self.available_connections: List[Any] = []
        self.wait_queue: List[Any] = []
        self._lock = threading.Lock()

    async def get_connection(self, connection_id: str = None) -> Any:
        """Get a connection from the pool"""
        with self._lock:
            if self.available_connections:
                connection = self.available_connections.pop()
                if connection_id:
                    self.active_connections[connection_id] = connection
                return connection

            if len(self.active_connections) < self.max_connections:
                # Create new connection (placeholder)
                connection = {"id": f"conn_{len(self.active_connections)}", "created_at": time.time()}
                if connection_id:
                    self.active_connections[connection_id] = connection
                return connection

            # Pool is full, wait for available connection
            return None

    def return_connection(self, connection: Any, connection_id: str = None) -> None:
        """Return a connection to the pool"""
        with self._lock:
            if connection_id and connection_id in self.active_connections:
                del self.active_connections[connection_id]

            if len(self.available_connections) < self.max_connections:
                self.available_connections.append(connection)

    def get_pool_stats(self) -> Dict[str, int]:
        """Get connection pool statistics"""
        with self._lock:
            return {
                "active_connections": len(self.active_connections),
                "available_connections": len(self.available_connections),
                "max_connections": self.max_connections,
                "utilization_percent": (len(self.active_connections) / self.max_connections) * 100
            }

class HealthCheck:
    """Comprehensive health check system"""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_func: Callable, critical: bool = True):
        """Register a health check function"""
        self.checks[name] = {
            "function": check_func,
            "critical": critical
        }

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_status = "healthy"

        for name, check_config in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_config["function"]):
                    result = await check_config["function"]()
                else:
                    result = check_config["function"]()

                results[name] = {
                    "status": "healthy" if result.get("healthy", True) else "unhealthy",
                    "details": result,
                    "critical": check_config["critical"],
                    "checked_at": datetime.now().isoformat()
                }

                if not result.get("healthy", True) and check_config["critical"]:
                    overall_status = "unhealthy"

            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "critical": check_config["critical"],
                    "checked_at": datetime.now().isoformat()
                }

                if check_config["critical"]:
                    overall_status = "unhealthy"

        self.last_results = results
        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.now().isoformat()
        }

    def get_last_results(self) -> Dict[str, Any]:
        """Get results from last health check run"""
        return self.last_results

def performance_tracking(operation_name: str):
    """Decorator to track operation performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                if hasattr(resource_monitor, 'record_request'):
                    resource_monitor.record_request()

                result = await func(*args, **kwargs)

                # Record successful operation
                response_time = time.time() - start_time
                if hasattr(resource_monitor, 'record_response_time'):
                    resource_monitor.record_response_time(response_time)

                return result

            except Exception as e:
                # Record failed operation
                response_time = time.time() - start_time
                logger.error(f"Operation {operation_name} failed after {response_time:.2f}s: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                if hasattr(resource_monitor, 'record_request'):
                    resource_monitor.record_request()

                result = func(*args, **kwargs)

                # Record successful operation
                response_time = time.time() - start_time
                if hasattr(resource_monitor, 'record_response_time'):
                    resource_monitor.record_response_time(response_time)

                return result

            except Exception as e:
                # Record failed operation
                response_time = time.time() - start_time
                logger.error(f"Operation {operation_name} failed after {response_time:.2f}s: {e}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def memory_optimization():
    """Force garbage collection and memory optimization"""
    gc.collect()
    logger.info("Memory optimization completed")

# Global instances
resource_monitor = ResourceMonitor()
cache_manager = CacheManager()
connection_pool = ConnectionPool()
health_checker = HealthCheck()

# Connect cache manager to resource monitor
cache_manager.set_resource_monitor(resource_monitor)

def initialize_production_features():
    """Initialize all production readiness features"""
    try:
        # Start resource monitoring
        resource_monitor.start_monitoring()

        # Register default health checks
        health_checker.register_check("system_resources", check_system_resources)
        health_checker.register_check("cache_health", check_cache_health)
        health_checker.register_check("connection_pool", check_connection_pool)

        logger.info("Production readiness features initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize production features: {e}")
        return False

def check_system_resources() -> Dict[str, Any]:
    """Health check for system resources"""
    try:
        metrics = resource_monitor.get_latest_metrics()
        system = metrics.get("system", {})

        cpu_healthy = system.get("cpu_percent", 0) < 80
        memory_healthy = system.get("memory_percent", 0) < 85
        disk_healthy = system.get("disk_usage_percent", 0) < 90

        return {
            "healthy": cpu_healthy and memory_healthy and disk_healthy,
            "cpu_percent": system.get("cpu_percent", 0),
            "memory_percent": system.get("memory_percent", 0),
            "disk_usage_percent": system.get("disk_usage_percent", 0)
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def check_cache_health() -> Dict[str, Any]:
    """Health check for cache system"""
    try:
        stats = cache_manager.get_stats()
        return {
            "healthy": stats["hit_rate"] > 0.5,  # 50% hit rate threshold
            "stats": stats
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def check_connection_pool() -> Dict[str, Any]:
    """Health check for connection pool"""
    try:
        stats = connection_pool.get_pool_stats()
        return {
            "healthy": stats["utilization_percent"] < 90,  # 90% utilization threshold
            "stats": stats
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def get_production_status() -> Dict[str, Any]:
    """Get comprehensive production status"""
    return {
        "resource_metrics": resource_monitor.get_latest_metrics(),
        "cache_stats": cache_manager.get_stats(),
        "connection_pool_stats": connection_pool.get_pool_stats(),
        "health_checks": health_checker.get_last_results(),
        "timestamp": datetime.now().isoformat()
    }

# Cleanup function
def cleanup_production_features():
    """Cleanup production features on shutdown"""
    try:
        resource_monitor.stop_monitoring()
        cache_manager.clear()
        logger.info("Production features cleaned up")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Test production features
    initialize_production_features()
    time.sleep(2)
    print("Production status:", get_production_status())
    cleanup_production_features()