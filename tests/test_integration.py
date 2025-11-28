"""
Integration tests for Hiero Review Tool.
Tests end-to-end workflows with mock Hiero environment.
"""
import pytest
import tempfile
import json
from pathlib import Path

from src.models import ProjectConfig, MediaPaths, ShotInfo, DepartmentInfo
from src.core import (
    CacheManager, ProjectScanner, VersionManager,
    TimelineBuilder, SequenceHandler
)
from src.config import ConfigManager
from src.utils.path_parser import parse_shot_path, extract_episode, extract_sequence


class TestProjectWorkflow:
    """Test complete project workflow from config to timeline."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create project structure
            ep01 = root / "Ep01"
            sq0010 = ep01 / "sq0010"
            sh0010 = sq0010 / "SH0010"
            comp = sh0010 / "comp"
            v001 = comp / "v001"
            v002 = comp / "v002"
            
            for d in [v001, v002]:
                d.mkdir(parents=True)
                # Create mock media files
                (d / "Ep01_sq0010_SH0010_comp.mov").touch()
            
            yield root
    
    def test_config_loading(self, temp_project):
        """Test loading project configuration."""
        config = ProjectConfig(
            project_name="TestProject",
            project_root=str(temp_project),
            media_paths=MediaPaths()
        )
        assert config.project_name == "TestProject"
        assert config.project_root == str(temp_project)
    
    def test_file_scanning(self, temp_project):
        """Test scanning project files."""
        scanner = ProjectScanner(str(temp_project))
        episodes = scanner.scan_episodes()

        assert episodes is not None
        assert "Ep01" in episodes
    
    def test_version_detection(self, temp_project):
        """Test version detection in project."""
        versions = ["v001", "v002", "v003"]
        sorted_vers = VersionManager.sort_versions(versions)
        latest = VersionManager.get_latest_version(versions)
        
        assert sorted_vers == ["v001", "v002", "v003"]
        assert latest == "v003"


class TestCacheIntegration:
    """Test cache manager integration."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache manager instance."""
        return CacheManager()
    
    def test_cache_scan_results(self, cache):
        """Test caching scan results."""
        scan_data = {
            "episodes": {"Ep01": {"sequences": ["sq0010"]}},
            "scan_time": 1.5
        }

        # CacheManager.set takes value first, then key parts
        cache.set(scan_data, "project_scan")
        retrieved = cache.get("project_scan")

        assert retrieved is not None
        assert retrieved["episodes"]["Ep01"]["sequences"] == ["sq0010"]
    
    def test_cache_invalidation(self, cache):
        """Test cache invalidation."""
        cache.set("test_key", "test_value")
        cache.invalidate("test_key")
        
        assert cache.get("test_key") is None


class TestTimelineBuilding:
    """Test timeline building workflow."""

    @pytest.fixture
    def temp_project_for_timeline(self):
        """Create a temporary project for timeline tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Ep01" / "sq0010" / "SH0010" / "comp" / "v001").mkdir(parents=True)
            yield root

    def test_timeline_builder_init(self, temp_project_for_timeline):
        """Test TimelineBuilder initialization."""
        scanner = ProjectScanner(str(temp_project_for_timeline))
        builder = TimelineBuilder(scanner)
        assert builder is not None
    
    def test_shot_info_creation(self):
        """Test creating shot info for timeline."""
        shot = ShotInfo(
            episode="Ep01",
            sequence="sq0010",
            shot="SH0010",
            departments={
                "comp": DepartmentInfo(
                    name="comp",
                    versions=["v001", "v002"],
                    current_version="v002"
                )
            }
        )
        
        assert shot.full_name == "Ep01_sq0010_SH0010"
        assert shot.departments["comp"].current_version == "v002"


class TestPathParsing:
    """Test path parsing integration."""
    
    def test_parse_full_path(self):
        """Test parsing a complete project path."""
        path = "/project/Ep01/sq0010/SH0010/comp/v001/render.mov"
        
        ep = extract_episode(path)
        seq = extract_sequence(path)
        
        assert ep == "Ep01"
        assert seq == "sq0010"
    
    def test_parse_shot_path_dict(self):
        """Test parse_shot_path returns dict."""
        path = "/project/Ep01/sq0010/SH0010/comp/v001/render.mov"
        result = parse_shot_path(path)

        assert isinstance(result, dict)
        # Keys are 'ep', 'seq', 'shot', 'dept'
        assert result.get("ep") == "Ep01"
        assert result.get("seq") == "sq0010"
        assert result.get("shot") == "SH0010"


class TestConfigManagerIntegration:
    """Test config manager integration."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a config manager with temp file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            yield ConfigManager(str(config_path))
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading configuration."""
        config_manager.set("test_setting", "test_value")
        config_manager.save_config()
        
        # Reload
        config_manager.load_config()
        assert config_manager.get("test_setting") == "test_value"

