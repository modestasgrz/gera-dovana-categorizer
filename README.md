# Gift voucher categorizer

This application automatically categorizes gift voucher CSV data by analyzing product names, descriptions, and locations. It adds a `category` column to your CSV file using AI classification.

## Installation

### Pre-built Executables

Download the executable for your platform from the releases page:
- **macOS**: `GiftVoucherCategorizer.app`
- **Windows**: `GiftVoucherCategorizer/` (folder; run `GiftVoucherCategorizer.exe` inside)
- **Linux**: `GiftVoucherCategorizer/` (folder; run `GiftVoucherCategorizer` inside, requires `chmod +x`)

### From Source

```bash
git clone <repository-url>
cd gera-dovana-categories
uv sync
uv run python src/main.py
```

**Requirements**: Python 3.12+, [uv](https://docs.astral.sh/uv/)

## Configuration

### OpenAI API Key

Get your API key from [OpenAI Platform](https://platform.openai.com/) → API keys.

Processing ~1,000 rows costs about $1 (depending on description lengths) and takes about 20 minutes using the GPT-5 nano model.

### Model Selection

| Model | Comment |
|-------|---------|
| `gpt-5-nano-2025-08-07` (default) | Fast, low cost, should be good enough | 
| `gpt-5-mini-2025-08-07` | Slower, higher cost, smarter |

## Usage

1. Launch the application and enter your OpenAI API key
2. Select your CSV file (must contain: `ProgramName`, `ProgramDescription`, `About_Place`)
3. Click **Run Categorization**
4. Output saved as `<original_name>_categorized.csv` in the same directory

### Input/Output

**Required columns:**
- `ProgramName`, `ProgramDescription`, `About_Place`

**Added columns:**
- `category` - GD category ID or `Unknown`
- `comment` - Confidence score and reasoning

All original columns are preserved.

### Troubleshooting

**Invalid API key:**
- Verify key format (`sk-...`) and OpenAI account credits

**File encoding error:**
- Re-save CSV as UTF-8

**Invalid CSV file:**
- Verify required columns: `ProgramName`, `ProgramDescription`, `About_Place`

**macOS security warning:**
- Right-click app → "Open" or Settings → Security & Privacy → "Open Anyway"

**Windows Defender warning:**
- Click "More info" → "Run anyway"

## Development

This project uses:
- **uv** for dependency management
- **ruff** for linting (strict mode)
- **mypy** for type checking (strict mode)
- **pytest** for testing

Install development dependencies:

```bash
uv sync --all-extras
```

Run tests:

```bash
make test
```

Run linter + formatter + type checker:

```bash
make check
```

## Building from Source

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

### Build

```bash
# macOS/Linux
./build.sh

# Windows
build.bat
```

### Clean

```bash
./build.sh clean  # or build.bat clean
```

### Output

- **macOS**: `dist/GiftVoucherCategorizer.app` (~39MB)
- **Windows**: `dist/GiftVoucherCategorizer/` (~35-40MB)
  - Run: `dist/GiftVoucherCategorizer/GiftVoucherCategorizer.exe`
  - Keep `_internal/` next to the exe (required at runtime)
- **Linux**: `dist/GiftVoucherCategorizer/` (~35-40MB)
  - Run: `dist/GiftVoucherCategorizer/GiftVoucherCategorizer` (requires `chmod +x`)

Build configuration: `product_categorizer.spec`
