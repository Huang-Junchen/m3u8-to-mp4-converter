@echo off
REM M3U8 to MP4 Converter - Nuitka Build Script
echo ========================================
echo Starting Nuitka Build Process
echo ========================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install Nuitka if not installed
echo Checking Nuitka installation...
python -m pip show nuitka >nul 2>&1
if errorlevel 1 (
    echo Nuitka not found, installing...
    uv pip install nuitka
)

echo.
echo Building with Nuitka...
echo.

REM Build with Nuitka
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=pyqt5 ^
    --windows-console-mode=disable ^
    --company-name="M3U8Converter" ^
    --product-name="M3U8 to MP4 Converter" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --file-description="M3U8 to MP4 Converter" ^
    --copyright="Copyright (c) 2025" ^
    --include-data-dir=resources=resources ^
    --include-data-dir=i18n=i18n ^
    --include-package=PyQt5 ^
    --include-package=aiohttp ^
    --include-package=pycryptodome ^
    --include-package=asyncio_throttle ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=PIL._tkinter_finder ^
    --remove-output ^
    --output-dir=dist ^
    main.py

echo.
echo ========================================
echo Build Complete!
echo Output: dist\main.exe
echo ========================================

pause
