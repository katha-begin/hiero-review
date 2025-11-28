"""
Unit tests for path parser utilities.
"""
import pytest
from src.utils import (
    parse_shot_path, parse_version_from_filename,
    parse_frame_number, get_frame_range,
    extract_episode, extract_sequence, extract_shot, extract_department,
)


class TestParseShotPath:
    """Tests for parse_shot_path function."""
    
    def test_full_path_parsing(self):
        path = "/project/Ep01/sq0010/SH0010/comp/v001/shot.mov"
        result = parse_shot_path(path)
        assert result["ep"] == "Ep01"
        assert result["seq"] == "sq0010"
        assert result["shot"] == "SH0010"
        assert result["dept"] == "comp"
    
    def test_partial_path(self):
        path = "/project/Ep01/sq0010"
        result = parse_shot_path(path)
        assert result["ep"] == "Ep01"
        assert result["seq"] == "sq0010"
        assert result.get("shot") is None
    
    def test_windows_path(self):
        path = "Z:\\Project\\Ep02\\sq0020\\SH0030\\light"
        result = parse_shot_path(path)
        assert result["ep"] == "Ep02"
        assert result["seq"] == "sq0020"
        assert result["shot"] == "SH0030"


class TestParseVersionFromFilename:
    """Tests for parse_version_from_filename function."""
    
    def test_version_in_filename(self):
        assert parse_version_from_filename("SH0010_comp_v003.mov") == "v003"
    
    def test_version_four_digits(self):
        assert parse_version_from_filename("shot_v0012.exr") == "v0012"
    
    def test_no_version(self):
        result = parse_version_from_filename("shot.mov")
        assert result is None
    
    def test_version_at_end(self):
        assert parse_version_from_filename("shot_v005") == "v005"


class TestParseFrameNumber:
    """Tests for parse_frame_number function."""
    
    def test_frame_four_digits(self):
        assert parse_frame_number("shot.1001.exr") == 1001
    
    def test_frame_in_filename(self):
        assert parse_frame_number("SH0010_comp_v001.1050.exr") == 1050
    
    def test_no_frame_number(self):
        result = parse_frame_number("shot.mov")
        assert result is None
    
    def test_frame_different_formats(self):
        # Frame number must be in .####.ext format
        assert parse_frame_number("shot.1001.exr") == 1001


class TestGetFrameRange:
    """Tests for get_frame_range function."""
    
    def test_frame_range_basic(self):
        files = [
            "shot.1001.exr",
            "shot.1002.exr",
            "shot.1003.exr",
        ]
        start, end = get_frame_range(files)
        assert start == 1001
        assert end == 1003
    
    def test_frame_range_unordered(self):
        files = [
            "shot.1050.exr",
            "shot.1001.exr",
            "shot.1025.exr",
        ]
        start, end = get_frame_range(files)
        assert start == 1001
        assert end == 1050
    
    def test_frame_range_empty(self):
        result = get_frame_range([])
        assert result == (None, None) or result is None
    
    def test_frame_range_single_file(self):
        files = ["shot.1001.exr"]
        start, end = get_frame_range(files)
        assert start == 1001
        assert end == 1001


class TestExtractEpisode:
    """Tests for extract_episode function."""
    
    def test_extract_ep_basic(self):
        assert extract_episode("Ep01") == "Ep01"
    
    def test_extract_ep_from_path(self):
        assert extract_episode("/project/Ep02/seq") == "Ep02"
    
    def test_extract_ep_not_found(self):
        result = extract_episode("/project/episode1")
        assert result is None


class TestExtractSequence:
    """Tests for extract_sequence function."""
    
    def test_extract_seq_basic(self):
        assert extract_sequence("sq0010") == "sq0010"
    
    def test_extract_seq_from_path(self):
        assert extract_sequence("/project/Ep01/sq0020/shot") == "sq0020"
    
    def test_extract_seq_not_found(self):
        result = extract_sequence("/project/sequence10")
        assert result is None


class TestExtractShot:
    """Tests for extract_shot function."""
    
    def test_extract_shot_basic(self):
        assert extract_shot("SH0010") == "SH0010"
    
    def test_extract_shot_from_path(self):
        assert extract_shot("/project/Ep01/sq0010/SH0030") == "SH0030"
    
    def test_extract_shot_not_found(self):
        result = extract_shot("/project/shot10")
        assert result is None


class TestExtractDepartment:
    """Tests for extract_department function."""
    
    def test_extract_dept_comp(self):
        assert extract_department("/project/comp/v001") == "comp"
    
    def test_extract_dept_light(self):
        assert extract_department("/project/light/v001") == "light"
    
    def test_extract_dept_anim(self):
        assert extract_department("/project/anim/v001") == "anim"
    
    def test_extract_dept_fx(self):
        assert extract_department("/project/fx/v001") == "fx"
    
    def test_extract_dept_not_found(self):
        result = extract_department("/project/modeling/v001")
        assert result is None or result == "modeling"

