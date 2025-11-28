"""
Department Switcher Module
===========================
Switch all shots in a timeline to a different department output.
"""
import re
from typing import List, Dict, Optional, Any, Callable, Set
from dataclasses import dataclass, field

from .hiero_wrapper import HieroClip, HieroTrackItem, HIERO_AVAILABLE
from .file_scanner import ProjectScanner
from .version_manager import VersionManager


@dataclass
class SwitchResult:
    """Result of department switch operation."""
    success: bool
    success_count: int = 0
    skipped_shots: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DepartmentSwitcher:
    """
    Switches track items to different department outputs.
    """
    
    # Known departments
    DEPARTMENTS = ['comp', 'light', 'lighting', 'anim', 'animation', 'fx', 'efx', 'roto', 'paint']
    
    def __init__(
        self,
        scanner: ProjectScanner,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize DepartmentSwitcher.
        
        Args:
            scanner: ProjectScanner instance
            progress_callback: Optional callback(message, current, total)
        """
        self._scanner = scanner
        self._progress_callback = progress_callback
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def get_current_department(self, track_item: Any) -> Optional[str]:
        """Extract current department from track item's media path."""
        try:
            if HIERO_AVAILABLE:
                source = track_item.source()
                path = source.mediaSource().fileinfos()[0].filename()
            else:
                path = track_item.clip._path if hasattr(track_item, 'clip') else ""
            
            path_lower = path.lower()
            for dept in self.DEPARTMENTS:
                if f'/{dept}/' in path_lower:
                    return dept
            return None
        except Exception:
            return None
    
    def get_available_departments(self, track: Any) -> Set[str]:
        """Get all departments available across track items."""
        departments = set()
        items = track.items() if hasattr(track, 'items') else []
        
        for item in items:
            dept = self.get_current_department(item)
            if dept:
                departments.add(dept)
        
        return departments
    
    def _find_department_media(
        self, current_path: str, new_dept: str, version: str = None
    ) -> Optional[str]:
        """
        Find media path for a different department.
        
        Replaces department in path and optionally version.
        """
        # Replace department in path
        path_lower = current_path.lower()
        new_path = current_path
        
        for dept in self.DEPARTMENTS:
            pattern = f'/{dept}/'
            if pattern in path_lower:
                # Find the actual case in path and replace
                idx = path_lower.index(pattern)
                actual = current_path[idx+1:idx+1+len(dept)]
                new_path = current_path[:idx+1] + new_dept + current_path[idx+1+len(dept):]
                break
        
        return new_path if new_path != current_path else None
    
    def switch_department(
        self, track: Any, new_department: str, maintain_version: bool = True
    ) -> SwitchResult:
        """
        Switch all track items to a different department.
        
        Args:
            track: Hiero video track
            new_department: Target department name
            maintain_version: Keep same version when switching
            
        Returns:
            SwitchResult with counts and details
        """
        result = SwitchResult(success=True)
        items = track.items() if hasattr(track, 'items') else []
        
        total = len(items)
        self._report_progress(f"Switching {total} items to {new_department}", 0, total)
        
        for i, item in enumerate(items):
            try:
                current_dept = self.get_current_department(item)
                if current_dept == new_department:
                    result.success_count += 1
                    continue
                
                # Get current path
                if HIERO_AVAILABLE:
                    source = item.source()
                    current_path = source.mediaSource().fileinfos()[0].filename()
                else:
                    current_path = item.clip._path if hasattr(item, 'clip') else ""
                
                # Find new department media
                new_path = self._find_department_media(current_path, new_department)
                
                if not new_path:
                    result.skipped_shots.append(f"Item {i}: No path for {new_department}")
                    continue
                
                # Create new clip and update
                new_clip = HieroClip.create_clip(new_path)
                if HieroTrackItem.update_item_source(item, new_clip):
                    result.success_count += 1
                    HieroTrackItem.set_metadata(item, "department", new_department)
                else:
                    result.errors.append(f"Item {i}: Failed to update source")
                
            except Exception as e:
                result.errors.append(f"Item {i}: {str(e)}")
            
            self._report_progress(f"Processed item {i+1}", i + 1, total)
        
        result.success = len(result.errors) == 0
        return result

