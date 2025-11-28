"""
Version Manager Module
=======================
Version detection, sorting, comparison, and manipulation.
"""
import re
from typing import List, Optional, Tuple


class VersionManager:
    """
    Manages version parsing, sorting, and manipulation.
    
    Supports formats: v001, v01, v1, V001 (case-insensitive)
    """
    
    # Pattern to extract version number
    VERSION_RE = re.compile(r'^[vV](\d+)$')
    
    @staticmethod
    def parse_version(version_str: str) -> Optional[int]:
        """
        Parse version string to integer.
        
        Args:
            version_str: Version string (e.g., "v009", "V001")
            
        Returns:
            Version number as int, or None if invalid
            
        Example:
            >>> VersionManager.parse_version("v009")
            9
        """
        match = VersionManager.VERSION_RE.match(version_str.strip())
        if match:
            return int(match.group(1))
        return None
    
    @staticmethod
    def format_version(version_num: int, padding: int = 3) -> str:
        """
        Format version number to string.
        
        Args:
            version_num: Version as integer
            padding: Number of digits (default: 3)
            
        Returns:
            Formatted version string
            
        Example:
            >>> VersionManager.format_version(9)
            'v009'
        """
        return f"v{version_num:0{padding}d}"
    
    @staticmethod
    def sort_versions(versions: List[str]) -> List[str]:
        """
        Sort version strings numerically.
        
        Args:
            versions: List of version strings
            
        Returns:
            Sorted list of versions
            
        Example:
            >>> VersionManager.sort_versions(['v010', 'v002', 'v001'])
            ['v001', 'v002', 'v010']
        """
        def sort_key(v):
            num = VersionManager.parse_version(v)
            return num if num is not None else float('inf')
        
        return sorted(versions, key=sort_key)
    
    @staticmethod
    def get_latest_version(versions: List[str]) -> Optional[str]:
        """
        Get the highest version from a list.
        
        Args:
            versions: List of version strings
            
        Returns:
            Highest version string, or None if empty
        """
        if not versions:
            return None
        sorted_versions = VersionManager.sort_versions(versions)
        return sorted_versions[-1] if sorted_versions else None
    
    @staticmethod
    def get_earliest_version(versions: List[str]) -> Optional[str]:
        """Get the lowest version from a list."""
        if not versions:
            return None
        sorted_versions = VersionManager.sort_versions(versions)
        return sorted_versions[0] if sorted_versions else None
    
    @staticmethod
    def increment_version(current: str, padding: int = 3) -> str:
        """
        Increment version by one.
        
        Args:
            current: Current version string
            padding: Number of digits for output
            
        Returns:
            Next version string
        """
        num = VersionManager.parse_version(current)
        if num is None:
            return VersionManager.format_version(1, padding)
        return VersionManager.format_version(num + 1, padding)
    
    @staticmethod
    def decrement_version(current: str, padding: int = 3) -> Optional[str]:
        """
        Decrement version by one.
        
        Args:
            current: Current version string
            padding: Number of digits for output
            
        Returns:
            Previous version string, or None if already at v001
        """
        num = VersionManager.parse_version(current)
        if num is None or num <= 1:
            return None
        return VersionManager.format_version(num - 1, padding)
    
    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """
        Compare two versions.
        
        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        num1 = VersionManager.parse_version(v1) or 0
        num2 = VersionManager.parse_version(v2) or 0
        
        if num1 < num2:
            return -1
        elif num1 > num2:
            return 1
        return 0
    
    @staticmethod
    def get_version_range(start: str, end: str, padding: int = 3) -> List[str]:
        """
        Generate list of versions in a range.
        
        Args:
            start: Start version (inclusive)
            end: End version (inclusive)
            padding: Number of digits
            
        Returns:
            List of version strings in range
        """
        start_num = VersionManager.parse_version(start) or 1
        end_num = VersionManager.parse_version(end) or 1
        
        if start_num > end_num:
            start_num, end_num = end_num, start_num
        
        return [VersionManager.format_version(i, padding) for i in range(start_num, end_num + 1)]

