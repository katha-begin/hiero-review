"""
Error Handling Module
=====================
Custom exceptions and error handling utilities.
"""
from typing import Optional, Any, Dict


class HieroReviewError(Exception):
    """Base exception for Hiero Review Tool."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ConfigurationError(HieroReviewError):
    """Error in configuration loading or validation."""
    pass


class ProjectNotFoundError(HieroReviewError):
    """Project directory or configuration not found."""
    pass


class MediaNotFoundError(HieroReviewError):
    """Media file or sequence not found."""
    pass


class VersionNotFoundError(HieroReviewError):
    """Requested version not found."""
    pass


class InvalidPathError(HieroReviewError):
    """Invalid file path or naming convention."""
    pass


class ScanError(HieroReviewError):
    """Error during project scanning."""
    pass


class TimelineBuildError(HieroReviewError):
    """Error building timeline."""
    pass


class HieroAPIError(HieroReviewError):
    """Error interacting with Hiero API."""
    pass


class CacheError(HieroReviewError):
    """Error with cache operations."""
    pass


class ValidationError(HieroReviewError):
    """Validation failed."""
    pass


def handle_error(error: Exception, context: str = "") -> str:
    """
    Handle an error and return a user-friendly message.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, HieroReviewError):
        return str(error)
    
    # Map common exceptions to friendly messages
    error_messages = {
        FileNotFoundError: "File or directory not found",
        PermissionError: "Permission denied - check file permissions",
        OSError: "System error occurred",
        ValueError: "Invalid value provided",
        TypeError: "Invalid type provided",
        KeyError: "Required key not found",
    }
    
    base_message = error_messages.get(type(error), "An unexpected error occurred")
    
    if context:
        return f"{base_message} while {context}: {error}"
    return f"{base_message}: {error}"


def safe_operation(default: Any = None, log_errors: bool = True):
    """
    Decorator for safe operation execution with error handling.
    
    Args:
        default: Default value to return on error
        log_errors: Whether to log errors
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    from .logger import log_error
                    log_error(f"Error in {func.__name__}", e)
                return default
        return wrapper
    return decorator


class ErrorCollector:
    """Collect multiple errors during an operation."""
    
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []
    
    def add_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Add an error."""
        self.errors.append({
            "message": message,
            "exception": str(exception) if exception else None
        })
    
    def add_warning(self, message: str) -> None:
        """Add a warning."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def get_summary(self) -> str:
        """Get error summary."""
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  - {err['message']}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  - {warn}")
        return "\n".join(lines) if lines else "No errors or warnings"

