"""Main conversion logic orchestrating the conversion process."""

from .mcap_writer import write_mcap


def convert_files(
    input_files: list[str], output_file: str, verbose: bool = False
) -> None:
    """Convert JSONL files to MCAP format.

    Args:
        input_files: List of input JSONL file paths
        output_file: Output MCAP file path
        verbose: Enable verbose output
    """
    write_mcap(input_files, output_file, verbose)
