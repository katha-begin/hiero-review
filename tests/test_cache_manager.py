"""
Unit tests for CacheManager.
"""
import pytest
import time
from src.core import CacheManager


class TestCacheBasicOperations:
    """Tests for basic cache operations."""
    
    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance."""
        cm = CacheManager()
        cm.clear()
        return cm
    
    def test_set_and_get(self, cache):
        cache.set("test_value", "test", "key")
        result = cache.get("test", "key")
        assert result == "test_value"
    
    def test_get_nonexistent(self, cache):
        result = cache.get("nonexistent", "key")
        assert result is None
    
    def test_set_complex_value(self, cache):
        value = {"name": "test", "data": [1, 2, 3]}
        cache.set(value, "complex", "key")
        result = cache.get("complex", "key")
        assert result == value
    
    def test_multiple_keys(self, cache):
        cache.set("value1", "key1")
        cache.set("value2", "key2")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
    
    def test_nested_keys(self, cache):
        cache.set("nested_value", "level1", "level2", "level3")
        result = cache.get("level1", "level2", "level3")
        assert result == "nested_value"


class TestCacheInvalidation:
    """Tests for cache invalidation."""
    
    @pytest.fixture
    def cache(self):
        cm = CacheManager()
        cm.clear()
        return cm
    
    def test_invalidate_specific_key(self, cache):
        cache.set("value", "key")
        cache.invalidate("key")
        assert cache.get("key") is None
    
    def test_invalidate_nested_key(self, cache):
        cache.set("value", "a", "b", "c")
        cache.invalidate("a", "b", "c")
        assert cache.get("a", "b", "c") is None
    
    def test_clear_all(self, cache):
        cache.set("value1", "key1")
        cache.set("value2", "key2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheOverwrite:
    """Tests for cache value overwriting."""
    
    @pytest.fixture
    def cache(self):
        cm = CacheManager()
        cm.clear()
        return cm
    
    def test_overwrite_value(self, cache):
        cache.set("original", "key")
        cache.set("updated", "key")
        assert cache.get("key") == "updated"
    
    def test_overwrite_with_different_type(self, cache):
        cache.set("string", "key")
        cache.set(123, "key")
        assert cache.get("key") == 123


class TestCacheDataTypes:
    """Tests for different data types in cache."""
    
    @pytest.fixture
    def cache(self):
        cm = CacheManager()
        cm.clear()
        return cm
    
    def test_cache_string(self, cache):
        cache.set("hello world", "str_key")
        assert cache.get("str_key") == "hello world"
    
    def test_cache_integer(self, cache):
        cache.set(42, "int_key")
        assert cache.get("int_key") == 42
    
    def test_cache_float(self, cache):
        cache.set(3.14159, "float_key")
        assert cache.get("float_key") == 3.14159
    
    def test_cache_list(self, cache):
        data = [1, 2, 3, "four", 5.0]
        cache.set(data, "list_key")
        assert cache.get("list_key") == data
    
    def test_cache_dict(self, cache):
        data = {"name": "test", "count": 10}
        cache.set(data, "dict_key")
        assert cache.get("dict_key") == data
    
    def test_cache_nested_structure(self, cache):
        data = {
            "episodes": [
                {"name": "Ep01", "sequences": ["sq0010", "sq0020"]},
                {"name": "Ep02", "sequences": ["sq0010"]},
            ]
        }
        cache.set(data, "nested_key")
        result = cache.get("nested_key")
        assert result["episodes"][0]["name"] == "Ep01"


class TestCacheKeyGeneration:
    """Tests for cache key generation."""
    
    @pytest.fixture
    def cache(self):
        cm = CacheManager()
        cm.clear()
        return cm
    
    def test_single_part_key(self, cache):
        cache.set("value", "single")
        assert cache.get("single") == "value"
    
    def test_multi_part_key(self, cache):
        cache.set("value", "part1", "part2", "part3")
        assert cache.get("part1", "part2", "part3") == "value"
    
    def test_different_key_paths_independent(self, cache):
        cache.set("value_a", "path", "a")
        cache.set("value_b", "path", "b")
        assert cache.get("path", "a") == "value_a"
        assert cache.get("path", "b") == "value_b"

