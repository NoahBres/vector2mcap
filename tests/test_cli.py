"""Tests for CLI functionality."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from vector2mcap.cli import main


@pytest.fixture
def sample_jsonl():
    """Create a temporary JSONL file with sample data."""
    content = """{"metric":{"name":"test_counter","namespace":"test","tags":{"host":"test-host"},"timestamp":"2025-07-16T14:20:06.666956352Z","kind":"absolute","counter":{"value":42.0}}}
{"metric":{"name":"test_gauge","namespace":"test","tags":{"host":"test-host"},"timestamp":"2025-07-16T14:20:06.666956352Z","kind":"absolute","gauge":{"value":100.5}}}
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(content)
        return f.name


def test_cli_help():
    """Test CLI help message."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Convert Vector JSONL files to MCAP format" in result.output


def test_cli_basic_conversion(sample_jsonl):
    """Test basic CLI conversion functionality."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".mcap", delete=False) as output_file:
        result = runner.invoke(main, [sample_jsonl, "-o", output_file.name])

        assert result.exit_code == 0
        assert "Successfully converted 1 files" in result.output
        assert Path(output_file.name).exists()
        assert Path(output_file.name).stat().st_size > 0


def test_cli_verbose_output(sample_jsonl):
    """Test CLI with verbose output."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(suffix=".mcap", delete=False) as output_file:
        result = runner.invoke(
            main, [sample_jsonl, "-o", output_file.name, "--verbose"]
        )

        assert result.exit_code == 0
        assert "Found 1 input files" in result.output
        assert "Processed 2 lines" in result.output
        assert "Successfully converted 2 messages" in result.output


def test_cli_missing_input():
    """Test CLI with missing input files."""
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent.jsonl", "-o", "output.mcap"])

    assert result.exit_code != 0
    assert "No input files found" in result.output


def test_cli_missing_output():
    """Test CLI without output file specified."""
    runner = CliRunner()
    result = runner.invoke(main, ["input.jsonl"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()
