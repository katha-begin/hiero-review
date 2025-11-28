"""
Unit tests for SequenceHandler module.
"""
import pytest
import tempfile
from pathlib import Path
from src.core.sequence_handler import SequenceHandler, SequenceInfo, ValidationResult


class TestSequenceHandlerInit:
    """Tests for SequenceHandler initialization."""
    
    def test_create_handler(self):
        handler = SequenceHandler()
        assert handler is not None


class TestValidateSequence:
    """Tests for validate_sequence method."""
    
    def test_validate_complete_sequence(self):
        handler = SequenceHandler()
        files = [f"shot.{i:04d}.exr" for i in range(1001, 1011)]
        result = handler.validate_sequence(files)
        assert result.is_valid is True
        assert result.frame_count == 10
        assert result.missing_frames == []
    
    def test_validate_incomplete_sequence(self):
        handler = SequenceHandler()
        files = ["shot.1001.exr", "shot.1002.exr", "shot.1005.exr"]
        result = handler.validate_sequence(files)
        assert 1003 in result.missing_frames
        assert 1004 in result.missing_frames
    
    def test_validate_empty_sequence(self):
        handler = SequenceHandler()
        result = handler.validate_sequence([])
        assert result.is_valid is False


class TestGetFrameRange:
    """Tests for get_frame_range method."""
    
    def test_frame_range_basic(self):
        handler = SequenceHandler()
        files = [f"shot.{i:04d}.exr" for i in range(1001, 1011)]
        result = handler.get_frame_range(files)
        assert result == (1001, 1010)
    
    def test_frame_range_unordered(self):
        handler = SequenceHandler()
        files = ["shot.1005.exr", "shot.1001.exr", "shot.1010.exr"]
        result = handler.get_frame_range(files)
        assert result == (1001, 1010)
    
    def test_frame_range_empty(self):
        handler = SequenceHandler()
        result = handler.get_frame_range([])
        assert result is None


class TestDetectMissingFrames:
    """Tests for detect_missing_frames method."""
    
    def test_no_missing_frames(self):
        handler = SequenceHandler()
        files = [f"shot.{i:04d}.exr" for i in range(1001, 1011)]
        missing = handler.detect_missing_frames(files)
        assert missing == []
    
    def test_with_gap(self):
        handler = SequenceHandler()
        files = ["shot.1001.exr", "shot.1002.exr", "shot.1005.exr"]
        missing = handler.detect_missing_frames(files)
        assert 1003 in missing
        assert 1004 in missing


class TestSequenceInfo:
    """Tests for SequenceInfo dataclass."""
    
    def test_sequence_info_creation(self):
        info = SequenceInfo(
            pattern="shot.####.exr",
            directory="/project",
            base_name="shot",
            extension=".exr",
            start_frame=1001,
            end_frame=1100,
            frame_count=100
        )
        assert info.pattern == "shot.####.exr"
        assert info.start_frame == 1001
    
    def test_is_complete_true(self):
        info = SequenceInfo(
            pattern="shot.####.exr",
            directory="/project",
            base_name="shot",
            extension=".exr",
            start_frame=1001,
            end_frame=1010,
            frame_count=10,
            missing_frames=[]
        )
        assert info.is_complete is True
    
    def test_is_complete_false(self):
        info = SequenceInfo(
            pattern="shot.####.exr",
            directory="/project",
            base_name="shot",
            extension=".exr",
            start_frame=1001,
            end_frame=1010,
            frame_count=8,
            missing_frames=[1003, 1004]
        )
        assert info.is_complete is False
    
    def test_hiero_pattern(self):
        info = SequenceInfo(
            pattern="shot.####.exr",
            directory="/project",
            base_name="shot",
            extension=".exr",
            start_frame=1001,
            end_frame=1010,
            frame_count=10,
            padding=4
        )
        assert "####" in info.hiero_pattern
    
    def test_printf_pattern(self):
        info = SequenceInfo(
            pattern="shot.####.exr",
            directory="/project",
            base_name="shot",
            extension=".exr",
            start_frame=1001,
            end_frame=1010,
            frame_count=10,
            padding=4
        )
        assert "%04d" in info.printf_pattern


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        result = ValidationResult(is_valid=True, frame_count=100)
        assert result.is_valid is True
        assert result.frame_count == 100
    
    def test_validation_result_with_errors(self):
        result = ValidationResult(
            is_valid=False,
            frame_count=0,
            errors=["No frames found"]
        )
        assert result.is_valid is False
        assert len(result.errors) == 1

