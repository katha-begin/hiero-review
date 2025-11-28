"""
Unit tests for ConfigManager.
"""
import pytest
import os
import tempfile
import json
from pathlib import Path
from src.config import ConfigManager


class TestConfigManagerBasic:
    """Tests for basic ConfigManager operations."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create ConfigManager with temp config file."""
        config_path = tmp_path / "test_config.json"
        return ConfigManager(config_path=str(config_path))
    
    def test_get_default_value(self, config):
        result = config.get("nonexistent", default="default_val")
        assert result == "default_val"
    
    def test_set_and_get(self, config):
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
    
    def test_set_without_save(self, config):
        config.set("temp_key", "temp_value", save=False)
        assert config.get("temp_key") == "temp_value"
    
    def test_set_with_save(self, config):
        config.set("saved_key", "saved_value", save=True)
        # Reload config
        config.load_config()
        assert config.get("saved_key") == "saved_value"


class TestConfigManagerPersistence:
    """Tests for config persistence."""
    
    def test_save_and_load(self, tmp_path):
        config_path = tmp_path / "persist_config.json"
        
        # Create and save config
        config1 = ConfigManager(config_path=str(config_path))
        config1.set("persist_key", "persist_value")
        config1.save_config()
        
        # Load in new instance
        config2 = ConfigManager(config_path=str(config_path))
        assert config2.get("persist_key") == "persist_value"
    
    def test_config_file_created(self, tmp_path):
        config_path = tmp_path / "new_config.json"
        config = ConfigManager(config_path=str(config_path))
        config.set("key", "value")
        config.save_config()
        
        assert config_path.exists()


class TestConfigManagerRecentProjects:
    """Tests for recent projects functionality."""
    
    @pytest.fixture
    def config(self, tmp_path):
        config_path = tmp_path / "recent_config.json"
        return ConfigManager(config_path=str(config_path))
    
    def test_add_recent_project(self, config):
        config.add_recent_project("/project/path1")
        recent = config.get("recent_projects", default=[])
        assert "/project/path1" in recent
    
    def test_add_multiple_recent_projects(self, config):
        config.add_recent_project("/project/path1")
        config.add_recent_project("/project/path2")
        recent = config.get("recent_projects", default=[])
        assert len(recent) >= 2
    
    def test_get_last_project(self, config):
        config.set_last_project("TestProject")
        last = config.get_last_project()
        assert last == "TestProject"

    def test_get_last_project_default(self, config):
        # Default value is "default"
        last = config.get_last_project()
        assert last == "default"
    
    def test_recent_projects_no_duplicates(self, config):
        config.add_recent_project("/project/path1")
        config.add_recent_project("/project/path1")
        recent = config.get("recent_projects", default=[])
        count = recent.count("/project/path1")
        assert count == 1


class TestConfigManagerCacheSettings:
    """Tests for cache-related settings."""
    
    @pytest.fixture
    def config(self, tmp_path):
        config_path = tmp_path / "cache_config.json"
        return ConfigManager(config_path=str(config_path))
    
    def test_cache_enabled_default(self, config):
        assert config.is_cache_enabled() is True
    
    def test_disable_cache(self, config):
        config.set("cache_enabled", False)
        assert config.is_cache_enabled() is False
    
    def test_enable_cache(self, config):
        config.set("cache_enabled", False)
        config.set("cache_enabled", True)
        assert config.is_cache_enabled() is True


class TestConfigManagerDefaults:
    """Tests for default configuration values."""
    
    @pytest.fixture
    def config(self, tmp_path):
        config_path = tmp_path / "defaults_config.json"
        return ConfigManager(config_path=str(config_path))
    
    def test_default_department(self, config):
        dept = config.get("default_department", default="comp")
        assert dept == "comp"
    
    def test_default_media_type(self, config):
        media = config.get("default_media_type", default="mov")
        assert media == "mov"
    
    def test_default_fps(self, config):
        fps = config.get("default_fps", default=24.0)
        assert fps == 24.0


class TestConfigManagerComplexValues:
    """Tests for complex configuration values."""
    
    @pytest.fixture
    def config(self, tmp_path):
        config_path = tmp_path / "complex_config.json"
        return ConfigManager(config_path=str(config_path))
    
    def test_set_dict_value(self, config):
        patterns = {"episode": r"Ep\d{2}", "sequence": r"sq\d{4}"}
        config.set("patterns", patterns)
        result = config.get("patterns")
        assert result["episode"] == r"Ep\d{2}"
    
    def test_set_list_value(self, config):
        departments = ["comp", "light", "anim"]
        config.set("departments", departments)
        result = config.get("departments")
        assert "comp" in result

