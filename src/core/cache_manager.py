"""
Cache Manager Module
=====================
Two-tier caching system for file system scan results.
L1: Memory cache (60-second TTL)
L2: Disk cache (1-hour TTL)
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Represents a cache entry with data and metadata."""
    data: Any
    timestamp: float
    ttl: int
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class CacheManager:
    """
    Two-tier cache manager.
    
    L1 (Memory): Fast, short-lived (default 60s TTL)
    L2 (Disk): Slower, longer-lived (default 1hr TTL)
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        memory_ttl: int = 60,
        disk_ttl: int = 3600,
        enabled: bool = True
    ):
        """
        Initialize CacheManager.
        
        Args:
            cache_dir: Directory for disk cache (default: ~/.nuke/hiero_review_cache)
            memory_ttl: Memory cache TTL in seconds (default: 60)
            disk_ttl: Disk cache TTL in seconds (default: 3600)
            enabled: Whether caching is enabled
        """
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_dir = cache_dir or Path.home() / ".nuke" / "hiero_review_cache"
        self._memory_ttl = memory_ttl
        self._disk_ttl = disk_ttl
        self._enabled = enabled
        
        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _make_key(self, *key_parts) -> str:
        """Create a cache key from parts."""
        key_str = ":".join(str(p) for p in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk cache file path for a key."""
        return self._cache_dir / f"{key}.json"
    
    def get(self, *key_parts) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            *key_parts: Key components (e.g., 'episodes', 'Ep01', 'sq0030')
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self._enabled:
            return None
        
        key = self._make_key(*key_parts)
        
        # Try L1 (memory) first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired():
                return entry.data
            else:
                del self._memory_cache[key]
        
        # Try L2 (disk)
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            try:
                with open(disk_path, 'r', encoding='utf-8') as f:
                    disk_data = json.load(f)
                
                entry = CacheEntry(
                    data=disk_data['data'],
                    timestamp=disk_data['timestamp'],
                    ttl=self._disk_ttl
                )
                
                if not entry.is_expired():
                    # Promote to L1
                    self._memory_cache[key] = CacheEntry(
                        data=entry.data,
                        timestamp=time.time(),
                        ttl=self._memory_ttl
                    )
                    return entry.data
                else:
                    disk_path.unlink()  # Remove expired cache
            except (json.JSONDecodeError, IOError, KeyError):
                pass
        
        return None
    
    def set(self, value: Any, *key_parts) -> None:
        """
        Store value in cache (both L1 and L2).
        
        Args:
            value: Value to cache
            *key_parts: Key components
        """
        if not self._enabled:
            return
        
        key = self._make_key(*key_parts)
        now = time.time()
        
        # Store in L1 (memory)
        self._memory_cache[key] = CacheEntry(data=value, timestamp=now, ttl=self._memory_ttl)
        
        # Store in L2 (disk)
        disk_path = self._get_disk_path(key)
        try:
            with open(disk_path, 'w', encoding='utf-8') as f:
                json.dump({'data': value, 'timestamp': now}, f)
        except IOError as e:
            print(f"[CacheManager] Failed to write disk cache: {e}")
    
    def invalidate(self, *key_parts) -> None:
        """Remove specific cache entry."""
        key = self._make_key(*key_parts)
        
        # Remove from L1
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Remove from L2
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            disk_path.unlink()
    
    def clear(self) -> None:
        """Clear all cache (both L1 and L2)."""
        self._memory_cache.clear()
        
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except IOError:
                    pass
    
    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable caching."""
        self._enabled = value

