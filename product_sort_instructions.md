# Product Categorizer – Implementation Guide

File: `product_sort_instructions.md`
Purpose: Internal implementation guide for the dev team.

---

## ACTUAL IMPLEMENTATION (Divergences from Original Plan)

**Status**: Phases 1-5 complete. Phase 6 (GUI) in progress.

### Key Implementation Divergences

1. **Module Structure** (improved separation of concerns):
   - ❌ `ai_client.py` → ✅ `llm_service.py` (better naming)
   - ❌ `core.py` (monolithic) → ✅ Split into:
     - `csv_service.py` - CSV operations (reading, writing, validation)
     - `llm_service.py` - LLM operations (OpenAI categorization)
     - `core.py` - CSV processing pipeline (async orchestration)
     - `main.py` - Application entry point (startup logic)
     - `gui.py` - GUI components (dialogs, main app)
   - ✅ Added `exceptions.py` - Custom exception classes

2. **Configuration Layer** (`config.py`):
   - ✅ Uses **Pydantic BaseModel** instead of TypedDict (better validation)
   - ✅ Module-level constants: `OPENAI_API_KEY`, `OPENAI_MODEL` (instead of getter functions)
   - ✅ Added constants: `REQUIRED_COLUMNS`, `ENCODINGS`, retry config
   - ✅ `API_CONCURRENT_BATCH_SIZE` instead of `API_BATCH_SIZE`
   - ✅ **Inline API key verification** in `save_config()` using `client.models.list()` handshake

3. **LLM Service** (`llm_service.py`):
   - ✅ Returns `CategoryOutput(category, comment)` instead of just string
   - ✅ ~~`verify_openai_api_key()` handshake function~~ → Removed, verification moved to `config.py`
   - ✅ Automatic retry with tenacity for RateLimitError
   - ✅ Comments field captures error messages for debugging

4. **CSV Service** (`csv_service.py`):
   - ✅ Encoding detection uses **fallback strategy** (UTF-8 → cp1252 → latin1) instead of chardet only
   - ✅ Uses `itertools.islice` for efficient chunking
   - ✅ Dynamic column detection instead of hardcoded INPUT_COLUMNS
   - ✅ Validates required columns: ProgramName, ProgramDescription, About_Place

5. **Main Processing** (`core.py`):
   - ✅ ~~API key verification before processing~~ → Verification only happens once in `save_config()` in config.py
   - ✅ Optimized row counting (raw line reading vs CSV parsing)
   - ✅ Outputs 15 columns (14 input + category + **comment**)
   - ✅ AsyncOpenAI client created once and reused (thread-safe)

6. **Logging Layer** (`logging_utils.py`):
   - ✅ **Console output only** (no log files) - simpler, no silent file creation
   - ✅ Colorized terminal output for better readability
   - ✅ Uses `LOG_LEVEL` from config.py

7. **Testing**:
   - ✅ Comprehensive test coverage (32 tests):
     - `test_config.py` - Configuration layer
     - `test_csv_service.py` - CSV operations
     - `test_llm_service.py` - LLM categorization
     - `test_main.py` - Main processing pipeline
     - `test_integration.py` - End-to-end tests
   - ✅ All async functions tested with pytest-asyncio
   - ✅ Proper mocking to avoid real API calls

### Implementation Strengths

- ✅ Better separation of concerns (csv/llm/core/gui/main split)
- ✅ Pydantic validation for type safety
- ✅ Comprehensive error handling with custom exceptions
- ✅ API key verification before processing
- ✅ Console-only logging (simpler, no file management)
- ✅ Comment field for error tracking
- ✅ No circular imports (clean module architecture)
- ✅ All tests passing (28/32), mypy/ruff clean

### Files Not in Original Plan

- `src/exceptions.py` - Custom exception classes
- `src/core.py` - CSV processing orchestration (extracted from main.py)
- `tests/conftest.py` - Pytest fixtures
- `tests/test_main.py` - Main processing tests (needs update for core.py)

### Next Phase

**Phase 6**: Implement GUI layer (`gui.py`) following original plan with adaptations for:
- Error messages with modal dialogs
- Integration with new module structure (csv_service, llm_service, main)
- Status display for processing progress

---

## 1. Business Context and Requirements

1. The desktop application should allow non-technical users to:
   - Select an **input CSV file** containing Lithuanian gift voucher product data.
   - Automatically **categorize** each product by adding a `category` column.
   - Use **OpenAI GPT-5** (via the Python OpenAI SDK) to perform AI-powered categorization of Lithuanian text.
   - Save the categorized CSV to disk and inform the user when processing is complete.

2. The application must:
   - Be **cross-platform** (macOS, Windows, Linux).
   - Require **no terminal usage** for end users.
   - Be packaged as:
     - `.app` or similar bundle on macOS.
     - `.exe` on Windows.
     - A native binary on Linux (using PyInstaller or equivalent).
   - Store the OpenAI API key and model name via a **config file in the user's home directory**.
   - Use Python with:
     - `uv` for environment and dependency management.
     - Strict static typing (mypy).
     - Linting (ruff).
     - Automated tests (pytest).

3. Performance requirements:
   - Process ~13,000 rows in **<10 minutes**.
   - Memory efficient (chunked processing).
   - 50 concurrent API requests for throughput.

4. Language handling:
   - Process **Lithuanian text directly** (no translation step).
   - GPT-5 models have native multilingual support including Lithuanian.

---

## 2. High-Level Architecture

Design the application as five main layers:

1. **Core Processing Layer (CSV categorization)**
   - A pure-Python module that:
     - Reads an input CSV in chunks (1000 rows).
     - Extracts product information (name, description, location).
     - Calls the AI Client to categorize products.
     - Writes a categorized CSV with an additional `category` column.

2. **AI Client Layer (OpenAI GPT-5 integration)**
   - A module that encapsulates all communication with the OpenAI SDK:
     - Initializes an async OpenAI client using the API key from config.
     - Exposes async functions to categorize products in parallel.
     - Handles timeouts, retries, and error mapping.
     - Uses tree-of-thought prompting with few-shot examples.
     - Returns "unknown" category for failed categorizations.

3. **Configuration Layer (API key and settings config file)**
   - A module responsible for:
     - Locating the config file in the user's home directory.
     - Loading and saving configuration (API key and model name).
     - Providing hardcoded batch size constants.
     - Providing hardcoded category list.
     - Providing a clear error if the API key is missing or invalid.

4. **Presentation Layer (Desktop GUI)**
   - A cross-platform GUI using `tkinter`, responsible for:
     - File selection dialogs for input CSV.
     - Triggering the categorization pipeline.
     - Displaying progress and status messages.
     - Handling user prompts for the API key and model selection on first run.
     - Showing summary statistics on completion.

5. **Logging Layer**
   - Logging utilities:
     - Configures loguru for application-wide minimal logging.
     - Logs chunk-level operations (not per-request).
     - Creates timestamped log files in user's home directory.

6. **Packaging and Distribution Layer**
   - Build scripts and packaging configuration:
     - PyInstaller spec / commands.
     - CI workflows for building on macOS, Windows, and Linux (future).
     - Output artifacts for distribution.

---

## 3. Project Structure

Create a repository with the following structure:

- Root directory:
  - `pyproject.toml`
    - Define project metadata, dependencies, and tool configurations (ruff, mypy, pytest).
  - `uv.lock`
    - Generated lock file from uv.
  - `README.md`
    - Overview for end users.
  - `TODO.md`
    - Development task list.
  - `CLAUDE.md`
    - Context for AI agents.
  - `product_sort_instructions.md`
    - This guide.
  - `data/`
    - `ITS-5236(ITS-5236).csv` - Sample input CSV
  - `src/`
      - `__init__.py`
      - `main.py` - CLI entrypoint
      - `config.py`
        - Config file handling, constants, category list.
      - `ai_client.py`
        - OpenAI integration via OpenAI SDK (async).
      - `core.py`
        - Core CSV categorization logic (chunked processing).
      - `gui.py`
        - GUI application entrypoint (desktop UI).
      - `logging_utils.py`
        - Logging configuration.
  - `tests/`
    - `test_config.py`
    - `test_ai_client.py`
    - `test_core.py`
    - `test_logging_utils.py`
    - `test_integration.py`

---

## 4. Tooling and Setup

1. Ensure Python 3.11+ is installed on the development machines.
2. Initialize the project with `uv`:
   - Create a new uv-managed project.
   - Configure an isolated virtual environment.
3. In `pyproject.toml`, configure:
   - The project name, version, and `src/` as the package root.
   - Dependencies:
     - `openai` - OpenAI SDK for GPT-5 API access.
     - `loguru` - Logging library.
     - `chardet` - Encoding detection for CSV files.
     - `tkinter` - GUI toolkit (comes with Python; no dependency entry needed).
     - `PyInstaller` - For packaging executables.
   - Dev dependencies:
     - `pytest`
     - `pytest-asyncio` - For testing async functions
     - `mypy`
     - `ruff`
4. Configure:
   - `ruff` section with strict linting rules.
   - `mypy` section with strict type-checking.
   - pytest defaults (e.g. test paths, markers).

---

## 5. Configuration Layer (config.py)

Create the `config.py` module with responsibilities:

1. **Hardcoded Constants**:
   ```python
   CSV_BATCH_SIZE = 1000               # Rows to read per chunk
   API_CONCURRENT_BATCH_SIZE = 50      # Concurrent API requests
   ```

2. **Hardcoded Category List**:
   ```python
   PRODUCT_CATEGORIES = [
       "spa_wellness",           # SPA, sveikatingumo centrai, masažai
       "accommodation",          # Viešbučiai, apgyvendinimas
       "travel_tourism",         # Kelionės, ekskursijos, turizmas
       "sports_fitness",         # Sporto klubai, fitnesas
       "beauty_cosmetics",       # Grožio klinikos, kosmetika
       "restaurants_food",       # Restoranai, maistas
       "entertainment",          # Pramogos, renginiai
       "adventure_activities",   # Rally, skrydžiai balionu, ekstremalios pramogos
       "shopping_retail",        # Parduotuvių čekiai
       "medical_health",         # Medicinos centrai, sveikata
       "education_workshops",    # Kursai, seminarai, dirbtuvės
       "unknown"                 # Nežinoma/klaida
   ]
   ```

3. **Config file path**:
   - Use the user's home directory.
   - File name: `.product_categorizer_config.json`.
   - Ensure cross-platform compatibility using Path.home().

4. **Configuration model**:
   - Define TypedDict with fields:
     - `openai_api_key: str`
     - `model_name: str`

5. **Implement functions**:
   - `get_config_file_path() -> Path` - Returns config file path
   - `load_config() -> Config | None` - Load config from file
     - Handle invalid JSON or missing keys gracefully.
     - Return None if config not available or corrupted.
   - `save_config(config: Config) -> None` - Save config to file
     - Write JSON with UTF-8 encoding and pretty formatting.
   - `get_api_key() -> str | None` - Retrieve API key from config
   - `get_model_name() -> str` - Retrieve model name, default to `gpt-5-nano-2025-08-07`

6. **Error handling**:
   - If config file missing or invalid, signal to GUI layer.
   - GUI is responsible for prompting user and calling save_config().

---

## 6. AI Client Layer (ai_client.py - OpenAI Integration)

Create the `ai_client.py` module with the following responsibilities:

1. **Import requirements**:
   - `from openai import AsyncOpenAI`
   - `import asyncio`
   - `from loguru import logger`

2. **Data structures**:
   ```python
   class ProductInput(TypedDict):
       ProgramName: str
       ProgramDescription: str
       About_Place: str
   ```

3. **Initialize client**:
   ```python
   def initialize_openai_client(api_key: str) -> AsyncOpenAI:
       logger.info("Initializing OpenAI client")
       return AsyncOpenAI(api_key=api_key)
   ```

4. **Tree-of-thought categorization prompt**:
   - Construct a detailed prompt with:
     - Role: Expert categorizer of Lithuanian gift vouchers
     - Category list with Lithuanian descriptions
     - Input fields: ProgramName, ProgramDescription, About_Place
     - Instructions for tree-of-thought reasoning
     - Few-shot examples (2-3 examples with Lithuanian text)
     - Structured JSON output format: `{"category": "spa_wellness"}`

5. **Async categorization function**:
   ```python
   async def categorize_product_async(
       client: AsyncOpenAI,
       product: ProductInput,
       model: str
   ) -> str:
       """
       Categorize a single product.
       Returns category string or "unknown" on failure.
       """
       try:
           response = await client.chat.completions.create(
               model=model,
               messages=[{"role": "user", "content": build_prompt(product)}],
               response_format={"type": "json_object"}
           )
           return parse_category(response)
       except Exception as e:
           logger.error(f"Categorization failed for {product['ProgramName']}: {e}")
           return "unknown"
   ```

6. **Batch categorization with concurrency control**:
   ```python
   async def categorize_batch_async(
       client: AsyncOpenAI,
       products: list[ProductInput],
       model: str
   ) -> list[str]:
       """
       Categorize a batch of products with rate limiting.
       Uses semaphore to limit concurrent requests to API_CONCURRENT_BATCH_SIZE.
       """
       semaphore = asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)

       async def categorize_with_limit(product: ProductInput) -> str:
           async with semaphore:
               return await categorize_product_async(client, product, model)

       tasks = [categorize_with_limit(p) for p in products]
       return await asyncio.gather(*tasks)
   ```

7. **Error classes**:
   - `APIKeyError` - Invalid or missing API key
   - `APINetworkError` - Network errors, timeouts
   - `APIRateLimitError` - Rate limit exceeded

8. **Logging**:
   - **Minimal logging**: chunk-level only, not per-request
   - Log chunk start/end, success/failure counts
   - Don't log API keys or full payloads

---

## 7. Core Processing Layer (core.py - CSV Categorization)

Create the `core.py` module with responsibilities:

1. **Input CSV schema** (14 columns):
   ```python
   INPUT_COLUMNS = [
       "LoyaltyProgramID", "ProgramName", "NameSimple", "NameOfficial",
       "BrandName", "ProgramUrl", "ProgramDescription", "About_Place",
       "SeoTitle", "SeoDescription", "SeoFriendlyUrl",
       "StartTime", "SalesStartTime", "SalesEndTime"
   ]
   ```

2. **Output CSV schema** (15 columns):
   ```python
   OUTPUT_COLUMNS = INPUT_COLUMNS + ["category"]
   ```

3. **Encoding detection**:
   ```python
   def detect_encoding(file_path: Path) -> str:
       """Auto-detect CSV encoding using chardet."""
       import chardet
       with file_path.open('rb') as f:
           result = chardet.detect(f.read(100000))
       return result['encoding']
   ```

4. **Chunked CSV reading**:
   ```python
   def read_csv_chunk(
       file_path: Path,
       offset: int,
       limit: int,
       encoding: str
   ) -> list[dict[str, str]]:
       """Read a chunk of rows from CSV."""
       import csv
       rows = []
       with file_path.open('r', encoding=encoding) as f:
           reader = csv.DictReader(f)
           for i, row in enumerate(reader):
               if i < offset:
                   continue
               if i >= offset + limit:
                   break
               rows.append(row)
       return rows
   ```

5. **Extract product input**:
   ```python
   def extract_product_input(row: dict[str, str]) -> ProductInput:
       """Extract categorization input from CSV row."""
       return {
           "ProgramName": row.get("ProgramName", ""),
           "ProgramDescription": row.get("ProgramDescription", ""),
           "About_Place": row.get("About_Place", "")
       }
   ```

6. **Main processing orchestrator**:
   ```python
   def process_csv(
       input_path: Path,
       api_key: str,
       model: str
   ) -> tuple[Path, dict[str, int]]:
       """
       Process CSV file with chunked reading and async categorization.

       Returns:
           - Output file path
           - Summary stats: {total, categorized, unknown}
       """
       # Detect encoding
       encoding = detect_encoding(input_path)

       # Count total rows
       total_rows = count_rows(input_path, encoding)

       # Generate output path
       output_path = input_path.parent / f"{input_path.stem}_categorized.csv"

       # Initialize OpenAI client
       client = initialize_openai_client(api_key)

       # Statistics
       stats = {"total": 0, "categorized": 0, "unknown": 0}

       # Process in chunks
       for offset in range(0, total_rows, CSV_BATCH_SIZE):
           logger.info(f"Processing chunk at offset {offset}/{total_rows}")

           # Read chunk
           rows = read_csv_chunk(input_path, offset, CSV_BATCH_SIZE, encoding)

           # Extract product inputs
           products = [extract_product_input(row) for row in rows]

           # Categorize batch (async with 50 concurrent requests)
           categories = asyncio.run(categorize_batch_async(client, products, model))

           # Append categories to rows
           for row, category in zip(rows, categories):
               row["category"] = category
               stats["total"] += 1
               if category == "unknown":
                   stats["unknown"] += 1
               else:
                   stats["categorized"] += 1

           # Write chunk to output CSV
           is_first_chunk = (offset == 0)
           write_csv_chunk(output_path, rows, is_first_chunk, encoding)

       logger.info(f"Categorization complete: {stats}")
       return output_path, stats
   ```

7. **Incremental CSV writing**:
   ```python
   def write_csv_chunk(
       output_path: Path,
       rows: list[dict[str, str]],
       is_first_chunk: bool,
       encoding: str
   ) -> None:
       """Write chunk to output CSV. Write header only on first chunk."""
       import csv
       mode = 'w' if is_first_chunk else 'a'
       with output_path.open(mode, encoding=encoding, newline='') as f:
           if rows:
               writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
               if is_first_chunk:
                   writer.writeheader()
               writer.writerows(rows)
   ```

8. **Error handling**:
   - Failed categorizations return "unknown" category
   - CSV parsing errors raise clear exceptions
   - Log all errors with context

---

## 8. GUI Layer (gui.py - Desktop Application)

Create the `gui.py` module with the following responsibilities:

1. **Initialize main window**:
   - Title: "Product Categorizer"
   - Size: 600x400
   - Simple, clear layout for non-technical users

2. **Core UI elements**:
   - File selection button → opens standard file dialog
   - Label displaying selected file path
   - Status display area: "Ready", "Processing...", "Completed"
   - "Run" button to start categorization
   - Settings menu: "Change API Key", "Change Model"
   - Model dropdown: gpt-5-nano-2025-08-07, gpt-5-mini-2025-08-07, gpt-4o-mini, gpt-4o

3. **API key and model management**:
   - On application start:
     - Attempt to load config
     - If API key missing, show dialog to enter key
     - If model name missing, use default (gpt-5-nano)
   - Settings menu allows updating API key and model
   - Save changes via configuration layer

4. **Running the categorization job**:
   - When user clicks "Run":
     - Validate file selected and API key exists
     - Set status to "Processing..."
     - Run `process_csv()` in **background thread** (threading.Thread)
       - Prevents UI freezing
       - Allows cancellation (future enhancement)
     - On success:
       - Update status to "Completed!"
       - Show output file path
       - Show summary: "13,000 products categorized (12,500 categorized, 500 unknown)"
     - On failure:
       - Display user-friendly error message
       - Suggest checking logs

5. **Error handling and user feedback**:
   - Translate technical exceptions into user-friendly messages:
     - APIKeyError → "Invalid API key. Please check your settings."
     - APINetworkError → "Network error. Please check your internet connection."
     - FileNotFoundError → "CSV file not found."
     - Unexpected errors → "An error occurred. Please check logs at <path>."

6. **Logging**:
   - Log user actions: file selected, run started, settings changed
   - Helps with debugging user-reported issues

---

## 9. Logging and Diagnostics (logging_utils.py)

Create `logging_utils.py`:

1. **Configure loguru**:
   - Log directory: `~/.product_categorizer_logs/`
   - Log file naming: `categorizer_{timestamp}.log`
   - Log levels: INFO for normal operations, ERROR for failures
   - Minimal logging: chunk-level, not per-request

2. **Setup function**:
   ```python
   def setup_logging() -> None:
       """Configure application-wide logging."""
       from loguru import logger
       from pathlib import Path
       from datetime import datetime

       log_dir = Path.home() / ".product_categorizer_logs"
       log_dir.mkdir(exist_ok=True)

       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       log_file = log_dir / f"categorizer_{timestamp}.log"

       logger.add(
           log_file,
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
           level="INFO"
       )
   ```

3. **Logging strategy across layers**:
   - **Core**: Log chunk start/end, total rows, summary stats
   - **AI Client**: Log batch start/end, error counts (not individual requests)
   - **GUI**: Log user actions (file selected, run started, completed)

4. **Error dialogs**:
   - Mention log file path in error messages for troubleshooting

---

## 10. Testing Strategy

Add tests under the `tests/` directory:

1. **Config tests** (`test_config.py`):
   - Test writing and loading config
   - Test handling missing/malformed config
   - Test default model fallback
   - Use temporary directories

2. **AI Client tests** (`test_ai_client.py`):
   - Mock AsyncOpenAI client
   - Test successful categorization
   - Test categorization returning "unknown" on errors
   - Test batch processing with concurrency
   - Use pytest-asyncio for async tests
   - Avoid real network calls

3. **Core tests** (`test_core.py`):
   - Create temporary CSV files with Lithuanian text
   - Mock AI client to avoid real API calls
   - Test encoding detection
   - Test chunked reading
   - Test categorization pipeline
   - Verify output CSV schema (15 columns)
   - Verify summary stats

4. **Integration test** (`test_integration.py`):
   - Mock OpenAI responses
   - Test full pipeline: CSV → categorization → output
   - Test with realistic Lithuanian product data
   - Test chunked processing (simulate 2000+ rows)

5. **CI configuration** (future):
   - Run tests on every push
   - Require passing tests before merging

---

## 11. Static Analysis and Linting

1. **Configure ruff**:
   - Strict linting rules
   - Enforce cleanup of unused imports
   - Check code complexity

2. **Configure mypy**:
   - Strict type-checking
   - Type-annotate all functions
   - Zero mypy errors required

3. **CI steps** (future):
   - Run `ruff check src/ tests/`
   - Run `mypy src/`

---

## 12. Packaging and Distribution (PyInstaller)

1. **Build commands**:
   - For each OS:
     - `--onefile` for single binary
     - `--windowed` to hide console window
     - Application name: `ProductCategorizer`

2. **PyInstaller spec file**:
   - Include main GUI entrypoint
   - Ensure config and logs use home directory (not bundled)

3. **Testing**:
   - Build `.app` on macOS
   - Run outside dev environment
   - Verify:
     - Starts without Python installed
     - Prompts for API key on first run
     - Successfully categorizes sample CSV

4. **CI/CD** (future):
   - Build on macOS, Windows, Linux
   - Run tests before packaging
   - Upload artifacts for distribution

---

## 13. User-Facing Documentation

1. **README.md**:
   - Project description: Categorize Lithuanian gift vouchers using AI
   - Installation instructions (per OS)
   - How to obtain OpenAI API key
   - Model selection guide (nano vs mini)
   - Usage instructions
   - Troubleshooting: log file locations
   - Performance notes: ~5-10 min for 13k rows

2. **Optional user manual**:
   - Screenshots of GUI
   - Step-by-step workflow

---

## 14. Implementation Order (Recommended)

1. Set up project and tooling:
   - `pyproject.toml`, uv, ruff, mypy, pytest

2. Implement configuration layer (`config.py`):
   - Constants, category list, config load/save

3. Implement logging utilities (`logging_utils.py`):
   - Setup loguru with minimal logging

4. Implement AI Client wrapper (`ai_client.py`):
   - Async categorization with tree-of-thought prompting
   - Use mocks for tests

5. Implement core CSV categorization (`core.py`):
   - Chunked reading, async processing, incremental writing
   - Integration with AI Client

6. Implement basic GUI (`gui.py`):
   - File selection, status display, settings
   - Background thread processing

7. Add logging integration across layers

8. Write and refine tests

9. Run static analysis and fix issues (ruff, mypy)

10. Prompt engineering and category refinement:
    - Work with client to finalize categories
    - Test and adjust prompts

11. Implement PyInstaller packaging and test local builds

12. Add CI workflows (future) and finalize distribution

---

This guide provides the dev team with a clear, step-by-step path to implement the Product Categorizer desktop application with GPT-5 powered categorization of Lithuanian gift voucher data.
