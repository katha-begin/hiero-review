"""
Unit tests for VersionManager.
"""
import pytest
from src.core import VersionManager


class TestVersionParsing:
    """Tests for version string parsing."""

    def test_parse_version_v001(self):
        assert VersionManager.parse_version("v001") == 1

    def test_parse_version_v009(self):
        assert VersionManager.parse_version("v009") == 9

    def test_parse_version_v100(self):
        assert VersionManager.parse_version("v100") == 100

    def test_parse_version_four_digits(self):
        assert VersionManager.parse_version("v0012") == 12

    def test_parse_version_invalid(self):
        assert VersionManager.parse_version("invalid") is None

    def test_parse_version_uppercase(self):
        assert VersionManager.parse_version("V001") == 1


class TestVersionFormatting:
    """Tests for version string formatting."""

    def test_format_version_single_digit(self):
        assert VersionManager.format_version(1) == "v001"

    def test_format_version_double_digit(self):
        assert VersionManager.format_version(12) == "v012"

    def test_format_version_triple_digit(self):
        assert VersionManager.format_version(123) == "v123"

    def test_format_version_four_digits(self):
        assert VersionManager.format_version(1234, 4) == "v1234"


class TestVersionSorting:
    """Tests for version sorting."""

    def test_sort_versions_basic(self):
        versions = ["v003", "v001", "v002"]
        sorted_vers = VersionManager.sort_versions(versions)
        assert sorted_vers == ["v001", "v002", "v003"]

    def test_sort_versions_mixed_digits(self):
        versions = ["v010", "v001", "v100", "v009"]
        sorted_vers = VersionManager.sort_versions(versions)
        assert sorted_vers == ["v001", "v009", "v010", "v100"]

    def test_sort_versions_empty(self):
        assert VersionManager.sort_versions([]) == []

    def test_sort_versions_single(self):
        assert VersionManager.sort_versions(["v001"]) == ["v001"]


class TestVersionComparison:
    """Tests for version comparison."""

    def test_compare_versions_less_than(self):
        assert VersionManager.compare_versions("v001", "v002") < 0

    def test_compare_versions_greater_than(self):
        assert VersionManager.compare_versions("v010", "v002") > 0

    def test_compare_versions_equal(self):
        assert VersionManager.compare_versions("v005", "v005") == 0


class TestVersionNavigation:
    """Tests for version increment/decrement."""

    def test_increment_version(self):
        assert VersionManager.increment_version("v001") == "v002"

    def test_increment_version_high(self):
        assert VersionManager.increment_version("v099") == "v100"

    def test_decrement_version(self):
        assert VersionManager.decrement_version("v005") == "v004"

    def test_decrement_version_min(self):
        result = VersionManager.decrement_version("v001")
        assert result is None


class TestLatestVersion:
    """Tests for getting latest version."""

    def test_get_latest_version(self):
        versions = ["v001", "v003", "v002"]
        assert VersionManager.get_latest_version(versions) == "v003"

    def test_get_latest_version_single(self):
        assert VersionManager.get_latest_version(["v005"]) == "v005"

    def test_get_latest_version_empty(self):
        assert VersionManager.get_latest_version([]) is None


class TestVersionRange:
    """Tests for version range generation."""

    def test_get_version_range(self):
        result = VersionManager.get_version_range("v001", "v003")
        assert result == ["v001", "v002", "v003"]

    def test_get_version_range_reversed(self):
        result = VersionManager.get_version_range("v003", "v001")
        assert result == ["v001", "v002", "v003"]

