"""CSV utility functions for reading, writing, and validating CSV files."""

import csv
import itertools
from pathlib import Path

from loguru import logger

from src.config import ENCODINGS, REQUIRED_COLUMNS
from src.llm_service import ProductInput


def detect_encoding(file_path: Path) -> str:
    """Detect CSV file encoding using fallback strategy.

    Tries encodings listed in ENCODINGS from src/config.py.

    Args:
        file_path: Path to the CSV file

    Returns:
        Detected encoding name

    Raises:
        ValueError: If all encoding attempts fail
    """
    for encoding in ENCODINGS:
        try:
            with file_path.open(encoding=encoding) as f:
                # Try to read first few lines to validate encoding
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
        except (UnicodeDecodeError, UnicodeError):
            continue
        else:
            logger.debug(f"Detected encoding: {encoding}")
            return encoding

    msg = f"Failed to detect encoding for {file_path}. Tried: {ENCODINGS}"
    raise ValueError(msg)


def read_csv_chunk(file_path: Path, offset: int, limit: int, encoding: str) -> list[dict[str, str]]:
    """Read a chunk of rows from CSV file.

    Args:
        file_path: Path to the CSV file
        offset: Starting row index (0-based, excluding header)
        limit: Maximum number of rows to read
        encoding: File encoding

    Returns:
        List of row dictionaries
    """
    with file_path.open(encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        return list(itertools.islice(reader, offset, offset + limit))


def get_csv_columns(file_path: Path, encoding: str) -> list[str]:
    """Get column names from CSV file.

    Args:
        file_path: Path to the CSV file
        encoding: File encoding

    Returns:
        List of column names from CSV header
    """
    with file_path.open(encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames) if reader.fieldnames else []


def validate_csv_columns(columns: list[str]) -> None:
    """Validate that CSV has all required columns.

    Args:
        columns: List of column names from CSV

    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        msg = f"CSV missing required columns: {missing}"
        raise ValueError(msg)


def extract_product_input(row: dict[str, str]) -> ProductInput:
    """Extract ProductInput from CSV row.

    Args:
        row: CSV row dictionary

    Returns:
        ProductInput object
    """
    return ProductInput(
        ProgramName=row.get("ProgramName", ""),
        ProgramDescription=row.get("ProgramDescription", ""),
        About_Place=row.get("About_Place", ""),
    )


def write_csv_chunk(
    output_path: Path,
    rows: list[dict[str, str]],
    is_first_chunk: bool,
    encoding: str,
    output_columns: list[str],
) -> None:
    """Write a chunk of rows to output CSV.

    Args:
        output_path: Path to output CSV file
        rows: List of row dictionaries (with category and comment)
        is_first_chunk: Whether this is the first chunk (write header)
        encoding: File encoding
        output_columns: List of output column names
    """
    mode = "w" if is_first_chunk else "a"

    with output_path.open(mode=mode, encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)

        if is_first_chunk:
            writer.writeheader()

        writer.writerows(rows)
