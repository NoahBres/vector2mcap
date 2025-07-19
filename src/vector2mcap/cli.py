"""Command-line interface for vector2mcap."""

import glob
from pathlib import Path
from typing import List

import click
from rich.console import Console
from rich.progress import Progress, TaskID


console = Console()


@click.command()
@click.argument("input_patterns", nargs=-1, required=True)
@click.option("-o", "--output", required=True, help="Output MCAP file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(input_patterns: tuple[str, ...], output: str, verbose: bool) -> None:
    """Convert Vector JSONL files to MCAP format.

    INPUT_PATTERNS can be file paths or glob patterns like "*.out"
    """
    from .converter import convert_files

    # Expand glob patterns to actual file paths
    input_files = []
    for pattern in input_patterns:
        matches = glob.glob(pattern)
        if not matches:
            console.print(
                f"[yellow]Warning: No files match pattern '{pattern}'[/yellow]"
            )
        input_files.extend(matches)

    if not input_files:
        console.print("[red]Error: No input files found[/red]")
        raise click.ClickException("No input files found")

    # Remove duplicates and sort
    input_files = sorted(set(input_files))

    if verbose:
        console.print(f"[green]Found {len(input_files)} input files:[/green]")
        for file in input_files:
            console.print(f"  {file}")
        console.print(f"[green]Output file: {output}[/green]")

    try:
        convert_files(input_files, output, verbose)
        console.print(
            f"[green]Successfully converted {len(input_files)} files to {output}[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
