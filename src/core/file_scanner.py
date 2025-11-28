"""
File Scanner Module
====================
Core file system scanning with parallel execution and caching.
"""
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Any

from .cache_manager import CacheManager
from ..utils.path_parser import (
    parse_version_from_filename,
    parse_frame_number,
    get_frame_range,
)
from ..models.models import ScanResult, ShotInfo, DepartmentInfo


# Media file extensions
MOV_EXTENSIONS = {'.mov', '.mp4', '.avi', '.mkv'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.exr', '.dpx', '.tiff', '.tif'}


class ProjectScanner:
    """
    Scans project directory structure for media files.
    
    Supports parallel scanning and caching for performance.
    """
    
    def __init__(
        self,
        project_root: str,
        cache_manager: Optional[CacheManager] = None,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize ProjectScanner.
        
        Args:
            project_root: Root directory of the project
            cache_manager: Optional cache manager instance
            max_workers: Max threads for parallel scanning (default: 4)
            progress_callback: Optional callback(message, current, total)
        """
        self._project_root = Path(project_root)
        self._cache = cache_manager or CacheManager()
        self._max_workers = max_workers
        self._progress_callback = progress_callback
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def _list_dirs(self, path: Path) -> List[str]:
        """List subdirectories in a path."""
        if not path.exists():
            return []
        try:
            return [d.name for d in path.iterdir() if d.is_dir()]
        except PermissionError:
            return []
    
    def _list_files(self, path: Path, extensions: set = None) -> List[str]:
        """List files in a path, optionally filtered by extensions."""
        if not path.exists():
            return []
        try:
            files = [f.name for f in path.iterdir() if f.is_file()]
            if extensions:
                files = [f for f in files if Path(f).suffix.lower() in extensions]
            return sorted(files)
        except PermissionError:
            return []
    
    def scan_episodes(self) -> List[str]:
        """Scan for episode directories."""
        cached = self._cache.get('episodes', str(self._project_root))
        if cached:
            return cached
        
        episodes = [d for d in self._list_dirs(self._project_root) if d.lower().startswith('ep')]
        episodes.sort()
        
        self._cache.set(episodes, 'episodes', str(self._project_root))
        return episodes
    
    def scan_sequences(self, episode: str) -> List[str]:
        """Scan for sequence directories in an episode."""
        cached = self._cache.get('sequences', str(self._project_root), episode)
        if cached:
            return cached
        
        ep_path = self._project_root / episode
        sequences = [d for d in self._list_dirs(ep_path) if d.lower().startswith('sq')]
        sequences.sort()
        
        self._cache.set(sequences, 'sequences', str(self._project_root), episode)
        return sequences
    
    def scan_shots(self, episode: str, sequence: str) -> List[str]:
        """Scan for shot directories in a sequence."""
        cached = self._cache.get('shots', str(self._project_root), episode, sequence)
        if cached:
            return cached
        
        seq_path = self._project_root / episode / sequence
        shots = [d for d in self._list_dirs(seq_path) if d.lower().startswith('sh')]
        shots.sort()
        
        self._cache.set(shots, 'shots', str(self._project_root), episode, sequence)
        return shots
    
    def scan_departments(self, episode: str, sequence: str, shot: str) -> List[str]:
        """Scan for department directories in a shot."""
        cached = self._cache.get('depts', str(self._project_root), episode, sequence, shot)
        if cached:
            return cached
        
        shot_path = self._project_root / episode / sequence / shot
        departments = self._list_dirs(shot_path)
        
        self._cache.set(departments, 'depts', str(self._project_root), episode, sequence, shot)
        return departments
    
    def scan_versions(self, episode: str, sequence: str, shot: str, dept: str) -> List[str]:
        """Scan for version directories in a department."""
        cached = self._cache.get('versions', str(self._project_root), episode, sequence, shot, dept)
        if cached:
            return cached
        
        # Look in output and version subdirectories
        dept_path = self._project_root / episode / sequence / shot / dept
        versions = set()
        
        # Check output folder for MOV files
        output_path = dept_path / "output"
        if output_path.exists():
            for f in self._list_files(output_path, MOV_EXTENSIONS):
                ver = parse_version_from_filename(f)
                if ver:
                    versions.add(ver)
        
        # Check version folder for subfolders
        version_path = dept_path / "version"
        if version_path.exists():
            for d in self._list_dirs(version_path):
                if d.lower().startswith('v'):
                    versions.add(d)
        
        result = sorted(list(versions))
        self._cache.set(result, 'versions', str(self._project_root), episode, sequence, shot, dept)
        return result

    def get_media_files(
        self, episode: str, sequence: str, shot: str, dept: str, version: str
    ) -> Dict[str, Any]:
        """
        Get media files for a specific version.

        Returns:
            Dict with 'mov_files', 'sequence_files', 'frame_range'
        """
        dept_path = self._project_root / episode / sequence / shot / dept
        result = {'mov_files': [], 'sequence_files': [], 'frame_range': None}

        # Check output folder for MOV
        output_path = dept_path / "output"
        if output_path.exists():
            for f in self._list_files(output_path, MOV_EXTENSIONS):
                if version in f:
                    result['mov_files'].append(str(output_path / f))

        # Check version folder for sequences
        version_path = dept_path / "version" / version
        if version_path.exists():
            seq_files = self._list_files(version_path, IMAGE_EXTENSIONS)
            result['sequence_files'] = [str(version_path / f) for f in seq_files]
            result['frame_range'] = get_frame_range(seq_files)

        return result

    def scan_shot_detail(self, episode: str, sequence: str, shot: str) -> Dict[str, Any]:
        """Scan full details for a single shot."""
        departments = self.scan_departments(episode, sequence, shot)
        shot_data = {}

        for dept in departments:
            versions = self.scan_versions(episode, sequence, shot, dept)
            if versions:
                latest = versions[-1]
                media = self.get_media_files(episode, sequence, shot, dept, latest)
                shot_data[dept] = {
                    'versions': versions,
                    'current_version': latest,
                    'mov_files': media['mov_files'],
                    'sequence_files': media['sequence_files'],
                    'frame_range': media['frame_range'],
                    'has_mov': len(media['mov_files']) > 0,
                    'has_sequence': len(media['sequence_files']) > 0,
                }

        return shot_data

    def scan_sequence_parallel(self, episode: str, sequence: str) -> Dict[str, Dict]:
        """Scan all shots in a sequence in parallel."""
        shots = self.scan_shots(episode, sequence)
        result = {}

        self._report_progress(f"Scanning {episode}/{sequence}", 0, len(shots))

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self.scan_shot_detail, episode, sequence, shot): shot
                for shot in shots
            }

            for i, future in enumerate(as_completed(futures)):
                shot = futures[future]
                try:
                    result[shot] = future.result()
                except Exception as e:
                    print(f"[Scanner] Error scanning {shot}: {e}")
                    result[shot] = {}

                self._report_progress(f"Scanned {shot}", i + 1, len(shots))

        return result

    def scan_full(self, episodes: List[str] = None) -> ScanResult:
        """
        Perform full scan of selected episodes.

        Args:
            episodes: List of episodes to scan (default: all)

        Returns:
            ScanResult with full hierarchy
        """
        start_time = time.time()

        if episodes is None:
            episodes = self.scan_episodes()

        data = {}
        total_sequences = 0

        for ep in episodes:
            data[ep] = {}
            sequences = self.scan_sequences(ep)
            total_sequences += len(sequences)

            for seq in sequences:
                self._report_progress(f"Scanning {ep}/{seq}")
                data[ep][seq] = self.scan_sequence_parallel(ep, seq)

        scan_time = time.time() - start_time
        return ScanResult(episodes=data, scan_time=scan_time, cached=False)

    def invalidate_cache(self) -> None:
        """Clear all cached scan results."""
        self._cache.clear()

