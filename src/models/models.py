"""
Data Models for Hiero Review Tool
==================================
Dataclasses for type-safe configuration and data handling.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import re


@dataclass
class NamingPatterns:
    """Regex patterns for parsing file/folder names."""
    episode_regex: str = r"Ep\d{2}"
    sequence_regex: str = r"sq\d{4}"
    shot_regex: str = r"SH\d{4}"
    version_regex: str = r"v\d{3,4}"
    
    def compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns."""
        return {
            'episode': re.compile(self.episode_regex),
            'sequence': re.compile(self.sequence_regex),
            'shot': re.compile(self.shot_regex),
            'version': re.compile(self.version_regex),
        }


@dataclass
class MediaPaths:
    """Media directory paths for a project."""
    import_dir: str = ""
    export_dir: str = ""
    audio_dir: str = ""


@dataclass
class ProjectSettings:
    """Project-level settings."""
    fps: float = 24.0
    resolution: Tuple[int, int] = (1920, 1080)
    color_space: str = "ACES"
    default_department: str = "comp"
    default_media_type: str = "mov"


@dataclass
class CacheSettings:
    """Cache configuration settings."""
    enabled: bool = True
    memory_ttl_seconds: int = 60
    disk_ttl_seconds: int = 3600
    disk_path: str = "~/.nuke/cache/hiero_review"


@dataclass
class ProjectConfig:
    """Complete project configuration."""
    project_name: str
    project_root: str
    media_paths: MediaPaths
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    naming: NamingPatterns = field(default_factory=NamingPatterns)
    cache: CacheSettings = field(default_factory=CacheSettings)
    schema_version: str = "1.0"
    structure: Dict[str, str] = field(default_factory=dict)
    
    @property
    def import_dir(self) -> str:
        return self.media_paths.import_dir
    
    @property
    def export_dir(self) -> str:
        return self.media_paths.export_dir
    
    @property
    def audio_dir(self) -> str:
        return self.media_paths.audio_dir
    
    @property
    def fps(self) -> float:
        return self.settings.fps
    
    @property
    def resolution(self) -> Tuple[int, int]:
        return self.settings.resolution
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create ProjectConfig from dictionary (JSON data)."""
        media_paths = MediaPaths(**data.get('media_paths', {}))
        
        settings_data = data.get('settings', {})
        resolution = settings_data.get('resolution', [1920, 1080])
        if isinstance(resolution, list):
            resolution = tuple(resolution)
        settings = ProjectSettings(
            fps=settings_data.get('fps', 24.0),
            resolution=resolution,
            color_space=settings_data.get('color_space', 'ACES'),
            default_department=settings_data.get('default_department', 'comp'),
            default_media_type=settings_data.get('default_media_type', 'mov'),
        )
        
        naming = NamingPatterns(**data.get('naming', {}))
        cache = CacheSettings(**data.get('cache', {}))
        
        return cls(
            project_name=data.get('project_name', 'Untitled'),
            project_root=data.get('project_root', ''),
            media_paths=media_paths,
            settings=settings,
            naming=naming,
            cache=cache,
            schema_version=data.get('schema_version', '1.0'),
            structure=data.get('structure', {}),
        )


@dataclass
class DepartmentInfo:
    """Information about a department's output for a shot."""
    name: str
    versions: List[str] = field(default_factory=list)
    current_version: str = ""
    has_mov: bool = False
    has_sequence: bool = False
    output_path: str = ""
    version_path: str = ""


@dataclass
class ShotInfo:
    """Information about a single shot."""
    episode: str
    sequence: str
    shot: str
    departments: Dict[str, DepartmentInfo] = field(default_factory=dict)
    frame_range: Tuple[int, int] = (1001, 1100)
    audio_path: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get full shot name (e.g., 'Ep01_sq0030_SH0060')."""
        return f"{self.episode}_{self.sequence}_{self.shot}"


@dataclass
class ScanResult:
    """Result of a project scan operation."""
    episodes: Dict[str, Dict] = field(default_factory=dict)
    scan_time: float = 0.0
    cached: bool = False
    error: Optional[str] = None


@dataclass
class CacheEntry:
    """A single cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: int

