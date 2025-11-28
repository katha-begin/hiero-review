"""
Image Sequence Handler Module
==============================
Loading and managing image sequences (PNG, EXR, etc.) in timelines.
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field

from .hiero_wrapper import HieroClip
from ..utils.path_parser import parse_frame_number


# Supported image formats
IMAGE_FORMATS = {'.png', '.exr', '.jpg', '.jpeg', '.tif', '.tiff', '.dpx'}


@dataclass
class SequenceInfo:
    """Information about an image sequence."""
    pattern: str  # e.g., "file.####.png" or "file.%04d.png"
    directory: str
    base_name: str
    extension: str
    start_frame: int
    end_frame: int
    frame_count: int
    missing_frames: List[int] = field(default_factory=list)
    padding: int = 4
    
    @property
    def is_complete(self) -> bool:
        """Check if sequence has no missing frames."""
        return len(self.missing_frames) == 0
    
    @property
    def hiero_pattern(self) -> str:
        """Get pattern in Hiero format (####)."""
        return f"{self.directory}/{self.base_name}.{'#' * self.padding}{self.extension}"
    
    @property
    def printf_pattern(self) -> str:
        """Get pattern in printf format (%04d)."""
        return f"{self.directory}/{self.base_name}.%0{self.padding}d{self.extension}"


@dataclass
class ValidationResult:
    """Result of sequence validation."""
    is_valid: bool
    frame_count: int = 0
    missing_frames: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SequenceHandler:
    """
    Handles detection, validation, and loading of image sequences.
    """
    
    # Pattern to detect frame number in filename
    FRAME_PATTERN = re.compile(r'\.(\d{4,})\.(\w+)$')
    
    def __init__(self):
        """Initialize SequenceHandler."""
        pass
    
    def detect_sequences(self, directory: str) -> List[SequenceInfo]:
        """
        Detect all image sequences in a directory.
        
        Args:
            directory: Path to search for sequences
            
        Returns:
            List of SequenceInfo for each detected sequence
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        # Group files by base name (without frame number)
        sequences: Dict[str, List[Tuple[str, int]]] = {}
        
        for file_path in dir_path.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in IMAGE_FORMATS:
                continue
            
            # Extract frame number
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
        
        # Build SequenceInfo for each detected sequence
        result = []
        for key, files in sequences.items():
            if len(files) < 2:
                continue  # Single file, not a sequence
            
            files.sort(key=lambda x: x[1])
            frames = [f[1] for f in files]
            
            # Detect padding from first file
            first_file = Path(files[0][0]).name
            match = self.FRAME_PATTERN.search(first_file)
            padding = len(match.group(1)) if match else 4
            
            # Find missing frames
            start_frame, end_frame = min(frames), max(frames)
            expected = set(range(start_frame, end_frame + 1))
            actual = set(frames)
            missing = sorted(expected - actual)
            
            # Extract base name and extension
            base_name = key.rsplit('.', 1)[0]
            extension = f".{key.rsplit('.', 1)[1]}" if '.' in key else ""
            
            result.append(SequenceInfo(
                pattern=f"{base_name}.{'#' * padding}{extension}",
                directory=str(dir_path),
                base_name=base_name,
                extension=extension,
                start_frame=start_frame,
                end_frame=end_frame,
                frame_count=len(frames),
                missing_frames=missing,
                padding=padding
            ))
        
        return result
    
    def create_sequence_clip(self, sequence_info: SequenceInfo) -> any:
        """
        Create a Hiero clip from sequence info.
        
        Args:
            sequence_info: SequenceInfo object
            
        Returns:
            Hiero clip object
        """
        frame_range = (sequence_info.start_frame, sequence_info.end_frame)
        return HieroClip.create_from_sequence(
            sequence_info.hiero_pattern,
            frame_range
        )
    
    def validate_sequence(self, files: List[str]) -> ValidationResult:
        """
        Validate a list of sequence files.
        
        Args:
            files: List of file paths
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=True)
        
        frames = []
        for f in files:
            frame = parse_frame_number(f)
            if frame is not None:
                frames.append(frame)
        
        if not frames:
            result.is_valid = False
            result.errors.append("No valid frame numbers found")
            return result
        
        frames.sort()
        result.frame_count = len(frames)
        
        # Check for missing frames
        start, end = frames[0], frames[-1]
        expected = set(range(start, end + 1))
        actual = set(frames)
        result.missing_frames = sorted(expected - actual)
        
        if result.missing_frames:
            result.errors.append(f"Missing {len(result.missing_frames)} frames")
        
        return result
    
    def get_frame_range(self, files: List[str]) -> Optional[Tuple[int, int]]:
        """Get frame range from list of files."""
        frames = [parse_frame_number(f) for f in files]
        frames = [f for f in frames if f is not None]
        
        if frames:
            return (min(frames), max(frames))
        return None
    
    def detect_missing_frames(self, files: List[str]) -> List[int]:
        """Detect missing frames in a sequence."""
        frames = [parse_frame_number(f) for f in files if parse_frame_number(f) is not None]
        if len(frames) < 2:
            return []
        
        start, end = min(frames), max(frames)
        expected = set(range(start, end + 1))
        return sorted(expected - set(frames))

