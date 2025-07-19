"""Tests for file reading functionality."""

import tempfile
import json
from pathlib import Path

import pytest

from vector2mcap.file_reader import read_jsonl_file, read_jsonl_files


@pytest.fixture
def sample_jsonl_file():
    """Create a temporary JSONL file."""
    data = [
        {"metric": {"name": "test1", "value": 1}},
        {"metric": {"name": "test2", "value": 2}},
        {"metric": {"name": "test3", "value": 3}},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
        return f.name


@pytest.fixture
def invalid_jsonl_file():
    """Create a JSONL file with some invalid JSON lines."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"valid": "json"}\n')
        f.write("invalid json line\n")
        f.write('{"another": "valid"}\n')
        return f.name


def test_read_jsonl_file_valid(sample_jsonl_file):
    """Test reading a valid JSONL file."""
    results = list(read_jsonl_file(sample_jsonl_file))

    assert len(results) == 3
    assert results[0]["metric"]["name"] == "test1"
    assert results[1]["metric"]["name"] == "test2"
    assert results[2]["metric"]["name"] == "test3"


def test_read_jsonl_file_with_invalid_lines(invalid_jsonl_file):
    """Test reading JSONL file with invalid JSON lines."""
    results = list(read_jsonl_file(invalid_jsonl_file))

    # Should skip invalid lines and continue
    assert len(results) == 2
    assert results[0]["valid"] == "json"
    assert results[1]["another"] == "valid"


def test_read_jsonl_file_nonexistent():
    """Test reading nonexistent file."""
    with pytest.raises(FileNotFoundError):
        list(read_jsonl_file("nonexistent.jsonl"))


def test_read_jsonl_files_multiple(sample_jsonl_file):
    """Test reading multiple JSONL files."""
    # Create another temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"additional": "data"}\n')
        second_file = f.name

    try:
        results = list(read_jsonl_files([sample_jsonl_file, second_file]))

        # Should have results from both files
        assert len(results) == 4  # 3 from first file + 1 from second

        # Check file paths are included
        file_paths = [result[0] for result in results]
        assert sample_jsonl_file in file_paths
        assert second_file in file_paths

    finally:
        Path(second_file).unlink()


def test_read_jsonl_files_with_missing_file(sample_jsonl_file):
    """Test reading files when some don't exist."""
    results = list(read_jsonl_files([sample_jsonl_file, "nonexistent.jsonl"]))

    # Should continue with valid files
    assert len(results) == 3
    assert all(result[0] == sample_jsonl_file for result in results)
