@echo off
REM M3U8 to MP4 Converter - Build Script
REM Uses PyInstaller to create standalone executable

echo ========================================
echo M3U8 to MP4 Converter - Build
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found
    echo Creating virtual environment with uv...
    uv venv
    call .venv\Scripts\activate.bat
)

REM Install PyInstaller if not installed
echo.
echo Checking PyInstaller installation...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found, installing...
    uv pip install pyinstaller
)

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist build_pyinstaller rmdir /s /q build_pyinstaller 2>nul
if exist dist rmdir /s /q dist 2>nul

echo.
echo Building with PyInstaller...
echo This may take 5-10 minutes, please be patient...
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
    --hidden-import Crypto ^
    --hidden-import asyncio_throttle ^
    --hidden-import qfluentwidgets ^
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

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Build Complete!
    echo ========================================
    echo.
    if exist dist\M3U8Converter.exe (
        echo Output: dist\M3U8Converter.exe
        echo.
        for %%A in (dist\M3U8Converter.exe) do (
            set SIZE=%%~zA
            set /a SIZEMB=!SIZE! / 1048576
            echo File size: !SIZEMB! MB
        )
        echo.
        echo You can now distribute the executable!
        echo Note: Make sure FFmpeg is available on the target system.
    ) else (
        echo [WARNING] M3U8Converter.exe not found in dist/
    )
) else (
    echo.
    echo ========================================
    echo [ERROR] Build failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo   - Missing dependencies: Run 'uv pip install -r requirements.txt'
    echo   - Insufficient disk space
    echo.
)

echo.
pause
