#!/usr/bin/env bash
# Build script for Gift Voucher Categorizer (macOS/Linux)
#
# This script builds a standalone executable using PyInstaller.
# Usage: ./build.sh [clean]
#   - ./build.sh       : Build the application
#   - ./build.sh clean : Clean build artifacts and exit

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Gift Voucher Categorizer - Build Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Function to clean build artifacts
clean_build() {
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build/
    rm -rf dist/
    rm -rf __pycache__/
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}✓ Build artifacts cleaned${NC}"
}

# If 'clean' argument provided, clean and exit
if [ "$1" == "clean" ]; then
    clean_build
    exit 0
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ Error: uv is not installed${NC}"
    echo "  Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies (ensures pyinstaller is installed from lockfile)
echo -e "${YELLOW}Syncing dependencies...${NC}"
uv sync --frozen


# Clean previous build artifacts
clean_build
echo ""

# Run PyInstaller
echo -e "${YELLOW}Running PyInstaller...${NC}"
echo ""
uv run pyinstaller product_categorizer.spec --clean

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Build Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Show output location based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}macOS App Bundle:${NC}"
    echo "  📦 dist/GiftVoucherCategorizer.app"
    echo ""
    echo -e "${YELLOW}To run:${NC}"
    echo "  1. Open the app: open dist/GiftVoucherCategorizer.app"
    echo "  2. Enter your OpenAI API key when prompted"
    echo "  3. Select a CSV file to categorize"
    echo ""
else
    echo -e "${GREEN}Linux Executable:${NC}"
    echo "  📦 dist/GiftVoucherCategorizer"
    echo ""
    echo -e "${YELLOW}To run:${NC}"
    echo "  1. Run: ./dist/GiftVoucherCategorizer"
    echo "  2. Enter your OpenAI API key when prompted"
    echo "  3. Select a CSV file to categorize"
    echo ""
fi

echo -e "${YELLOW}Build artifacts:${NC}"
echo "  - build/ (temporary files, can be deleted)"
echo "  - dist/  (final executable)"
echo ""
echo -e "${YELLOW}To clean build artifacts:${NC}"
echo "  ./build.sh clean"
echo ""
