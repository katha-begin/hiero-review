"""
Utility functions for Hiero Review Tool.
"""

from .path_parser import (
    normalize_path,
    extract_episode,
    extract_sequence,
    extract_shot,
    extract_department,
    parse_shot_path,
    parse_version_from_filename,
    parse_frame_number,
    get_frame_range,
    # Patterns (for custom regex in config)
    EP_PATTERN,
    SEQ_PATTERN,
    SHOT_PATTERN,
    VERSION_PATTERN,
    FRAME_PATTERN,
)

from .validators import (
    ValidationReport,
    ValidationMessage,
    Severity,
    validate_naming_convention,
    validate_version_format,
    validate_frame_sequence,
    validate_project_structure,
    validate_audio_match,
)

from .logger import (
    get_logger,
    setup_logging,
    LogContext,
    log_operation,
    log_error,
    log_warning,
    log_info,
    log_debug,
)

from .profiler import (
    Profiler,
    ProfileResult,
    profile,
    profile_block,
    get_profiler,
    print_profile_summary,
)

from .errors import (
    HieroReviewError,
    ConfigurationError,
    ProjectNotFoundError,
    MediaNotFoundError,
    VersionNotFoundError,
    InvalidPathError,
    ScanError,
    TimelineBuildError,
    HieroAPIError,
    CacheError,
    ValidationError,
    handle_error,
    safe_operation,
    ErrorCollector,
)

__all__ = [
    # Path parser
    'normalize_path',
    'extract_episode',
    'extract_sequence',
    'extract_shot',
    'extract_department',
    'parse_shot_path',
    'parse_version_from_filename',
    'parse_frame_number',
    'get_frame_range',
    'EP_PATTERN',
    'SEQ_PATTERN',
    'SHOT_PATTERN',
    'VERSION_PATTERN',
    'FRAME_PATTERN',
    # Validators
    'ValidationReport',
    'ValidationMessage',
    'Severity',
    'validate_naming_convention',
    'validate_version_format',
    'validate_frame_sequence',
    'validate_project_structure',
    'validate_audio_match',
    # Logger
    'get_logger',
    'setup_logging',
    'LogContext',
    'log_operation',
    'log_error',
    'log_warning',
    'log_info',
    'log_debug',
    # Profiler
    'Profiler',
    'ProfileResult',
    'profile',
    'profile_block',
    'get_profiler',
    'print_profile_summary',
    # Errors
    'HieroReviewError',
    'ConfigurationError',
    'ProjectNotFoundError',
    'MediaNotFoundError',
    'VersionNotFoundError',
    'InvalidPathError',
    'ScanError',
    'TimelineBuildError',
    'HieroAPIError',
    'CacheError',
    'ValidationError',
    'handle_error',
    'safe_operation',
    'ErrorCollector',
]

