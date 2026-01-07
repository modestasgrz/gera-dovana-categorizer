# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Gift Voucher Categorizer.

This spec file packages the Gift Voucher Categorizer application into a standalone executable.
- Entry point: src/main.py
- Bundle type: One-file (easier distribution)
- Mode: Windowed (no console for GUI)
- Includes: All src modules, prompts module, and required dependencies
"""

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect data files from prompts package
prompts_datas = collect_data_files('prompts')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=prompts_datas,
    hiddenimports=[
        'src',
        'src.config',
        'src.core',
        'src.csv_service',
        'src.exceptions',
        'src.gui',
        'src.llm_service',
        'src.logging_utils',
        'src.main',
        'categories',
        'categories.categories',
        'prompts',
        'prompts.v1',
        'openai',
        'loguru',
        'tenacity',
        'tiktoken',  # Required by openai
        'tiktoken_ext',  # Required by openai
        'tiktoken_ext.openai_public',  # Required by openai
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest-asyncio',
        'mypy',
        'ruff',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Use onedir mode for macOS compatibility
    name='GiftVoucherCategorizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Console enabled to preserve stderr on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GiftVoucherCategorizer',
)

# macOS-specific app bundle configuration
app = BUNDLE(
    coll,
    name='GiftVoucherCategorizer.app',
    icon=None,  # Add icon path here if available (e.g., 'assets/icon.icns')
    bundle_identifier='com.giftvouchercategorizer.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Gift Voucher Categorizer',
        'CFBundleDisplayName': 'Gift Voucher Categorizer',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSRequiresAquaSystemAppearance': 'False',  # Support dark mode
    },
)
