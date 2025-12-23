# CLAUDE.md - Project Context for AI Agents

## Project Overview
**Product Categorizer** is a cross-platform desktop application that automatically categorizes Lithuanian gift voucher products from CSV files using OpenAI's GPT-5 models. The app adds a `category` column to existing CSV data based on product names, descriptions, and locations.

## Business Context
- **Input**: CSV file with 14 columns containing Lithuanian gift voucher data (~13k rows)
- **Task**: Add a `category` column to each row using AI classification
- **Output**: New CSV file with original 14 columns + `category` column
- **Language**: Direct Lithuanian text classification (no translation)
- **Performance Target**: <10 minutes for 13k rows
- **Error Handling**: Failed classifications default to "unknown" category

## Technology Stack
- **Language**: Python 3.12+
- **Package Manager**: uv
- **Build System**: setuptools
- **Data Validation**: Pydantic (BaseModel for structured data)
- **AI Provider**: OpenAI GPT-5 (via official Python SDK)
  - Primary model: `gpt-5-nano-2025-08-07`
  - Fallback: `gpt-5-mini-2025-08-07`
- **GUI Framework**: tkinter (built-in)
- **Logging**: loguru
- **Encoding Detection**: chardet
- **Type Checking**: mypy (strict mode)
- **Linting**: ruff (strict rules)
- **Testing**: pytest with pytest-asyncio
- **Packaging**: PyInstaller

## Architecture Overview

### Five Main Layers

1. **Configuration Layer** (`src/config.py`)
   - Manages OpenAI API key and model name in user's home directory
   - Config file: `~/.product_categorizer_config.json`
   - Uses Pydantic BaseModel for config validation
   - Hardcoded constants: `CSV_BATCH_SIZE = 1000`, `API_CONCURRENT_BATCH_SIZE = 50`
   - Hardcoded category list: `PRODUCT_CATEGORIES`
   - Functions: `load_config()`, `save_config()`, `get_config_file_path()`
   - Module-level constants: `API_KEY`, `MODEL_NAME` (loaded on import)
   - **CRITICAL**: If `API_KEY` or `MODEL_NAME` is None, GUI must show modal window to collect values before processing

2. **AI Client Layer** (`src/ai_client.py`)
   - Encapsulates all OpenAI SDK interaction
   - Async parallel API calls (50 concurrent requests via asyncio.Semaphore)
   - Tree-of-thought prompting with few-shot examples for Lithuanian text
   - Functions: `initialize_openai_client()`, `categorize_product_async()`, `categorize_batch_async()`
   - Error classes: `APIKeyError`, `APINetworkError`, `APIRateLimitError`

3. **Core Processing Layer** (`src/core.py`)
   - CSV transformation logic with chunked reading (1000 rows per chunk)
   - Auto-detects encoding using chardet
   - Processes chunks asynchronously with 50 concurrent API calls
   - Incremental output writing
   - Functions: `detect_encoding()`, `read_csv_chunk()`, `process_csv()`, `write_csv_chunk()`
   - Input columns: ProgramName, ProgramDescription, About_Place
   - Output: original 14 columns + "category"

4. **Presentation Layer** (`src/gui.py`)
   - Cross-platform tkinter GUI
   - File selection, status display, API key/model management
   - Background thread processing to avoid UI blocking
   - Simple "Processing..." message (real-time progress is nice-to-have)

5. **Logging Utilities** (`src/logging_utils.py`)
   - Configures loguru for minimal logging (chunk-level, not per-request)
   - Console output only - no log files created
   - Colorized terminal output for better readability

## Project Structure
```
.
├── pyproject.toml          # Project config, dependencies, tool settings
├── uv.lock                 # Dependency lock file
├── README.md               # User documentation
├── TODO.md                 # Development task list
├── CLAUDE.md               # This file
├── product_sort_instructions.md  # Detailed implementation guide
├── data/
│   └── ITS-5236(ITS-5236).csv   # Sample input CSV
├── src/
│   ├── __init__.py
│   ├── main.py         # CLI entrypoint
│   ├── config.py           # Configuration layer + constants
│   ├── ai_client.py        # OpenAI integration (async)
│   ├── core.py             # CSV processing logic
│   ├── gui.py              # Desktop GUI
│   └── logging_utils.py    # Logging setup
└── tests/
    ├── test_config.py
    ├── test_ai_client.py
    ├── test_core.py
    ├── test_logging_utils.py
    └── test_integration.py
```

## Key Configuration

### Batch Size Constants (in `config.py`)
```python
# Hardcoded constants - DO NOT make configurable via GUI
CSV_BATCH_SIZE = 1000              # Rows to read per chunk
API_CONCURRENT_BATCH_SIZE = 50     # Concurrent API requests
```

### Product Categories (in `config.py`)
```python
# Hardcoded category list - will be finalized with client
PRODUCT_CATEGORIES = [
    "spa_wellness",           # SPA, wellness, massage, health treatments
    "accommodation",          # Hotels, vacation stays, lodging
    "travel_tourism",         # Travel agencies, tours, trips, excursions
    "sports_fitness",         # Gyms, sports clubs, fitness centers
    "beauty_cosmetics",       # Beauty clinics, cosmetics, grooming
    "restaurants_food",       # Restaurants, cafes, dining, food experiences
    "entertainment",          # Shows, events, cultural activities
    "adventure_activities",   # Rally taxi, balloon rides, extreme sports
    "shopping_retail",        # Gift cards, retail stores, shopping
    "medical_health",         # Medical centers, health checkups, clinics
    "education_workshops",    # Classes, workshops, tea ceremonies, courses
    "unknown"                 # Fallback for unclear/failed categorizations
]
```

### Config File Format (`~/.product_categorizer_config.json`)
```json
{
  "openai_api_key": "sk-...",
  "model_name": "gpt-5-nano-2025-08-07"
}
```

## CSV Schema

### Input CSV (14 columns)
```
LoyaltyProgramID, ProgramName, NameSimple, NameOfficial, BrandName,
ProgramUrl, ProgramDescription, About_Place, SeoTitle, SeoDescription,
SeoFriendlyUrl, StartTime, SalesStartTime, SalesEndTime
```

### Output CSV (15 columns)
```
<All 14 input columns> + category
```

### Columns Used for Categorization
- `ProgramName` - Product name (Lithuanian)
- `ProgramDescription` - Product description (Lithuanian)
- `About_Place` - Location/place information (Lithuanian)

## Coding Standards

### Type Annotations
- **REQUIRED** for all function arguments and return types
- **DO NOT** use `from __future__ import annotations` - use native Python 3.12 syntax
- Use `X | None` instead of `Optional[X]`
- **Use Pydantic `BaseModel`** for all dataclass-like structures and data validation
  - Provides runtime validation, better IDE support, and clearer errors
  - Preferred over `TypedDict` for structured data (e.g., `Config`, `ProductInput`, `CategoryResult`)
  - Use `.model_dump()` to convert to dict when needed (e.g., for JSON serialization)
  - Access fields as attributes: `product.ProgramName` not `product["ProgramName"]`
- Example:
  ```python
  from pydantic import BaseModel

  class Config(BaseModel):
      openai_api_key: str
      model_name: str

  class ProductInput(BaseModel):
      ProgramName: str
      ProgramDescription: str
      About_Place: str

  class CategoryResult(BaseModel):
      category: str

  async def categorize_product_async(
      client: AsyncOpenAI,
      product: ProductInput,
      model: str
  ) -> str:
      # Access fields as attributes
      prompt = f"Categorize: {product.ProgramName}"
      ...
  ```

### Async/Await Patterns
- Use `async`/`await` for AI client functions
- Use `asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)` for rate limiting
- Run async code in sync context using `asyncio.run()` from core.py
- Example:
  ```python
  import asyncio
  from openai import AsyncOpenAI

  async def categorize_batch_async(
      client: AsyncOpenAI,
      products: list[ProductInput],
      model: str
  ) -> list[str]:
      semaphore = asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)

      async def categorize_with_limit(product: ProductInput) -> str:
          async with semaphore:
              return await categorize_product_async(client, product, model)

      tasks = [categorize_with_limit(p) for p in products]
      return await asyncio.gather(*tasks)
  ```

### Error Handling
- Create custom exception classes for domain errors
- Failed categorizations → return "unknown", don't raise
- Provide clear error messages for users
- Log all errors with context using loguru
- Example:
  ```python
  try:
      response = await client.chat.completions.create(...)
      return parse_category(response)
  except Exception as e:
      logger.error(f"Categorization failed: {e}")
      return "unknown"
  ```

### Logging
- Use loguru logger: `from loguru import logger`
- **Console output only** - no log files created (avoids silent file creation on client's PC)
- **Minimal logging strategy**: chunk-level only, not per-request
- Log at appropriate levels:
  - `logger.info()` - chunk start/end, summary counts
  - `logger.error()` - errors and exceptions
- Don't log sensitive data (API keys)
- Colorized output for better terminal readability
- Example:
  ```python
  logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({len(rows)} rows)")
  logger.info(f"Chunk complete: {categorized} categorized, {unknown} unknown")
  ```

### Encoding Detection
- Use `chardet` to auto-detect CSV encoding
- Don't hardcode encoding (UTF-8, UTF-8-sig, etc.)
- Handle BOM automatically
- Example:
  ```python
  import chardet

  def detect_encoding(file_path: Path) -> str:
      with file_path.open('rb') as f:
          result = chardet.detect(f.read(100000))
      return result['encoding']
  ```

### Testing
- Write tests immediately after implementing each module
- Use pytest fixtures for setup/teardown
- Use `tmp_path` fixture for temporary file operations
- Mock external dependencies (OpenAI API)
- Keep mocks simple - avoid over-complicated test setups
- Test async functions using pytest-asyncio
- Example:
  ```python
  import pytest
  from unittest.mock import AsyncMock

  @pytest.mark.asyncio
  async def test_categorize_product() -> None:
      mock_client = AsyncMock()
      mock_client.chat.completions.create.return_value = mock_response

      result = await categorize_product_async(mock_client, product, "gpt-5-nano")

      assert result == "spa_wellness"
  ```

### Linting & Type Checking
- Run `ruff check src/ tests/` before committing
- Run `mypy src/` before committing
- Fix all errors - zero tolerance policy
- Ruff strict rules enforced in `pyproject.toml`

## Development Workflow

1. **Implement module** (e.g., `config.py`)
2. **Add type annotations** to all functions
3. **Write tests** immediately (`test_config.py`)
4. **Run tests**: `pytest tests/test_config.py -v`
5. **Run mypy**: `mypy src/config.py`
6. **Run ruff**: `ruff check src/config.py`
7. **Fix any issues**
8. **Move to next module**

## Implementation Order
1. Project setup (uv, pyproject.toml, tooling)
2. Configuration layer + tests (includes constants and category list)
3. Logging utilities + tests
4. AI Client layer + tests (async implementation)
5. Core processing layer + tests (chunked + async)
6. GUI layer (manual testing)
7. Integration testing with real CSV sample
8. Prompt engineering and category refinement
9. Packaging with PyInstaller
10. Documentation

## Key Design Principles

### Simplicity First
- Avoid redundant function wrappers
- Don't over-engineer - solve the immediate problem
- No unnecessary abstractions
- Keep mocks simple in tests
- No resume capability (simpler)

### Performance Optimization
- Chunked CSV reading (1000 rows) for memory efficiency
- Async parallel API calls (50 concurrent) for speed
- Incremental output writing to avoid memory issues
- Target: <10 minutes for 13k rows

### Senior SWE Standards
- Type everything
- Test everything (except GUI initially)
- Log appropriately (minimal, chunk-level)
- Handle errors explicitly
- Clear separation of concerns

### User-Focused
- Non-technical users should never see terminal
- Clear, friendly error messages
- Obvious UI flow: select file → run → get output
- API key and model management seamless
- Simple "Processing..." status (no complex progress bars initially)

## Lithuanian Language Handling

### Direct Classification Strategy
- **NO translation step** - process Lithuanian text directly
- GPT-5 models have native Lithuanian support
- More cost-effective (single API call vs translate + classify)
- Preserves cultural context for gift categorization

### Prompt Strategy
- Tree-of-thought reasoning
- Few-shot examples with Lithuanian text
- Structured JSON output
- Category must be from predefined list or "unknown"

### Example Prompt Structure
```python
prompt = """
You are an expert at categorizing Lithuanian gift vouchers and experiences.

Categories:
- spa_wellness: SPA, sveikatingumo centrai, masažai
- accommodation: Viešbučiai, apgyvendinimas
- travel_tourism: Kelionės, ekskursijos, turizmas
... [full category list with Lithuanian descriptions]

Analyze the following product and select ONE category:

Product Name: {ProgramName}
Description: {ProgramDescription}
Location: {About_Place}

Think step-by-step:
1. What type of service/product is this?
2. Which category best fits?
3. If unclear, return "unknown"

Return ONLY the category name in JSON format: {"category": "spa_wellness"}
"""
```

## Common Patterns

### Config Loading Pattern
```python
from pathlib import Path
import json
from loguru import logger
from pydantic import BaseModel, ValidationError

class Config(BaseModel):
    openai_api_key: str
    model_name: str

def get_config_file_path() -> Path:
    return Path.home() / ".product_categorizer_config.json"

def load_config() -> Config | None:
    config_path = get_config_file_path()
    if not config_path.exists():
        logger.debug(f"Config file not found at {config_path}")
        return None
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return Config(**data)  # Use Config(**data) not model_validate
    except (json.JSONDecodeError, OSError, ValidationError) as e:
        logger.error(f"Failed to load config: {e}")
        return None

def save_config(config: Config) -> None:
    config_path = get_config_file_path()
    try:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info(f"Config saved to {config_path}")
    except OSError as e:
        logger.error(f"Failed to save config: {e}")
        raise

# Load configuration on module import
_config = load_config()

# Module-level constants (not functions!)
API_KEY: str | None = _config.openai_api_key if _config else None
MODEL_NAME: str = _config.model_name if _config else "gpt-5-nano-2025-08-07"
```

### Async Categorization Pattern
```python
from openai import AsyncOpenAI
from pydantic import BaseModel
import asyncio

class ProductInput(BaseModel):
    ProgramName: str
    ProgramDescription: str
    About_Place: str

async def categorize_batch_async(
    client: AsyncOpenAI,
    products: list[ProductInput],
    model: str
) -> list[str]:
    semaphore = asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)

    async def categorize_one(product: ProductInput) -> str:
        async with semaphore:
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": build_prompt(product)}],
                    response_format={"type": "json_object"}
                )
                return parse_category(response)
            except Exception as e:
                logger.error(f"Failed to categorize: {e}")
                return "unknown"

    tasks = [categorize_one(p) for p in products]
    return await asyncio.gather(*tasks)
```

### Chunked CSV Processing Pattern
```python
def process_csv(input_path: Path, api_key: str, model: str) -> tuple[Path, dict[str, int]]:
    encoding = detect_encoding(input_path)
    total_rows = count_rows(input_path, encoding)

    output_path = input_path.parent / f"{input_path.stem}_categorized.csv"
    client = AsyncOpenAI(api_key=api_key)

    stats = {"total": 0, "categorized": 0, "unknown": 0}

    for offset in range(0, total_rows, CSV_BATCH_SIZE):
        logger.info(f"Processing chunk at offset {offset}")

        rows = read_csv_chunk(input_path, offset, CSV_BATCH_SIZE, encoding)
        products = [extract_product_input(row) for row in rows]

        categories = asyncio.run(categorize_batch_async(client, products, model))

        for row, category in zip(rows, categories):
            row["category"] = category
            stats["total"] += 1
            stats["categorized" if category != "unknown" else "unknown"] += 1

        is_first = (offset == 0)
        write_csv_chunk(output_path, rows, is_first, encoding)

    return output_path, stats
```

## Important Notes

### What NOT to Do
- ❌ Don't use `from __future__ import annotations` - use native Python 3.12 syntax
- ❌ Don't use `Optional[X]` - use `X | None` instead
- ❌ Don't use `Config.model_validate(data)` - use `Config(**data)` instead
- ❌ Don't use `TypedDict` for data structures - use Pydantic `BaseModel` instead
- ❌ Don't create getter functions for config values - use module-level constants
- ❌ Don't create wrapper functions for single operations
- ❌ Don't add comments to self-evident code
- ❌ Don't use complex mocking frameworks when simple mocks work
- ❌ Don't add features not in requirements
- ❌ Don't skip type annotations "for now"
- ❌ Don't commit code that fails mypy or ruff
- ❌ Don't translate Lithuanian text to English
- ❌ Don't log every API request (minimal logging only)
- ❌ Don't make batch sizes configurable (hardcode them)
- ❌ Don't create log files - use console output only

### What TO Do
- ✅ Type annotate everything
- ✅ Use Pydantic BaseModel for dataclass-like structures (validation, IDE support)
- ✅ Write tests immediately after implementation
- ✅ Log important operations (chunk-level)
- ✅ Handle errors explicitly with custom exceptions
- ✅ Keep code simple and readable
- ✅ Run linters and type checker before committing
- ✅ Process Lithuanian text directly
- ✅ Use async/await for concurrent API calls
- ✅ Auto-detect CSV encoding with chardet
- ✅ Return "unknown" for failed categorizations

## External References
- [OpenAI Python SDK Docs](https://github.com/openai/openai-python)
- [OpenAI GPT-5 Models](https://platform.openai.com/docs/models)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Chardet Documentation](https://chardet.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## Performance Notes
- Expected runtime: 5-10 minutes for 13k rows
- Memory usage: Low (~100MB peak with chunking)
- API costs: ~$0.50-2.00 per 13k rows (depending on model)
- Concurrency: 50 requests in parallel (rate limit safe)

---

This document provides AI agents with the context needed to contribute to the Product Categorizer project following established patterns and standards.
