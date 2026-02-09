# Gift voucher categorizer

This application automatically categorizes gift voucher CSV data by analyzing product names, descriptions, and locations. It adds `category_id`, `category_url`, and `comment` columns to your CSV file using AI classification.

## Installation

### Pre-built Executables

Download the executable for your platform from the [GitHub Releases](../../releases) page:
- **Windows**: `GiftVoucherCategorizer-windows.zip` (extract and run `GiftVoucherCategorizer.exe`)
- **macOS (Apple Silicon)**: `GiftVoucherCategorizer-macos-arm64.zip`
- **macOS (Intel)**: `GiftVoucherCategorizer-macos-intel.zip`

For detailed information about releases and building, see the [Downloads & Releases](#downloads--releases) section below.

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
- `category_id` - GD category ID or `unknown`
- `category_url` - URL to the category page on GerasDovana.lt
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

## Downloads & Releases

### Pre-built Releases

Pre-built executables for all platforms are available on the [GitHub Releases](../../releases) page.

Each release includes:
- **Windows** (`GiftVoucherCategorizer-windows.zip`) - x64 executable
- **macOS ARM64** (`GiftVoucherCategorizer-macos-arm64.zip`) - Apple Silicon (M1/M2/M3/M4)
- **macOS Intel** (`GiftVoucherCategorizer-macos-intel.zip`) - Intel Macs

Simply download the appropriate ZIP file for your platform and extract it.

### GitHub Actions Workflows

This project uses GitHub Actions to automatically build executables for all platforms. Three workflows are available:

#### 1. **Build and Release** (Primary)
**File:** `.github/workflows/release.yml`

Creates a new GitHub release with all platform builds attached.

**Usage:**
1. Go to **Actions** tab in GitHub
2. Select **"Build and Release"** workflow
3. Click **"Run workflow"**
4. Enter version number (e.g., `v1.0.0`)
5. Click **"Run workflow"**

The workflow will:
- Build for Windows (x64)
- Build for macOS ARM64 (Apple Silicon)
- Build for macOS Intel (x86_64)
- Create a new GitHub release with all three builds as downloadable ZIP files

#### 2. **Windows Build** (Legacy/Testing)
**File:** `.github/workflows/windows-build.yml`

Builds Windows executable only (for testing without creating a release).

**Usage:** Actions → "Windows Build" → Run workflow

#### 3. **macOS Build** (Legacy/Testing)
**File:** `.github/workflows/macos-build.yml`

Builds both macOS architectures (ARM64 + Intel) for testing without creating a release.

**Usage:** Actions → "macOS Build" → Run workflow

**Note:** Intel builds use the `macos-15-intel` runner, which will be deprecated in August 2027 as GitHub transitions to ARM64-only macOS runners.

## Building Locally

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
