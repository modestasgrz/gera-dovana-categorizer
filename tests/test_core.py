"""Tests for CSV processing pipeline."""

import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from src.core import process_csv_async
from src.llm_service import CategoryOutput


@pytest.mark.asyncio
async def test_process_csv_async(tmp_path: Path) -> None:
    """Test full CSV processing pipeline."""
    # Create test input CSV with required columns
    input_file = tmp_path / "input.csv"
    header = "ProgramName,ProgramDescription,About_Place,ExtraCol"
    rows = [
        "Test Program,Description,Place,Extra1",
        "Another,Desc2,Place2,Extra2",
    ]
    input_file.write_text(f"{header}\n" + "\n".join(rows), encoding="utf-8")

    # Mock OpenAI client
    mock_client = AsyncMock()

    # Mock categorize_batch_async
    mock_results = [
        CategoryOutput(category="spa_wellness", comment=""),
        CategoryOutput(category="restaurants_food", comment=""),
    ]

    with (
        patch("src.core.OPENAI_API_KEY", "test-api-key"),
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.categorize_batch_async", return_value=mock_results),
    ):
        output_path, summary = await process_csv_async(input_file)

    # Verify output file exists
    assert output_path.exists()
    assert output_path.name == "input_categorized.csv"

    # Verify summary stats
    assert summary["total"] == 2
    assert summary["categorized"] == 2
    assert summary["unknown"] == 0

    # Verify output contents
    with output_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        result_rows = list(reader)

    assert len(result_rows) == 2
    assert result_rows[0]["category"] == "spa_wellness"
    assert result_rows[1]["category"] == "restaurants_food"
    # Verify original columns preserved
    assert result_rows[0]["ExtraCol"] == "Extra1"


@pytest.mark.asyncio
async def test_process_csv_async_with_unknown_categories(tmp_path: Path) -> None:
    """Test CSV processing with unknown categories."""
    # Create test input CSV
    input_file = tmp_path / "input.csv"
    header = "ProgramName,ProgramDescription,About_Place"
    row = "Test,Desc,Place"
    input_file.write_text(f"{header}\n{row}", encoding="utf-8")

    # Mock OpenAI client
    mock_client = AsyncMock()

    # Mock categorize_batch_async with unknown result
    mock_results = [CategoryOutput(category="unknown", comment="API error")]

    with (
        patch("src.core.OPENAI_API_KEY", "test-api-key"),
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.categorize_batch_async", return_value=mock_results),
    ):
        _output_path, summary = await process_csv_async(input_file)

    # Verify summary stats
    assert summary["total"] == 1
    assert summary["categorized"] == 0
    assert summary["unknown"] == 1
