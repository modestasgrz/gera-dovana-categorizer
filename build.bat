@echo off
REM Build script for Gift Voucher Categorizer (Windows)
REM
REM This script builds a standalone executable using PyInstaller.
REM Usage: build.bat [clean]
REM   - build.bat       : Build the application
REM   - build.bat clean : Clean build artifacts and exit

setlocal enabledelayedexpansion

echo ========================================================
echo   Gift Voucher Categorizer - Build Script
echo ========================================================
echo.

REM Function to clean build artifacts
if "%1"=="clean" (
    echo Cleaning build artifacts...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    if exist __pycache__ rmdir /s /q __pycache__
    for /d /r %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
    for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    echo [OK] Build artifacts cleaned
    goto :eof
)

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv is not installed
    echo   Install uv: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

REM Sync dependencies (ensures pyinstaller is installed from lockfile)
echo Syncing dependencies...
uv sync --frozen

REM Clean previous build artifacts
echo.
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo [OK] Build artifacts cleaned
echo.

REM Run PyInstaller
echo Running PyInstaller...
echo.
uv run pyinstaller product_categorizer.spec --clean

echo.
echo ========================================================
echo   Build Complete!
echo ========================================================
echo.
echo Windows Executable:
echo   [*] dist\GiftVoucherCategorizer.exe
echo.
echo To run:
echo   1. Run: dist\GiftVoucherCategorizer.exe
echo   2. Enter your OpenAI API key when prompted
echo   3. Select a CSV file to categorize
echo.
echo Build artifacts:
echo   - build\ (temporary files, can be deleted)
echo   - dist\  (final executable)
echo.
echo To clean build artifacts:
echo   build.bat clean
echo.
