"""MCAP writer with protobuf support."""

from pathlib import Path
from typing import Iterator, Tuple, Dict, Any

from mcap_protobuf.writer import Writer
from rich.console import Console
from rich.progress import Progress, TaskID

from . import event_pb2
from .file_reader import read_jsonl_files
from .json_to_protobuf import json_to_event_wrapper


console = Console()


def write_mcap(input_files: list[str], output_file: str, verbose: bool = False) -> None:
    """Write JSONL files to MCAP format using protobuf serialization.

    Args:
        input_files: List of input JSONL file paths
        output_file: Output MCAP file path
        verbose: Enable verbose output
    """
    output_path = Path(output_file)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_lines = 0
    processed_lines = 0
    error_count = 0

    # Count total lines for progress tracking
    if verbose:
        console.print("[blue]Counting input lines...[/blue]")
        for file_path in input_files:
            try:
                with open(file_path, "r") as f:
                    total_lines += sum(1 for line in f if line.strip())
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not count lines in {file_path}: {e}[/yellow]"
                )

    with open(output_path, "wb") as f, Writer(f) as writer:
        # Progress tracking
        if verbose and total_lines > 0:
            with Progress() as progress:
                task = progress.add_task("Converting files...", total=total_lines)

                for file_path, json_obj in read_jsonl_files(input_files):
                    processed_lines += 1

                    # Convert JSON to protobuf
                    event_wrapper = json_to_event_wrapper(json_obj)
                    if event_wrapper is None:
                        error_count += 1
                        progress.advance(task)
                        continue

                    # Write to MCAP
                    try:
                        writer.write_message(
                            topic="vector_event",
                            message=event_wrapper,
                            log_time=event_wrapper.metric.timestamp.ToNanoseconds(),
                            publish_time=event_wrapper.metric.timestamp.ToNanoseconds(),
                        )
                    except Exception as e:
                        console.print(f"[red]Error writing message: {e}[/red]")
                        error_count += 1

                    progress.advance(task)
        else:
            # Process without progress bar
            for file_path, json_obj in read_jsonl_files(input_files):
                processed_lines += 1

                # Convert JSON to protobuf
                event_wrapper = json_to_event_wrapper(json_obj)
                if event_wrapper is None:
                    error_count += 1
                    continue

                # Write to MCAP
                try:
                    writer.write_message(
                        topic="vector_event",
                        message=event_wrapper,
                        log_time=event_wrapper.metric.timestamp.ToNanoseconds(),
                        publish_time=event_wrapper.metric.timestamp.ToNanoseconds(),
                    )
                except Exception as e:
                    console.print(f"[red]Error writing message: {e}[/red]")
                    error_count += 1

    # Summary
    successful_lines = processed_lines - error_count
    if verbose:
        console.print(f"[green]Processed {processed_lines} lines[/green]")
        console.print(
            f"[green]Successfully converted {successful_lines} messages[/green]"
        )
        if error_count > 0:
            console.print(f"[yellow]Encountered {error_count} errors[/yellow]")
        console.print(f"[green]Output written to: {output_file}[/green]")
