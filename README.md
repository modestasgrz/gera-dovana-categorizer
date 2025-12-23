# Product Categorizer

AI-powered categorization tool for Lithuanian gift voucher products using OpenAI GPT-5.

## Overview

This application automatically categorizes Lithuanian gift voucher CSV data by analyzing product names, descriptions, and locations. It adds a `category` column to your CSV file using state-of-the-art AI classification.

## Features

- **Direct Lithuanian text processing** - No translation needed
- **High performance** - Process 13,000+ rows in under 10 minutes
- **Cross-platform** - Works on macOS, Windows, and Linux
- **User-friendly GUI** - No terminal required
- **Configurable models** - Support for GPT-5-nano, GPT-5-mini, and GPT-4o
- **Memory efficient** - Chunked processing for large files
- **Auto-encoding detection** - Handles various CSV encodings automatically

## Installation

_Coming soon_

## Usage

_Coming soon_

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
uv run pytest
```

Run linter:

```bash
uv run ruff check src/ tests/
```

Run type checker:

```bash
uv run mypy src/
```

## License

_To be determined_
