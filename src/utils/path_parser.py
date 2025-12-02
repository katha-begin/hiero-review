"""
Path Parser Module
===================
Utility functions for parsing project file paths and extracting metadata.
"""
import os
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Default regex patterns
EP_PATTERN = r'(Ep\d{2})'
SEQ_PATTERN = r'(sq\d{4})'
SHOT_PATTERN = r'(SH\d{4})'
SHOT_WITH_SUFFIX_PATTERN = r'(SH\d{4})([A-Za-z])?'  # Matches SH0010, SH0010A, SH0010B
VERSION_PATTERN = r'[_/]v(\d{3,4})'
FRAME_PATTERN = r'\.(\d{4,5})\.\w+$'

# Compiled patterns for performance
_EP_RE = re.compile(EP_PATTERN, re.IGNORECASE)
_SEQ_RE = re.compile(SEQ_PATTERN, re.IGNORECASE)
_SHOT_RE = re.compile(SHOT_PATTERN, re.IGNORECASE)
_SHOT_SUFFIX_RE = re.compile(SHOT_WITH_SUFFIX_PATTERN, re.IGNORECASE)
_VERSION_RE = re.compile(VERSION_PATTERN, re.IGNORECASE)
_FRAME_RE = re.compile(FRAME_PATTERN)


def normalize_path(path: str) -> str:
    """
    Normalize path separators for cross-platform compatibility.
    
    Args:
        path: File path string
        
    Returns:
        Normalized path with forward slashes
    """
    return path.replace('\\', '/')


def extract_episode(path: str) -> Optional[str]:
    """
    Extract episode identifier from path.
    
    Args:
        path: File path string
        
    Returns:
        Episode string (e.g., 'Ep01') or None
    """
    path = normalize_path(path)
    match = _EP_RE.search(path)
    return match.group(1) if match else None


def extract_sequence(path: str) -> Optional[str]:
    """
    Extract sequence identifier from path.
    
    Args:
        path: File path string
        
    Returns:
        Sequence string (e.g., 'sq0030') or None
    """
    path = normalize_path(path)
    match = _SEQ_RE.search(path)
    return match.group(1) if match else None


def extract_shot(path: str) -> Optional[str]:
    """
    Extract shot identifier from path.
    
    Args:
        path: File path string
        
    Returns:
        Shot string (e.g., 'SH0060') or None
    """
    path = normalize_path(path)
    match = _SHOT_RE.search(path)
    return match.group(1) if match else None


def extract_department(path: str) -> Optional[str]:
    """
    Extract department from path based on common department names.
    
    Args:
        path: File path string
        
    Returns:
        Department string or None
    """
    path = normalize_path(path).lower()
    departments = ['comp', 'light', 'lighting', 'anim', 'animation', 'fx', 'efx', 'roto', 'paint']
    
    for dept in departments:
        if f'/{dept}/' in path or f'/{dept}' == path[-len(dept)-1:]:
            return dept
    
    return None


def parse_shot_path(path: str) -> Dict[str, Optional[str]]:
    """
    Parse a shot path and extract all components.
    
    Args:
        path: File path string
        
    Returns:
        Dictionary with ep, seq, shot, dept keys
        
    Example:
        >>> parse_shot_path("V:/SWA/all/scene/Ep01/sq0030/SH0060/comp/output/file.mov")
        {'ep': 'Ep01', 'seq': 'sq0030', 'shot': 'SH0060', 'dept': 'comp'}
    """
    return {
        'ep': extract_episode(path),
        'seq': extract_sequence(path),
        'shot': extract_shot(path),
        'dept': extract_department(path),
    }


def parse_version_from_filename(filename: str) -> Optional[str]:
    """
    Extract version string from filename.
    
    Args:
        filename: Filename or path string
        
    Returns:
        Version string (e.g., 'v009') or None
        
    Example:
        >>> parse_version_from_filename("Ep01_sq0030_SH0060_v009.mov")
        'v009'
    """
    match = _VERSION_RE.search(filename)
    if match:
        return f"v{match.group(1)}"
    return None


def parse_frame_number(filename: str) -> Optional[int]:
    """
    Extract frame number from image sequence filename.
    
    Args:
        filename: Filename string
        
    Returns:
        Frame number as integer or None
        
    Example:
        >>> parse_frame_number("Ep01_sq0030_SH0060.1001.png")
        1001
    """
    match = _FRAME_RE.search(filename)
    if match:
        return int(match.group(1))
    return None


def get_frame_range(files: List[str]) -> Optional[Tuple[int, int]]:
    """
    Get frame range from a list of sequence files.
    
    Args:
        files: List of filenames
        
    Returns:
        Tuple of (start_frame, end_frame) or None
    """
    frames = []
    for f in files:
        frame = parse_frame_number(f)
        if frame is not None:
            frames.append(frame)
    
    if frames:
        return (min(frames), max(frames))
    return None


def is_sub_shot(shot_name: str) -> bool:
    """
    Check if a shot name is a sub-shot (has A, B, C suffix).

    Args:
        shot_name: Shot name like 'SH0010' or 'SH0010A'

    Returns:
        True if it's a sub-shot (e.g., SH0010A, SH0010B)

    Example:
        >>> is_sub_shot('SH0010')
        False
        >>> is_sub_shot('SH0010A')
        True
    """
    match = _SHOT_SUFFIX_RE.search(shot_name)
    if match:
        suffix = match.group(2)
        return suffix is not None
    return False


def get_base_shot(shot_name: str) -> str:
    """
    Get the base shot name without A/B/C suffix.

    Args:
        shot_name: Shot name like 'SH0010A'

    Returns:
        Base shot name like 'SH0010'

    Example:
        >>> get_base_shot('SH0010A')
        'SH0010'
    """
    match = _SHOT_SUFFIX_RE.search(shot_name)
    if match:
        return match.group(1)
    return shot_name


def filter_sub_shots(shot_names: List[str]) -> List[str]:
    """
    Filter out sub-shots, keeping only base shots.
    If both SH0010 and SH0010A exist, keep only SH0010.

    Args:
        shot_names: List of shot names

    Returns:
        Filtered list with only base shots

    Example:
        >>> filter_sub_shots(['SH0010', 'SH0010A', 'SH0010B', 'SH0020'])
        ['SH0010', 'SH0020']
    """
    base_shots = set()
    result = []

    for shot in shot_names:
        if is_sub_shot(shot):
            # Skip sub-shots
            continue
        base = get_base_shot(shot)
        if base not in base_shots:
            base_shots.add(base)
            result.append(shot)

    return result


def extract_shot_number(shot_name: str) -> int:
    """
    Extract numeric part of shot name for sorting.

    Args:
        shot_name: Shot name like 'SH0010' or 'SH0015'

    Returns:
        Numeric value (e.g., 10, 15)
    """
    match = re.search(r'\d+', shot_name)
    if match:
        return int(match.group())
    return 0


def extract_sequence_number(seq_name: str) -> int:
    """
    Extract numeric part of sequence name for sorting.

    Args:
        seq_name: Sequence name like 'sq0010' or 'sq0015'

    Returns:
        Numeric value (e.g., 10, 15)
    """
    match = re.search(r'\d+', seq_name)
    if match:
        return int(match.group())
    return 0


def sort_shots(shot_names: List[str]) -> List[str]:
    """
    Sort shots by numeric order.

    Args:
        shot_names: List of shot names

    Returns:
        Sorted list: SH0010, SH0015, SH0018, SH0020
    """
    return sorted(shot_names, key=extract_shot_number)


def sort_sequences(seq_names: List[str]) -> List[str]:
    """
    Sort sequences by numeric order.

    Args:
        seq_names: List of sequence names

    Returns:
        Sorted list: sq0010, sq0015, sq0020
    """
    return sorted(seq_names, key=extract_sequence_number)


def filter_and_sort_shots(shot_names: List[str]) -> List[str]:
    """
    Filter out sub-shots and sort by numeric order.

    Args:
        shot_names: List of shot names

    Returns:
        Filtered and sorted list

    Example:
        >>> filter_and_sort_shots(['SH0020', 'SH0010A', 'SH0010', 'SH0015'])
        ['SH0010', 'SH0015', 'SH0020']
    """
    filtered = filter_sub_shots(shot_names)
    return sort_shots(filtered)
