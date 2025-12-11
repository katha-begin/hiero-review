"""
Lighting Scanner Module
========================
Scans lighting department folder for versions, layers, and render passes.

Expected folder structure:
    {shot}/lighting/version/{version}/{layer}/{image.####.exr}

Example:
    SH0010/lighting/version/v001/MASTER_CHAR_A/fileName.1001.exr
    SH0010/lighting/version/v001/MASTER_CHAR_B/fileName.1001.exr
    SH0010/lighting/version/v002/MASTER_ENV/fileName.1001.exr
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.path_parser import parse_frame_number


@dataclass
class RenderPassInfo:
    """Information about a render pass (image sequence in a layer folder)."""
    name: str  # e.g., "fileName" (base name without frame number)
    directory: str  # Full path to layer folder
    pattern: str  # e.g., "fileName.####.exr"
    start_frame: int
    end_frame: int
    frame_count: int
    files: List[str] = field(default_factory=list)
    
    @property
    def hiero_pattern(self) -> str:
        """Get Hiero-compatible pattern (with ####)."""
        return f"{self.directory}/{self.pattern}"
    
    @property
    def printf_pattern(self) -> str:
        """Get printf-style pattern (%04d)."""
        # Extract padding from pattern
        hash_count = self.pattern.count('#')
        base = self.pattern.replace('#' * hash_count, f'%0{hash_count}d')
        return f"{self.directory}/{base}"


@dataclass
class LayerInfo:
    """Information about a render layer (folder containing render passes)."""
    name: str  # e.g., "MASTER_CHAR_A"
    path: str  # Full path to layer folder
    render_passes: List[RenderPassInfo] = field(default_factory=list)


@dataclass
class VersionInfo:
    """Information about a lighting version."""
    version: str  # e.g., "v001"
    path: str  # Full path to version folder
    layers: List[LayerInfo] = field(default_factory=list)


@dataclass
class LightingScanResult:
    """Result of scanning lighting department for a shot."""
    shot_name: str
    department: str  # "lighting"
    versions: List[VersionInfo] = field(default_factory=list)
    latest_version: Optional[str] = None
    
    @property
    def has_data(self) -> bool:
        return len(self.versions) > 0


class LightingScanner:
    """
    Scans lighting department folder structure for renders.
    
    Structure: {shot}/lighting/version/{version}/{layer}/{sequence.####.exr}
    """
    
    # Pattern to match frame numbers in filenames (e.g., .1001. or .0001.)
    FRAME_PATTERN = re.compile(r'\.(\d{4,})\.(\w+)$')
    
    # Supported image formats
    IMAGE_FORMATS = {'.exr'}  # Only EXR as per requirements
    
    def __init__(self, project_root: str):
        """
        Initialize LightingScanner.
        
        Args:
            project_root: Root directory of the project
        """
        self._project_root = Path(project_root)
    
    def scan_shot_lighting(
        self, 
        episode: str, 
        sequence: str, 
        shot: str,
        department: str = "lighting"
    ) -> LightingScanResult:
        """
        Scan lighting department for a specific shot.
        
        Args:
            episode: Episode name (e.g., "Ep01")
            sequence: Sequence name (e.g., "sq0010")
            shot: Shot name (e.g., "SH0010")
            department: Department name (default: "lighting")
            
        Returns:
            LightingScanResult with all versions, layers, and render passes
        """
        result = LightingScanResult(
            shot_name=f"{episode}_{sequence}_{shot}",
            department=department
        )
        
        # Build path to lighting version folder
        lighting_path = self._project_root / episode / sequence / shot / department / "version"
        
        if not lighting_path.exists():
            return result
        
        # Scan for version folders
        versions = self._scan_versions(lighting_path)
        result.versions = versions
        
        if versions:
            result.latest_version = versions[-1].version  # Last is latest (sorted)
        
        return result
    
    def _scan_versions(self, version_root: Path) -> List[VersionInfo]:
        """Scan for version folders (v001, v002, etc.)."""
        versions = []
        
        try:
            for item in sorted(version_root.iterdir()):
                if item.is_dir() and item.name.lower().startswith('v'):
                    version_info = VersionInfo(
                        version=item.name,
                        path=str(item)
                    )
                    version_info.layers = self._scan_layers(item)
                    versions.append(version_info)
        except PermissionError:
            pass
        
        return versions
    
    def _scan_layers(self, version_path: Path) -> List[LayerInfo]:
        """Scan for layer folders inside a version folder."""
        layers = []

        try:
            for item in sorted(version_path.iterdir()):
                if item.is_dir():
                    layer_info = LayerInfo(
                        name=item.name,
                        path=str(item)
                    )
                    layer_info.render_passes = self._scan_render_passes(item)
                    if layer_info.render_passes:  # Only add layers with render passes
                        layers.append(layer_info)
        except PermissionError:
            pass

        return layers

    def _scan_render_passes(self, layer_path: Path) -> List[RenderPassInfo]:
        """Scan for image sequences (render passes) in a layer folder."""
        # Group files by base name (sequence detection)
        sequences: Dict[str, List[Tuple[str, int]]] = {}

        try:
            for file_path in layer_path.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in self.IMAGE_FORMATS:
                    continue

                # Extract frame number using pattern
                match = self.FRAME_PATTERN.search(file_path.name)
                if not match:
                    continue

                frame_num = int(match.group(1))
                ext = f".{match.group(2)}"

                # Get base name (everything before frame number)
                base_name = file_path.name[:match.start()]
                if base_name.endswith('.'):
                    base_name = base_name[:-1]

                key = f"{base_name}{ext}"
                if key not in sequences:
                    sequences[key] = []
                sequences[key].append((str(file_path), frame_num))
        except PermissionError:
            pass

        # Build RenderPassInfo for each sequence
        result = []
        for key, files in sequences.items():
            if len(files) < 1:  # Allow single-frame sequences
                continue

            files.sort(key=lambda x: x[1])
            frames = [f[1] for f in files]

            # Detect padding from first file
            first_file = Path(files[0][0]).name
            match = self.FRAME_PATTERN.search(first_file)
            padding = len(match.group(1)) if match else 4

            start_frame, end_frame = min(frames), max(frames)

            # Build pattern (e.g., "fileName.####.exr")
            base_name = key.rsplit('.', 1)[0]
            extension = f".{key.rsplit('.', 1)[1]}" if '.' in key else ""
            pattern = f"{base_name}.{'#' * padding}{extension}"

            result.append(RenderPassInfo(
                name=base_name,
                directory=str(layer_path),
                pattern=pattern,
                start_frame=start_frame,
                end_frame=end_frame,
                frame_count=len(frames),
                files=[f[0] for f in files]
            ))

        return result

    def get_shot_info_from_track_item(self, track_item) -> Optional[Dict[str, str]]:
        """
        Extract episode, sequence, shot info from a track item.

        Args:
            track_item: Hiero track item

        Returns:
            Dict with 'episode', 'sequence', 'shot' keys or None
        """
        try:
            # Try metadata first
            metadata = track_item.metadata()
            if metadata:
                shot = metadata.value("shot")
                if shot:
                    # Parse shot name like "Ep01_sq0010_SH0010"
                    parts = shot.split('_')
                    if len(parts) >= 3:
                        return {
                            'episode': parts[0],
                            'sequence': parts[1],
                            'shot': parts[2]
                        }

            # Fallback: try to get from source path
            source = track_item.source()
            if source:
                path = source.mediaSource().fileinfos()[0].filename()
                return self._parse_path_components(path)
        except Exception:
            pass

        return None

    def _parse_path_components(self, path: str) -> Optional[Dict[str, str]]:
        """Parse episode, sequence, shot from file path."""
        path_lower = path.lower()
        parts = path.replace('\\', '/').split('/')

        result = {}
        for i, part in enumerate(parts):
            part_lower = part.lower()
            if part_lower.startswith('ep') and 'episode' not in result:
                result['episode'] = part
            elif part_lower.startswith('sq') and 'sequence' not in result:
                result['sequence'] = part
            elif part_lower.startswith('sh') and 'shot' not in result:
                result['shot'] = part

        if 'episode' in result and 'sequence' in result and 'shot' in result:
            return result
        return None

