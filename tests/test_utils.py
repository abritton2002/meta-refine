"""Tests for Meta-Refine utility functions."""

import pytest
from pathlib import Path
import tempfile

from core.utils import format_file_size, get_language_stats, is_binary_file


def test_format_file_size():
    """Test file size formatting."""
    assert format_file_size(0) == "0 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1024 * 1024) == "1.0 MB"


def test_get_language_stats_empty():
    """Test language stats with empty file list."""
    stats = get_language_stats([])
    assert stats == {}


def test_get_language_stats_python():
    """Test language stats with Python files."""
    files = [Path("test.py"), Path("another.py")]
    stats = get_language_stats(files)
    assert stats["Python"] == 2


def test_is_binary_file_text():
    """Test detection of text files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is a text file")
        temp_path = Path(f.name)
    
    try:
        result = is_binary_file(temp_path)
        assert result is False
    finally:
        temp_path.unlink() 