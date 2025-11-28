"""
Version Updater Module
=======================
Update clips to different versions while maintaining timeline structure.
"""
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field

from .version_manager import VersionManager
from .hiero_wrapper import HieroClip, HieroTrackItem, HIERO_AVAILABLE
from .file_scanner import ProjectScanner


@dataclass
class UpdateResult:
    """Result of version update operation."""
    success: bool
    updated_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    changes: List[Dict[str, str]] = field(default_factory=list)  # {shot, old_version, new_version}


class VersionUpdater:
    """
    Updates track items to different versions.
    """
    
    def __init__(
        self,
        scanner: ProjectScanner,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize VersionUpdater.
        
        Args:
            scanner: ProjectScanner instance for finding versions
            progress_callback: Optional callback(message, current, total)
        """
        self._scanner = scanner
        self._progress_callback = progress_callback
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def get_item_current_version(self, track_item: Any) -> Optional[str]:
        """
        Get current version from track item.
        
        Extracts version from source media path.
        """
        try:
            if HIERO_AVAILABLE:
                source = track_item.source()
                media = source.mediaSource()
                path = media.fileinfos()[0].filename()
            else:
                # Mock mode
                path = track_item.clip._path if hasattr(track_item, 'clip') else ""
            
            # Extract version from path
            import re
            match = re.search(r'[_/](v\d{3,4})', path, re.IGNORECASE)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def _get_new_media_path(
        self, current_path: str, new_version: str, media_type: str = "mov"
    ) -> Optional[str]:
        """
        Generate new media path with different version.
        """
        import re
        # Replace version in path
        new_path = re.sub(r'[_/]v\d{3,4}', f'_{new_version}', current_path, flags=re.IGNORECASE)
        return new_path if new_path != current_path else None
    
    def update_shot_version(
        self, track_item: Any, new_version: str, dept: str = None
    ) -> bool:
        """
        Update a single track item to a new version.
        
        Args:
            track_item: Hiero track item to update
            new_version: Target version string (e.g., "v009")
            dept: Department (optional, for path lookup)
            
        Returns:
            True if updated successfully
        """
        try:
            current_version = self.get_item_current_version(track_item)
            if current_version == new_version:
                return True  # Already at target version
            
            # Get current path and generate new path
            if HIERO_AVAILABLE:
                source = track_item.source()
                current_path = source.mediaSource().fileinfos()[0].filename()
            else:
                current_path = track_item.clip._path if hasattr(track_item, 'clip') else ""
            
            new_path = self._get_new_media_path(current_path, new_version)
            if not new_path:
                return False
            
            # Create new clip and update source
            new_clip = HieroClip.create_clip(new_path)
            return HieroTrackItem.update_item_source(track_item, new_clip)
            
        except Exception as e:
            print(f"[VersionUpdater] Error updating version: {e}")
            return False
    
    def update_all_versions(self, track: Any, new_version: str) -> UpdateResult:
        """
        Update all track items to a specific version.
        
        Args:
            track: Hiero video track
            new_version: Target version for all items
            
        Returns:
            UpdateResult with counts and details
        """
        result = UpdateResult(success=True)
        
        if HIERO_AVAILABLE:
            items = track.items()
        else:
            items = track.items() if hasattr(track, 'items') else []
        
        total = len(items)
        self._report_progress(f"Updating {total} items to {new_version}", 0, total)
        
        for i, item in enumerate(items):
            old_version = self.get_item_current_version(item)
            
            if self.update_shot_version(item, new_version):
                result.updated_count += 1
                result.changes.append({
                    'shot': f"Item {i}",
                    'old_version': old_version or "unknown",
                    'new_version': new_version
                })
            else:
                result.skipped_count += 1
            
            self._report_progress(f"Updated item {i+1}", i + 1, total)
        
        return result
    
    def increment_all_versions(self, track: Any) -> UpdateResult:
        """Increment all track items to next version."""
        result = UpdateResult(success=True)
        items = track.items() if hasattr(track, 'items') else []
        
        for item in items:
            current = self.get_item_current_version(item)
            if current:
                new_ver = VersionManager.increment_version(current)
                if self.update_shot_version(item, new_ver):
                    result.updated_count += 1
                else:
                    result.skipped_count += 1
        
        return result
    
    def decrement_all_versions(self, track: Any) -> UpdateResult:
        """Decrement all track items to previous version."""
        result = UpdateResult(success=True)
        items = track.items() if hasattr(track, 'items') else []
        
        for item in items:
            current = self.get_item_current_version(item)
            if current:
                new_ver = VersionManager.decrement_version(current)
                if new_ver and self.update_shot_version(item, new_ver):
                    result.updated_count += 1
                else:
                    result.skipped_count += 1
        
        return result

