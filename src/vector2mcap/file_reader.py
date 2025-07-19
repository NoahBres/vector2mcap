"""File reading utilities for JSONL files."""

import json
from pathlib import Path
from typing import Iterator, Dict, Any

from rich.console import Console


console = Console()


def read_jsonl_file(file_path: str) -> Iterator[Dict[str, Any]]:
    """Read a JSONL file and yield parsed JSON objects.

    Args:
        file_path: Path to the JSONL file

    Yields:
        Parsed JSON objects from each line

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If a line contains invalid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    line_number = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line_number += 1
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                console.print(
                    f"[yellow]Warning: Invalid JSON on line {line_number} in {file_path}: {e}[/yellow]"
                )
                # Continue processing other lines instead of failing completely
                continue


def read_jsonl_files(file_paths: list[str]) -> Iterator[tuple[str, Dict[str, Any]]]:
    """Read multiple JSONL files and yield (filename, json_object) pairs.

    Args:
        file_paths: List of file paths to read

    Yields:
        Tuples of (filename, parsed_json_object)
    """
    for file_path in file_paths:
        try:
            for json_obj in read_jsonl_file(file_path):
                yield file_path, json_obj
        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}[/red]")
            continue
        except Exception as e:
            console.print(f"[red]Error reading {file_path}: {e}[/red]")
            continue
