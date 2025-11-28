"""
Project Configuration Module
=============================
Handles loading, validation, and management of project configurations.
"""
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.models import (
    ProjectConfig,
    MediaPaths,
    ProjectSettings,
    NamingPatterns,
    CacheSettings,
)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path.home() / ".nuke" / "hiero_review_projects"


def list_available_projects() -> List[str]:
    """List all available project configurations."""
    config_dir = get_config_dir()
    if not config_dir.exists():
        return []
    return [f.stem for f in config_dir.glob("*.json")]


def validate_config(data: Dict[str, Any]) -> List[str]:
    """
    Validate configuration data.
    
    Returns:
        List of validation error messages (empty if valid).
    """
    errors = []
    
    # Required fields
    if not data.get('project_name'):
        errors.append("Missing required field: 'project_name'")
    
    if not data.get('project_root'):
        errors.append("Missing required field: 'project_root'")
    
    # Media paths validation
    media_paths = data.get('media_paths', {})
    if not media_paths.get('import_dir'):
        errors.append("Missing required field: 'media_paths.import_dir'")
    
    # Settings validation
    settings = data.get('settings', {})
    fps = settings.get('fps', 24.0)
    if not isinstance(fps, (int, float)) or fps <= 0:
        errors.append(f"Invalid fps value: {fps} (must be positive number)")
    
    resolution = settings.get('resolution', [1920, 1080])
    if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
        errors.append(f"Invalid resolution: {resolution} (must be [width, height])")
    
    # Naming patterns validation (check regex validity)
    naming = data.get('naming', {})
    import re
    for key in ['episode_regex', 'sequence_regex', 'shot_regex', 'version_regex']:
        pattern = naming.get(key)
        if pattern:
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex pattern '{key}': {e}")
    
    return errors


def load_project_config(project_name: str) -> ProjectConfig:
    """
    Load project configuration from JSON file.
    
    Args:
        project_name: Name of the project (without .json extension)
        
    Returns:
        ProjectConfig instance
        
    Raises:
        FileNotFoundError: If config file not found
        ConfigValidationError: If config validation fails
        json.JSONDecodeError: If JSON is invalid
    """
    config_dir = get_config_dir()
    config_file = config_dir / f"{project_name}.json"
    
    if not config_file.exists():
        # Try default config
        config_file = config_dir / "default.json"
        if not config_file.exists():
            raise FileNotFoundError(
                f"Project config '{project_name}' not found and no default.json exists.\n"
                f"Please create a config file at: {config_dir}"
            )
    
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate configuration
    errors = validate_config(data)
    if errors:
        raise ConfigValidationError(
            f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    return ProjectConfig.from_dict(data)


def save_project_config(config: ProjectConfig, project_name: Optional[str] = None) -> Path:
    """
    Save project configuration to JSON file.
    
    Args:
        config: ProjectConfig instance to save
        project_name: Optional name override (defaults to config.project_name)
        
    Returns:
        Path to saved config file
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    name = project_name or config.project_name
    config_file = config_dir / f"{name}.json"
    
    data = {
        'schema_version': config.schema_version,
        'project_name': config.project_name,
        'project_root': config.project_root,
        'media_paths': {
            'import_dir': config.media_paths.import_dir,
            'export_dir': config.media_paths.export_dir,
            'audio_dir': config.media_paths.audio_dir,
        },
        'structure': config.structure,
        'settings': {
            'fps': config.settings.fps,
            'resolution': list(config.settings.resolution),
            'color_space': config.settings.color_space,
            'default_department': config.settings.default_department,
            'default_media_type': config.settings.default_media_type,
        },
        'naming': {
            'episode_regex': config.naming.episode_regex,
            'sequence_regex': config.naming.sequence_regex,
            'shot_regex': config.naming.shot_regex,
            'version_regex': config.naming.version_regex,
        },
        'cache': {
            'enabled': config.cache.enabled,
            'memory_ttl_seconds': config.cache.memory_ttl_seconds,
            'disk_ttl_seconds': config.cache.disk_ttl_seconds,
            'disk_path': config.cache.disk_path,
        },
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return config_file

