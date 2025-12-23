"""CSV processing orchestration."""

from collections.abc import Callable
from pathlib import Path

from loguru import logger
from openai import AsyncOpenAI

from src.config import ACTIVE_CONFIG, CSV_BATCH_SIZE
from src.csv_service import (
    detect_encoding,
    extract_product_input,
    get_csv_columns,
    read_csv_chunk,
    validate_csv_columns,
    write_csv_chunk,
)
from src.llm_service import CategoryOutput, categorize_batch_async


async def process_csv_async(
    input_path: Path,
    progress_callback: Callable[[int, int], None] | None = None,
    rate_limit_callback: Callable[[bool], None] | None = None,
) -> tuple[Path, dict[str, int]]:
    """Process CSV file and categorize products using OpenAI API.

    Args:
        input_path: Path to input CSV file
        progress_callback: Optional callback(rows_processed, total_rows)
        rate_limit_callback: Optional callback(is_waiting) for rate limit status

    Returns:
        Tuple of (output_path, summary_stats)
    """
    # Create OpenAI client
    client = AsyncOpenAI(api_key=ACTIVE_CONFIG.openai_api_key)

    encoding = detect_encoding(input_path)
    logger.info(f"Processing {input_path} with encoding {encoding}")

    input_columns = get_csv_columns(input_path, encoding)
    validate_csv_columns(input_columns)
    logger.debug(f"CSV columns: {input_columns}")

    output_columns = [*input_columns, "category", "comment"]

    # Count rows by reading raw lines instead of parsing CSV
    with input_path.open(encoding=encoding) as f:
        total_rows = sum(1 for _ in f) - 1  # Subtract 1 for header row

    logger.info(f"Total rows to process: {total_rows}")

    output_path = input_path.parent / f"{input_path.stem}_categorized.csv"
    summary: dict[str, int] = {"total": total_rows, "categorized": 0, "unknown": 0}
    offset = 0
    is_first_chunk = True

    while offset < total_rows:
        rows = read_csv_chunk(input_path, offset, CSV_BATCH_SIZE, encoding)

        if not rows:
            break

        products = [extract_product_input(row) for row in rows]
        # AsyncOpenAI client is thread-safe and designed to be shared across concurrent requests
        results: list[CategoryOutput] = await categorize_batch_async(
            client, products, ACTIVE_CONFIG.model_name, rate_limit_callback
        )

        for row, result in zip(rows, results, strict=True):
            row["category"] = str(result.category)
            row["comment"] = str(result.comment)
            if str(result.category).lower() == "unknown":
                summary["unknown"] += 1
            else:
                summary["categorized"] += 1

        write_csv_chunk(output_path, rows, is_first_chunk, encoding, output_columns)

        is_first_chunk = False
        offset += len(rows)

        logger.info(f"Processed {offset}/{total_rows} rows")

        # Call progress callback if provided
        if progress_callback:
            progress_callback(offset, total_rows)

    logger.success(f"Categorization complete. Output: {output_path}")
    logger.info(f"Summary: {summary}")

    return output_path, summary
