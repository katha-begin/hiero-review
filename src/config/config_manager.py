"""
Configuration Manager Module
=============================
Manages user preferences and application state persistence.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default configuration values
DEFAULT_CONFIG = {
    "last_project": "default",
    "last_episode": "",
    "last_sequences": [],
    "cache_enabled": True,
    "recent_projects": [],
    "window_geometry": None,
    "default_department": "comp",
    "default_media_type": "mov",
}


class ConfigManager:
    """
    Manages user configuration and application state.
    
    Config is stored at: ~/.nuke/hiero_review_tool_config.json
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_path: Optional custom config file path
        """
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = Path.home() / ".nuke" / "hiero_review_tool_config.json"
        
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    @property
    def config_path(self) -> Path:
        """Get the config file path."""
        return self._config_path
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ConfigManager] Error loading config: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
        
        # Merge with defaults for any missing keys
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value
        
        return self._config
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError as e:
            print(f"[ConfigManager] Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            save: Whether to save immediately
        """
        self._config[key] = value
        if save:
            self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = DEFAULT_CONFIG.copy()
        self.save_config()
    
    # Convenience methods for common operations
    
    def get_last_project(self) -> str:
        """Get the last used project name."""
        return self.get("last_project", "default")
    
    def set_last_project(self, project: str) -> None:
        """Set the last used project name."""
        self.set("last_project", project)
        self.add_recent_project(project)
    
    def get_recent_projects(self) -> List[str]:
        """Get list of recently used projects."""
        return self.get("recent_projects", [])
    
    def add_recent_project(self, project: str, max_recent: int = 10) -> None:
        """Add a project to the recent projects list."""
        recent = self.get_recent_projects()
        if project in recent:
            recent.remove(project)
        recent.insert(0, project)
        self.set("recent_projects", recent[:max_recent])
    
    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get("cache_enabled", True)
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable caching."""
        self.set("cache_enabled", enabled)


# Global instance (lazy initialization)
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global ConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

