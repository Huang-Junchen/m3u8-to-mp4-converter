@echo off
REM M3U8 to MP4 Converter - PyInstaller Build Script
REM This script does NOT require a C compiler
echo ========================================
echo Starting PyInstaller Build Process
echo ========================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install PyInstaller if not installed
echo Checking PyInstaller installation...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found, installing...
    uv pip install pyinstaller
)

echo.
echo Building with PyInstaller...
echo.

REM Build with PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "M3U8Converter" ^
    --add-data "resources;resources" ^
    --add-data "i18n;i18n" ^
    --hidden-import PyQt5 ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import aiohttp ^
    --hidden-import aiohttp.client ^
    --hidden-import pycryptodome ^
    --hidden-import asyncio_throttle ^
    --hidden-import colorthief ^
    --hidden-import darkdetect ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module test ^
    --exclude-module tests ^
    --noconfirm ^
    --distpath dist ^
    --workpath build_pyinstaller ^
    main.py

echo.
echo ========================================
echo Build Complete!
echo Output: dist\M3U8Converter.exe
echo ========================================
echo.
echo Note: The executable size may be large (80-150 MB)
echo This is normal because it includes Python runtime and all dependencies.
echo.

pause
