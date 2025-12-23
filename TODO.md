# Product Categorizer - Development TODO List

## Phase 1: Project Setup & Tooling ✅ COMPLETE
- [x] Initialize uv project structure
- [x] Create `pyproject.toml` with dependencies (openai, loguru, pytest, mypy, ruff, pyinstaller, chardet)
- [x] Configure ruff with strict linting rules in `pyproject.toml`
- [x] Configure mypy with strict type-checking in `pyproject.toml`
- [x] Configure pytest settings in `pyproject.toml`
- [x] Create `src/` directory structure
- [x] Create `tests/` directory structure
- [x] Create `data/` directory for sample CSVs
- [x] Create `.gitignore` for Python project
- [x] Verify uv environment setup with `uv sync`

## Phase 2: Configuration Layer (`config.py`) ✅ COMPLETE
- [x] Define batch size constants: `CSV_BATCH_SIZE = 1000`, `API_CONCURRENT_BATCH_SIZE = 50`
- [x] Define hardcoded category list: `PRODUCT_CATEGORIES` (12 categories including "unknown")
- [x] Define `Config` Pydantic model with fields: `openai_api_key: str`, `model_name: str`
- [x] Implement `get_config_file_path() -> Path` function (returns `~/.product_categorizer_config.json`)
- [x] Implement `load_config() -> Config | None` function with Pydantic validation and error handling
- [x] Implement `save_config(config: Config) -> None` function with JSON serialization
- [x] Create module-level constants `API_KEY` and `MODEL_NAME` (loaded on import)
- [x] Add type annotations to all functions (no `from __future__ import annotations`)
- [x] Write `tests/test_config.py` with pytest (6 focused tests)
  - Test loading valid config
  - Test loading when file not found (returns None)
  - Test loading with missing fields (returns None)
  - Test loading malformed JSON (returns None)
  - Test saving config
  - Test save/load roundtrip
- [x] Run mypy on `src/config.py` (strict mode, no issues)
- [x] Run ruff on `src/config.py` (strict linting, all checks passed)

**Important Notes:**
- If config file doesn't exist, has missing fields, or is malformed → GUI must show modal to prompt user for API key and model name (implemented in Phase 6)
- `API_KEY` and `MODEL_NAME` constants cannot remain None - GUI must ensure valid values before processing
- Config uses Pydantic `BaseModel` for validation (not TypedDict)
- Use `Config(**data)` instead of `Config.model_validate(data)`

## Phase 3: Logging Utilities (`logging_utils.py`) ✅ COMPLETE
- [x] Import and configure loguru logger
- [x] Implement `setup_logging()` function for console output only (no log files)
- [x] Configure log levels (INFO for chunk-level operations, ERROR for failures)
- [x] Configure log format with timestamps and levels (colorized output)
- [x] Add type annotations
- [x] Run mypy on `src/logging_utils.py`
- [x] Run ruff on `src/logging_utils.py`

**Important Note:**
- Logs go to console/terminal only - no silent file creation on client's PC

## Phase 4: AI Client Layer (`llm_service.py`) ✅ COMPLETE
- [x] Import OpenAI SDK, asyncio, and tenacity
- [x] Define `ProductInput` Pydantic BaseModel
- [x] Define `CategoryOutput` Pydantic BaseModel (category: str, comment: str)
- [x] ~~Implement `verify_openai_api_key(client: AsyncOpenAI) -> bool` handshake function~~ → Moved to `config.py` as inline verification in `save_config()`
- [x] Implement tree-of-thought categorization prompt (TODO: refine in Phase 9)
- [x] Implement `categorize_product_async(client: AsyncOpenAI, product: ProductInput, model: str) -> CategoryOutput`
  - [x] Automatic retry logic for `RateLimitError` using tenacity (configurable wait/attempts)
  - [x] Catch all errors and return `CategoryOutput` with 'unknown' category
- [x] Implement `categorize_batch_async(client: AsyncOpenAI, products: list[ProductInput], model: str) -> list[CategoryOutput]`
  - [x] Use asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE) for concurrency
- [x] Custom exceptions defined in `src/exceptions.py`
- [x] Add detailed logging with loguru (errors and status)
- [x] Add type annotations to all functions
- [x] Run mypy and ruff on `src/llm_service.py`

## Phase 5: Core Processing Layer ✅ COMPLETE (diverged from plan)
**Note**: Implementation diverged into separate modules for better separation of concerns:
- CSV operations → `src/csv_service.py`
- LLM operations → `src/llm_service.py`
- Main orchestration → `src/core.py` (CSV processing pipeline)
- Application entry point → `src/main.py`

- [x] Import csv, pathlib (in csv_service.py and core.py)
- [x] Code determines input schema columns, with required columns (REQUIRED_COLUMNS in config.py)
- [x] Code determines output schema (14 input columns + "category" + "comment")
- [x] Implement `detect_encoding(file_path: Path) -> str` function in csv_service.py
  - Tries UTF-8, cp1252, latin1 in order (configurable via ENCODINGS in config.py)
  - Raises ValueError if all fail
- [x] Implement `read_csv_chunk()` function in csv_service.py
  - Uses csv.DictReader with detected encoding
  - Uses itertools.islice for efficient chunking
  - Returns list of row dictionaries
- [x] Implement `extract_product_input()` function in csv_service.py
  - Extracts ProgramName, ProgramDescription, About_Place
  - Returns ProductInput BaseModel
- [x] Implement main processing logic in core.py `process_csv_async()` function
  - Detects encoding using csv_service
  - Validates CSV columns with REQUIRED_COLUMNS
  - Counts total rows
  - Creates AsyncOpenAI client
  - Loops through chunks (CSV_BATCH_SIZE = 1000):
    - Reads chunk via read_csv_chunk()
    - Extracts ProductInput for each row
    - Calls categorize_batch_async() (50 concurrent via semaphore)
    - Appends category and comment to rows
    - Writes chunk incrementally via write_csv_chunk()
  - Generates output path: `<original_name>_categorized.csv`
  - Returns (output_path, summary_stats)
- [x] Implement `write_csv_chunk()` function in csv_service.py
  - Writes header only on first chunk
  - Appends subsequent chunks
  - Uses csv.DictWriter
- [x] Add `get_csv_columns()` function in csv_service.py
  - Extracts column names from CSV header
- [x] Add `validate_csv_columns()` function in csv_service.py
  - Validates required columns are present
- [x] Add comprehensive error handling and minimal logging
- [x] Add type annotations to all functions
- [x] Write comprehensive tests:
  - tests/test_csv_service.py (CSV operations)
  - tests/test_llm_service.py (LLM operations, mocked)
  - tests/test_main.py (integration testing)
  - tests/test_config.py (configuration)
- [x] Run mypy on all Phase 5 modules
- [x] Run ruff on all Phase 5 modules

**Completed Phase 5 TODO items**:
- [x] Optimize row counting for better performance (raw line reading instead of CSV parsing)
- [x] Add API key verification before processing starts (verify_openai_api_key handshake)
- [x] Clean up TODO comments in code (except modal window - Phase 6)
- [x] All unit tests updated and passing (32 tests)
- [x] mypy and ruff checks passing with no issues

**Remaining TODO comments in code (to be addressed in Phase 6)**:
- core.py line 30: Modal window for error messages (Phase 6 GUI implementation)
- core.py line 62: Research senior ways to count rows (current implementation is efficient)
- llm_service.py line 58: Prompt engineering refinement (Phase 9 task)

## Phase 6: GUI Layer (`gui.py`) ✅ COMPLETE
- [x] Import tkinter and threading
- [x] Define `ProductCategorizerApp` class
- [x] Implement main window initialization (title: "Product Categorizer", size: 700x500, modern layout)
- [x] **Implement startup config validation with modal window:**
  - On app start, check if `OPENAI_API_KEY` is None
  - If config missing → show modal window to collect:
    - OpenAI API Key (text input, masked with *)
    - Model Name (dropdown: gpt-5-nano-2025-08-07, gpt-5-mini-2025-08-07, gpt-4o-mini, gpt-4o)
  - Save config using `save_config()` and update instance variables
  - Prevents closing dialog without API key (warns user before exit)
- [x] Create file selection button and dialog for input CSV
- [x] Create label to display selected file path (dynamic, updates on selection)
- [x] Create status display area with scrollable Text widget
  - Shows messages: "Ready", "Processing...", "Completed"
  - Colorized, monospace font for better readability
- [x] Create "Run Categorization" button for processing
  - Disabled until file is selected
  - Changes to "Processing..." during execution
- [x] Implement Settings button (reopens config modal)
- [x] Implement `_on_select_file()` method with file dialog
- [x] Implement `_on_run_processing()` method
  - Validates file selected and API key exists
  - Updates status to "Processing..."
  - Runs processing in background thread (threading.Thread, daemon=True)
  - On success: shows completion modal with summary stats + output path
  - On error: shows user-friendly error modal
- [x] Implement `_prompt_for_config()` method (modal dialog)
  - Centered on screen
  - Prevents closing without API key (with confirmation)
  - Saves and reloads config
- [x] Add user-friendly error message translation (`_translate_error()`)
  - API key errors → "Invalid API key..."
  - Network errors → "Network error..."
  - Encoding errors → "File encoding error..."
  - Missing columns → "Invalid CSV file..."
  - Authentication errors → "Authentication failed..."
  - Generic fallback for unknown errors
- [x] Add logging for user actions (file selected, processing started, etc.)
- [x] Add type annotations to all methods
- [x] Create `run_app()` entrypoint function in `src/gui.py`
- [x] Run mypy on `src/gui.py` (no issues)
- [x] Run ruff on `src/gui.py` (all checks passed)

**Implementation Highlights**:
- Modern, professional UI with color scheme (#2c3e50, #3498db, #27ae60)
- Error handling abstracted to `_validate_and_process()` (ruff TRY301 compliance)
- Background thread processing prevents UI freezing
- Modal dialogs for all user interactions (config, success, errors)
- Status text widget shows processing log in real-time
- Fully type-annotated and linter-clean

**Manual Testing Required** (Phase 7):
- Test with valid API key and sample CSV
- Test with invalid API key
- Test with malformed CSV
- Test settings dialog update

## Phase 7: Integration & End-to-End Testing
- [ ] Create `src/main.py` for CLI entrypoint
- [ ] Test full flow: config setup → file selection → processing → output
- [ ] Use actual sample CSV (data/test_data.csv) for testing
- [ ] Verify categorized output has correct schema (14 + 2 columns)
- [ ] Verify categories are from predefined list or "unknown"
- [ ] Test error scenarios end-to-end (missing API key, invalid CSV, network errors)
- [ ] Write integration test in `tests/test_integration.py`
  - Mock OpenAI responses
  - Test full CSV categorization pipeline with Lithuanian text
  - Test chunked processing (simulate 2000+ rows)
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run mypy on entire `src/` directory
- [ ] Run ruff on entire codebase

## Phase 8: Packaging & Distribution
- [ ] Create PyInstaller spec file for the application
- [ ] Test PyInstaller build on macOS
  - Create `.app` bundle with `--windowed` flag
  - Test app runs without Python installed
  - Verify config file creation in home directory
  - Verify log file creation
  - Test with sample CSV end-to-end
- [ ] Document PyInstaller commands in README
- [ ] Add build script (shell script or Python script)
- [ ] (Future) Set up CI/CD for multi-platform builds

## Phase 9: Prompt Engineering & Category Refinement
- [ ] Work with client to finalize category list
- [ ] Refine tree-of-thought prompt with real examples
- [ ] Test categorization accuracy on sample data
- [ ] Adjust prompt based on results
- [ ] Document prompt engineering decisions

## Phase 10: Documentation & Polish
- [ ] Update `README.md` with:
  - Project description (categorization app for Lithuanian gift vouchers)
  - Installation instructions (per OS)
  - OpenAI API key setup guide
  - Model selection guide (nano vs mini)
  - Usage instructions
  - Troubleshooting section
  - Log file locations
  - Performance notes (~5-10 min for 13k rows)
- [ ] Add docstrings to all public functions
- [ ] Add inline comments for complex logic only (where not self-evident)
- [ ] Review and refactor for simplicity (avoid over-engineering)
- [ ] Final linting pass: `ruff check src/ tests/`
- [ ] Final type-checking pass: `mypy src/`
- [ ] Final test pass: `pytest tests/ -v`

## Nice-to-Have Features (Future)
- [ ] Real-time progress display in GUI (row X/Y, percentage)
- [ ] Resume capability for interrupted processing
- [ ] Category confidence scores
- [ ] Export categorization statistics report
- [ ] Batch size configuration in GUI
- [ ] Dark mode for GUI

## Notes
- Tests are written immediately after each component
- Avoid redundant function wrappers
- Keep mocks simple and straightforward
- Follow Senior SWE Python standards throughout
- All functions have type annotations
- Ruff strict linting rules enforced
- mypy strict mode enforced
- Direct Lithuanian classification (no translation step)
- Target performance: <10 minutes for 13k rows
