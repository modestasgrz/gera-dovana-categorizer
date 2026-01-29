"""Integration tests for Gift Voucher Categorizer."""

import csv
import math
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from src.config import CSV_BATCH_SIZE, REQUIRED_COLUMNS
from src.core import process_csv_async
from src.llm_service import CategoryOutput, ProductInput


@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_processes_sample_csv(tmp_path: Path) -> None:
    """Process a sample CSV and verify output schema and categories."""
    input_path = tmp_path / "test_data.csv"
    fieldnames = [*REQUIRED_COLUMNS, "ExtraCol"]
    rows = [
        {
            "ProgramName": "SPA poilsis",
            "ProgramDescription": "Masažai ir procedūros",
            "About_Place": "Vilnius",
            "ExtraCol": "Extra1",
        },
        {
            "ProgramName": "Vakariene",
            "ProgramDescription": "Romantiska vakariene dviem",
            "About_Place": "Kaunas",
            "ExtraCol": "Extra2",
        },
    ]

    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    mock_client = AsyncMock()

    async def fake_categorize_batch_async(
        _client: AsyncMock,
        products: list[ProductInput],
        _model: str,
        _language: str,
        _rate_limit_callback: object = None,
    ) -> list[CategoryOutput]:
        return [CategoryOutput(category="spa_wellness", comment="") for _ in products]

    with (
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="lt"),
        patch("src.core.categorize_batch_async", side_effect=fake_categorize_batch_async),
    ):
        output_path, summary = await process_csv_async(input_path)

    assert output_path.exists()
    assert output_path.name == "test_data_categorized.csv"

    with input_path.open(encoding="utf-8") as f:
        input_reader = csv.DictReader(f)
        input_columns = list(input_reader.fieldnames or [])
        input_rows = list(input_reader)

    with output_path.open(encoding="utf-8") as f:
        output_reader = csv.DictReader(f)
        output_columns = list(output_reader.fieldnames or [])
        output_rows = list(output_reader)

    assert output_columns == [
        *input_columns,
        "category_id",
        "category_url",
        "category_name",
        "comment",
    ]
    assert len(output_rows) == len(input_rows)
    assert summary["total"] == len(input_rows)
    assert summary["categorized"] == len(input_rows)
    assert summary["unknown"] == 0

    categories = {row["category_id"] for row in output_rows}
    assert categories == {"spa_wellness"}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_chunked_processing(tmp_path: Path) -> None:
    """Process 2001 rows to verify chunking and batch boundaries."""
    input_path = tmp_path / "large.csv"
    fieldnames = ["ProgramName", "ProgramDescription", "About_Place", "ExtraCol"]

    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx in range(2001):
            writer.writerow(
                {
                    "ProgramName": f"SPA procedura {idx}",
                    "ProgramDescription": "Atpalaiduojantis masazas ir SPA ritualai",
                    "About_Place": "Vilnius",
                    "ExtraCol": f"extra-{idx}",
                }
            )

    mock_client = AsyncMock()
    batch_sizes: list[int] = []

    async def fake_categorize_batch_async(
        _client: AsyncMock,
        products: list[ProductInput],
        _model: str,
        _language: str,
        _rate_limit_callback: object = None,
    ) -> list[CategoryOutput]:
        batch_sizes.append(len(products))
        return [CategoryOutput(category="restaurants_food", comment="") for _ in products]

    with (
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="lt"),
        patch("src.core.categorize_batch_async", side_effect=fake_categorize_batch_async),
    ):
        output_path, summary = await process_csv_async(input_path)

    assert output_path.exists()
    assert summary["total"] == 2001
    assert summary["categorized"] == 2001
    assert summary["unknown"] == 0
    assert sum(batch_sizes) == 2001
    assert all(size <= CSV_BATCH_SIZE for size in batch_sizes)
    assert len(batch_sizes) == math.ceil(2001 / CSV_BATCH_SIZE)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_invalid_csv_missing_columns(tmp_path: Path) -> None:
    """Fail fast when required CSV columns are missing."""
    input_path = tmp_path / "invalid.csv"
    input_path.write_text("ProgramName,About_Place\nTest,Place", encoding="utf-8")

    mock_client = AsyncMock()

    with (
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        pytest.raises(ValueError, match=r"CSV missing required columns"),
    ):
        await process_csv_async(input_path)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_network_error_marks_unknown(tmp_path: Path) -> None:
    """Treat network-like failures as unknown categories in the output."""
    input_path = tmp_path / "network.csv"
    input_path.write_text(
        "ProgramName,ProgramDescription,About_Place\n"
        "Masazas,Atpalaiduojantis masazas,Vilnius\n"
        "Vakariene,Romantiska vakariene,Kaunas\n",
        encoding="utf-8",
    )

    mock_client = AsyncMock()

    async def fake_categorize_batch_async(
        _client: AsyncMock,
        products: list[ProductInput],
        _model: str,
        _language: str,
        _rate_limit_callback: object = None,
    ) -> list[CategoryOutput]:
        return [CategoryOutput(category="unknown", comment="Network error") for _ in products]

    with (
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="lt"),
        patch("src.core.categorize_batch_async", side_effect=fake_categorize_batch_async),
    ):
        output_path, summary = await process_csv_async(input_path)

    assert output_path.exists()
    assert summary["total"] == 2
    assert summary["categorized"] == 0
    assert summary["unknown"] == 2

    with output_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert all(row["category_id"] == "unknown" for row in rows)
    assert all(row["category_url"] == "" for row in rows)  # Unknown has empty URL


@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_unknown_language_defaults_to_lithuanian(tmp_path: Path) -> None:
    """Test that unknown language detection defaults to Lithuanian."""
    input_path = tmp_path / "test.csv"
    input_path.write_text(
        "ProgramName,ProgramDescription,About_Place\nTest,Test,Test",
        encoding="utf-8",
    )

    mock_client = AsyncMock()

    async def fake_categorize_batch_async(
        _client: AsyncMock,
        products: list[ProductInput],
        _model: str,
        language: str,
        _rate_limit_callback: object = None,
    ) -> list[CategoryOutput]:
        # Verify that language is "lt" even though detection returned unknown
        assert language == "lt"
        return [CategoryOutput(category="292", comment="Chosen 292 (0.80)") for _ in products]

    with (
        patch("src.core.AsyncOpenAI", return_value=mock_client),
        patch("src.core.detect_language_async", return_value="unknown"),
        patch("src.core.categorize_batch_async", side_effect=fake_categorize_batch_async),
    ):
        output_path, _ = await process_csv_async(input_path)

    # Verify the output includes language note
    with output_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert "; Language unidentified, defaulted to Lithuanian." in rows[0]["comment"]
