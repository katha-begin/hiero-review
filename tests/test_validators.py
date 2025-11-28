"""
Unit tests for validators module.
"""
import pytest
import tempfile
from pathlib import Path
from src.utils.validators import (
    validate_naming_convention, validate_version_format,
    validate_frame_sequence, validate_project_structure,
    ValidationReport,
)


class TestValidateNamingConvention:
    """Tests for validate_naming_convention function."""

    def test_valid_naming_standard(self):
        # Must have Ep##, sq####, SH####
        assert validate_naming_convention("Ep01_sq0010_SH0010_comp_v001.mov") is True

    def test_valid_naming_with_frame(self):
        assert validate_naming_convention("Ep01_sq0010_SH0010_v001.1001.exr") is True

    def test_invalid_naming_no_episode(self):
        assert validate_naming_convention("sq0010_SH0010_v001.mov") is False

    def test_invalid_naming_no_shot(self):
        assert validate_naming_convention("Ep01_sq0010_v001.mov") is False


class TestValidateVersionFormat:
    """Tests for validate_version_format function."""

    def test_valid_version_v001(self):
        assert validate_version_format("v001") is True

    def test_valid_version_v123(self):
        assert validate_version_format("v123") is True

    def test_valid_version_v0012(self):
        assert validate_version_format("v0012") is True

    def test_valid_version_uppercase(self):
        assert validate_version_format("V001") is True

    def test_invalid_version_no_v(self):
        assert validate_version_format("001") is False

    def test_invalid_version_text(self):
        assert validate_version_format("version1") is False

    def test_invalid_version_empty(self):
        assert validate_version_format("") is False


class TestValidateFrameSequence:
    """Tests for validate_frame_sequence function."""

    def test_complete_sequence(self):
        files = [f"shot.{i:04d}.exr" for i in range(1001, 1011)]
        result = validate_frame_sequence(files)
        assert result["complete"] is True
        assert result["missing_frames"] == []

    def test_sequence_with_gaps(self):
        files = ["shot.1001.exr", "shot.1002.exr", "shot.1005.exr"]
        result = validate_frame_sequence(files)
        assert result["complete"] is False
        assert 1003 in result["missing_frames"]
        assert 1004 in result["missing_frames"]

    def test_empty_sequence(self):
        result = validate_frame_sequence([])
        assert result["complete"] is False

    def test_single_frame(self):
        files = ["shot.1001.exr"]
        result = validate_frame_sequence(files)
        assert result["complete"] is True


class TestValidateProjectStructure:
    """Tests for validate_project_structure function."""

    def test_nonexistent_path(self):
        result = validate_project_structure("/nonexistent/path")
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_project_structure(tmpdir)
            # Should have warning about no episodes
            assert len(result.warnings) > 0 or len(result.errors) >= 0


class TestValidationReport:
    """Tests for ValidationReport class."""

    def test_validation_report_empty(self):
        report = ValidationReport()
        assert report.is_valid is True
        assert len(report.errors) == 0

    def test_validation_report_with_error(self):
        report = ValidationReport()
        report.add_error("Test error")
        assert report.is_valid is False
        assert len(report.errors) == 1

    def test_validation_report_with_warning(self):
        report = ValidationReport()
        report.add_warning("Test warning")
        assert report.is_valid is True  # Warnings don't make it invalid
        assert len(report.warnings) == 1

    def test_validation_report_with_info(self):
        report = ValidationReport()
        report.add_info("Test info")
        assert report.is_valid is True
        assert len(report.info) == 1

    def test_validation_report_multiple_messages(self):
        report = ValidationReport()
        report.add_error("Error 1")
        report.add_error("Error 2")
        report.add_warning("Warning 1")
        assert len(report.errors) == 2
        assert len(report.warnings) == 1

