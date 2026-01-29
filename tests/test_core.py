"""Tests for CSV processing pipeline."""

import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from src.core import normalize_comment_with_names, process_csv_async
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
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="lt"),
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
    assert result_rows[0]["category_id"] == "spa_wellness"
    assert result_rows[1]["category_id"] == "restaurants_food"
    assert result_rows[0]["category_url"] == ""  # Unknown categories have empty URL
    assert "category_name" in result_rows[0]
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
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="lt"),
        patch("src.core.categorize_batch_async", return_value=mock_results),
    ):
        _output_path, summary = await process_csv_async(input_file)

    # Verify summary stats
    assert summary["total"] == 1
    assert summary["categorized"] == 0
    assert summary["unknown"] == 1


def test_normalize_comment_with_names() -> None:
    """Test comment normalization with category names."""
    category_map = {
        "292": "SPA ir masažai",
        "299": "Vakarienės",
        "280": "Poilsis su nakvyne",
    }

    comment = "Chosen 292 (0.85); considered 299 (0.10) but focused on relaxation."
    result = normalize_comment_with_names(comment, category_map)

    assert "Chosen SPA ir masažai" in result
    assert "considered Vakarienės" in result
    assert "(0.85)" in result  # Confidence preserved
    assert "(0.10)" in result


def test_normalize_comment_preserves_confidence() -> None:
    """Test that confidence scores are not modified."""
    category_map = {"251": "Oro pramogos"}

    comment = "Chosen 251 (0.95); considered Unknown (0.02) but air activity."
    result = normalize_comment_with_names(comment, category_map)

    assert "Chosen Oro pramogos" in result
    assert "(0.95)" in result
    assert "(0.02)" in result


def test_normalize_comment_unknown_category_id() -> None:
    """Test comment normalization when category ID not in map."""
    category_map = {"292": "SPA ir masažai"}

    comment = "Chosen 999 (0.50); considered 292 (0.40) but unclear."
    result = normalize_comment_with_names(comment, category_map)

    # Unknown IDs should remain as IDs
    assert "Chosen 999" in result
    assert "considered SPA ir masažai" in result


def test_normalize_comment_no_category_ids() -> None:
    """Test comment normalization with no category IDs."""
    category_map = {"292": "SPA ir masažai"}

    comment = "Unknown category - product description too vague."
    result = normalize_comment_with_names(comment, category_map)

    # Should return unchanged
    assert result == comment
