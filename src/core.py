"""CSV processing orchestration."""

import re
from collections.abc import Callable
from pathlib import Path

from categories.categories_lt import CATEGORY_NAME_MAP as NAME_MAP_LT
from categories.categories_lt import CATEGORY_URL_MAP as URL_MAP_LT
from categories.categories_lv import CATEGORY_NAME_MAP as NAME_MAP_LV
from categories.categories_lv import CATEGORY_URL_MAP as URL_MAP_LV
from categories.categories_pl import CATEGORY_NAME_MAP as NAME_MAP_PL
from categories.categories_pl import CATEGORY_URL_MAP as URL_MAP_PL
from loguru import logger
from openai import AsyncOpenAI

from src.config import ACTIVE_CONFIG, CSV_BATCH_SIZE
from src.csv_service import (
    build_language_sample,
    detect_encoding,
    extract_product_input,
    get_csv_columns,
    read_csv_chunk,
    validate_csv_columns,
    write_csv_chunk,
)
from src.llm_service import CategoryOutput, categorize_batch_async, detect_language_async


def normalize_comment_with_names(comment: str, category_name_map: dict[str, str]) -> str:
    """Replace category IDs in comment with category names.
    Replace patterns like "Chosen 292" or "considered 273" with category names
    Pattern matches: "word 123" where 123 is a category ID
    Preserves confidence scores like "(0.95)"

    Args:
        comment: Original comment with category IDs
        category_name_map: Mapping of category ID to name

    Returns:
        Comment with category IDs replaced by names
    """

    def replace_id_with_name(match: re.Match[str]) -> str:
        prefix = match.group(1)  # "Chosen " or "considered "
        cat_id = match.group(2)  # The category ID
        cat_name = category_name_map.get(
            cat_id, cat_id
        )  # Replace with name or keep ID if not found
        return f"{prefix}{cat_name}"

    # Pattern: matches "word 123" but not "(0.12)" or similar
    pattern = r"(\w+\s+)(\d{2,})\b(?!\))"
    return re.sub(pattern, replace_id_with_name, comment)


async def process_csv_async(  # noqa: PLR0915
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

    # Detect language from sample
    language_sample = build_language_sample(input_path, encoding)
    detected_language = await detect_language_async(
        client, language_sample, ACTIVE_CONFIG.model_name
    )

    # Default to Lithuanian if unknown
    if detected_language == "unknown":
        logger.warning("Could not detect language, defaulting to Lithuanian (lt)")
        detected_language = "lt"
        language_note = "; Language unidentified, defaulted to Lithuanian."
    else:
        logger.info(f"Detected language: {detected_language}")
        language_note = ""

    # Select category catalogs based on detected language
    catalog_map = {
        "lt": (NAME_MAP_LT, URL_MAP_LT),
        "lv": (NAME_MAP_LV, URL_MAP_LV),
        "pl": (NAME_MAP_PL, URL_MAP_PL),
    }
    category_name_map, category_url_map = catalog_map.get(
        detected_language, (NAME_MAP_LT, URL_MAP_LT)
    )

    output_columns = [*input_columns, "category_id", "category_url", "category_name", "comment"]

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
            client, products, ACTIVE_CONFIG.model_name, detected_language, rate_limit_callback
        )

        for row, result in zip(rows, results, strict=True):
            category_id = str(result.category)
            row["category_id"] = category_id
            row["category_url"] = category_url_map.get(category_id, "")
            row["category_name"] = category_name_map.get(category_id, "")

            # Normalize comment by replacing category IDs with category names
            comment = str(result.comment)
            comment = normalize_comment_with_names(comment, category_name_map)

            # Append language note if language was unknown
            if language_note:
                comment += language_note
            row["comment"] = comment

            if category_id.lower() == "unknown":
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
