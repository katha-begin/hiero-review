"""
Performance Profiling Module
============================
Tools for profiling and optimizing performance.
"""
import time
import functools
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import contextmanager

from .logger import get_logger

_logger = get_logger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiled operation."""
    name: str
    duration: float
    calls: int = 1
    avg_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    
    def __post_init__(self):
        if self.avg_duration == 0.0:
            self.avg_duration = self.duration
        if self.min_duration == 0.0:
            self.min_duration = self.duration
        if self.max_duration == 0.0:
            self.max_duration = self.duration


class Profiler:
    """Simple profiler for tracking operation performance."""
    
    _instance: Optional['Profiler'] = None
    
    def __init__(self):
        self._results: Dict[str, ProfileResult] = {}
        self._enabled = True
    
    @classmethod
    def get_instance(cls) -> 'Profiler':
        """Get singleton profiler instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def enable(self) -> None:
        """Enable profiling."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable profiling."""
        self._enabled = False
    
    def clear(self) -> None:
        """Clear all profiling results."""
        self._results.clear()
    
    def record(self, name: str, duration: float) -> None:
        """Record a profiling result."""
        if not self._enabled:
            return
        
        if name in self._results:
            result = self._results[name]
            result.calls += 1
            result.duration += duration
            result.avg_duration = result.duration / result.calls
            result.min_duration = min(result.min_duration, duration)
            result.max_duration = max(result.max_duration, duration)
        else:
            self._results[name] = ProfileResult(name=name, duration=duration)
    
    def get_results(self) -> Dict[str, ProfileResult]:
        """Get all profiling results."""
        return self._results.copy()
    
    def get_summary(self) -> str:
        """Get a formatted summary of profiling results."""
        if not self._results:
            return "No profiling data collected."
        
        lines = ["Performance Summary:", "-" * 60]
        
        # Sort by total duration
        sorted_results = sorted(
            self._results.values(),
            key=lambda r: r.duration,
            reverse=True
        )
        
        for result in sorted_results:
            lines.append(
                f"{result.name}: {result.duration:.3f}s total, "
                f"{result.calls} calls, {result.avg_duration:.3f}s avg"
            )
        
        return "\n".join(lines)


# Global profiler instance
_profiler = Profiler.get_instance()


def profile(name: Optional[str] = None) -> Callable:
    """
    Decorator to profile a function.
    
    Args:
        name: Optional name for the profile entry (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        profile_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                _profiler.record(profile_name, duration)
        
        return wrapper
    return decorator


@contextmanager
def profile_block(name: str):
    """
    Context manager to profile a code block.
    
    Usage:
        with profile_block("my_operation"):
            # code to profile
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        _profiler.record(name, duration)


def get_profiler() -> Profiler:
    """Get the global profiler instance."""
    return _profiler


def print_profile_summary() -> None:
    """Print profiling summary to logger."""
    _logger.info(_profiler.get_summary())

