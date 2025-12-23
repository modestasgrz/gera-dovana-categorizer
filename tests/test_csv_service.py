"""Tests for CSV utility functions."""

import csv
from pathlib import Path

from src.config import REQUIRED_COLUMNS
from src.csv_service import (
    detect_encoding,
    extract_product_input,
    read_csv_chunk,
    write_csv_chunk,
)
from src.llm_service import ProductInput


def test_required_columns_schema() -> None:
    """Test that REQUIRED_COLUMNS has correct structure."""
    assert len(REQUIRED_COLUMNS) == 3
    assert "ProgramName" in REQUIRED_COLUMNS
    assert "ProgramDescription" in REQUIRED_COLUMNS
    assert "About_Place" in REQUIRED_COLUMNS


def test_detect_encoding_utf8(tmp_path: Path) -> None:
    """Test encoding detection for UTF-8 file."""
    test_file = tmp_path / "test_utf8.csv"
    test_file.write_text("Name,Description\nTest,Tęst", encoding="utf-8")

    encoding = detect_encoding(test_file)
    assert encoding == "utf-8"


def test_detect_encoding_cp1252(tmp_path: Path) -> None:
    """Test encoding detection for cp1252 file."""
    test_file = tmp_path / "test_cp1252.csv"
    # Write with cp1252 encoding (Windows)
    test_file.write_bytes(b"Name,Description\r\nTest,T\xe8st")

    encoding = detect_encoding(test_file)
    assert encoding in ["utf-8", "cp1252", "latin1"]


def test_read_csv_chunk(tmp_path: Path) -> None:
    """Test reading a chunk of CSV rows."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("Name,Value\nRow1,A\nRow2,B\nRow3,C\nRow4,D\nRow5,E", encoding="utf-8")

    # Read first 2 rows
    rows = read_csv_chunk(test_file, offset=0, limit=2, encoding="utf-8")
    assert len(rows) == 2
    assert rows[0]["Name"] == "Row1"
    assert rows[1]["Name"] == "Row2"

    # Read next 2 rows
    rows = read_csv_chunk(test_file, offset=2, limit=2, encoding="utf-8")
    assert len(rows) == 2
    assert rows[0]["Name"] == "Row3"
    assert rows[1]["Name"] == "Row4"


def test_read_csv_chunk_offset_beyond_file(tmp_path: Path) -> None:
    """Test reading chunk with offset beyond file length."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("Name,Value\nRow1,A", encoding="utf-8")

    rows = read_csv_chunk(test_file, offset=10, limit=5, encoding="utf-8")
    assert len(rows) == 0


def test_extract_product_input() -> None:
    """Test extracting ProductInput from CSV row."""
    row = {
        "ProgramName": "Test Program",
        "ProgramDescription": "Test Description",
        "About_Place": "Test Place",
        "OtherField": "Ignored",
    }

    product = extract_product_input(row)

    assert isinstance(product, ProductInput)
    assert product.ProgramName == "Test Program"
    assert product.ProgramDescription == "Test Description"
    assert product.About_Place == "Test Place"


def test_extract_product_input_missing_fields() -> None:
    """Test extracting ProductInput with missing fields."""
    row = {"ProgramName": "Test"}

    product = extract_product_input(row)

    assert product.ProgramName == "Test"
    assert product.ProgramDescription == ""
    assert product.About_Place == ""


def test_write_csv_chunk_first(tmp_path: Path) -> None:
    """Test writing first chunk with header."""
    output_file = tmp_path / "output.csv"

    # Create minimal test data
    input_cols = ["ProgramName", "ProgramDescription", "About_Place"]
    output_cols = [*input_cols, "category", "comment"]

    rows = [
        {
            "ProgramName": "Test1",
            "ProgramDescription": "",
            "About_Place": "",
            "category": "spa_wellness",
            "comment": "",
        },
        {
            "ProgramName": "Test2",
            "ProgramDescription": "",
            "About_Place": "",
            "category": "unknown",
            "comment": "Error",
        },
    ]

    write_csv_chunk(
        output_file, rows, is_first_chunk=True, encoding="utf-8", output_columns=output_cols
    )

    # Verify file contents
    with output_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        result_rows = list(reader)

    assert len(result_rows) == 2
    assert result_rows[0]["category"] == "spa_wellness"
    assert result_rows[1]["category"] == "unknown"


def test_write_csv_chunk_append(tmp_path: Path) -> None:
    """Test appending chunk without header."""
    output_file = tmp_path / "output.csv"

    input_cols = ["ProgramName", "ProgramDescription", "About_Place"]
    output_cols = [*input_cols, "category", "comment"]

    # Write first chunk with header
    rows1 = [
        {
            "ProgramName": "Test1",
            "ProgramDescription": "",
            "About_Place": "",
            "category": "spa_wellness",
            "comment": "",
        }
    ]
    write_csv_chunk(
        output_file, rows1, is_first_chunk=True, encoding="utf-8", output_columns=output_cols
    )

    # Append second chunk
    rows2 = [
        {
            "ProgramName": "Test2",
            "ProgramDescription": "",
            "About_Place": "",
            "category": "unknown",
            "comment": "",
        }
    ]
    write_csv_chunk(
        output_file, rows2, is_first_chunk=False, encoding="utf-8", output_columns=output_cols
    )

    # Verify file contents
    with output_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        result_rows = list(reader)

    assert len(result_rows) == 2
