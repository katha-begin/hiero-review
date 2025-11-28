"""
Media File Validators Module
=============================
Validation utilities for media files, frame sequences, and naming conventions.
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from .path_parser import (
    EP_PATTERN, SEQ_PATTERN, SHOT_PATTERN, VERSION_PATTERN,
    parse_frame_number,
)


class Severity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    """A single validation message."""
    severity: Severity
    message: str
    path: Optional[str] = None


@dataclass
class ValidationReport:
    """Validation report containing all messages."""
    messages: List[ValidationMessage] = field(default_factory=list)
    
    @property
    def errors(self) -> List[str]:
        return [m.message for m in self.messages if m.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[str]:
        return [m.message for m in self.messages if m.severity == Severity.WARNING]
    
    @property
    def info(self) -> List[str]:
        return [m.message for m in self.messages if m.severity == Severity.INFO]
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def add_error(self, message: str, path: str = None) -> None:
        self.messages.append(ValidationMessage(Severity.ERROR, message, path))
    
    def add_warning(self, message: str, path: str = None) -> None:
        self.messages.append(ValidationMessage(Severity.WARNING, message, path))
    
    def add_info(self, message: str, path: str = None) -> None:
        self.messages.append(ValidationMessage(Severity.INFO, message, path))


def validate_naming_convention(filename: str) -> bool:
    """
    Validate if filename follows naming convention.
    Expected: Ep##_sq####_SH####_v###.ext or Ep##_sq####_SH####.####.ext
    """
    # Check for episode
    if not re.search(EP_PATTERN, filename, re.IGNORECASE):
        return False
    # Check for sequence
    if not re.search(SEQ_PATTERN, filename, re.IGNORECASE):
        return False
    # Check for shot
    if not re.search(SHOT_PATTERN, filename, re.IGNORECASE):
        return False
    return True


def validate_version_format(version_str: str) -> bool:
    """Validate version string format (v001, v01, v1, V001)."""
    return bool(re.match(r'^[vV]\d{1,4}$', version_str))


def validate_frame_sequence(files: List[str]) -> Dict[str, any]:
    """
    Validate a frame sequence for completeness.
    
    Returns:
        Dict with 'complete', 'missing_frames', 'frame_range'
    """
    frames = []
    for f in files:
        frame = parse_frame_number(f)
        if frame is not None:
            frames.append(frame)
    
    if not frames:
        return {'complete': False, 'missing_frames': [], 'frame_range': None}
    
    frames = sorted(frames)
    start, end = frames[0], frames[-1]
    expected = set(range(start, end + 1))
    actual = set(frames)
    missing = sorted(expected - actual)
    
    return {
        'complete': len(missing) == 0,
        'missing_frames': missing,
        'frame_range': (start, end),
    }


def validate_project_structure(root: str) -> ValidationReport:
    """
    Validate project directory structure.
    
    Checks for:
    - Episode folders (Ep##)
    - Sequence folders (sq####)
    - Shot folders (SH####)
    - Department folders
    """
    report = ValidationReport()
    root_path = Path(root)
    
    if not root_path.exists():
        report.add_error(f"Project root does not exist: {root}")
        return report
    
    # Check for episode folders
    episodes = [d for d in root_path.iterdir() if d.is_dir() and re.match(EP_PATTERN, d.name, re.IGNORECASE)]
    
    if not episodes:
        report.add_warning("No episode folders found (expected Ep## format)")
        return report
    
    report.add_info(f"Found {len(episodes)} episode(s)")
    
    for ep in episodes:
        sequences = [d for d in ep.iterdir() if d.is_dir() and re.match(SEQ_PATTERN, d.name, re.IGNORECASE)]
        if not sequences:
            report.add_warning(f"No sequences in {ep.name}")
            continue
        
        for seq in sequences:
            shots = [d for d in seq.iterdir() if d.is_dir() and re.match(SHOT_PATTERN, d.name, re.IGNORECASE)]
            if not shots:
                report.add_warning(f"No shots in {ep.name}/{seq.name}")
    
    return report


def validate_audio_match(video_path: str, audio_path: str) -> bool:
    """Check if audio file matches video file by naming convention."""
    video_name = Path(video_path).stem
    audio_name = Path(audio_path).stem
    
    # Extract ep, seq, shot from both
    video_ep = re.search(EP_PATTERN, video_name, re.IGNORECASE)
    audio_ep = re.search(EP_PATTERN, audio_name, re.IGNORECASE)
    
    if not video_ep or not audio_ep:
        return False
    
    return video_ep.group(1).lower() == audio_ep.group(1).lower()

