@echo off
REM M3U8 to MP4 Converter - Fixed Nuitka Build Script
REM This script handles Nuitka issues with aiohttp and other C extensions

setlocal EnableDelayedExpansion

echo ========================================
echo M3U8 to MP4 Converter - Nuitka Build
echo ========================================
echo.

REM Define Visual Studio paths
set "VS2022_BUILDTOOLS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
set "VS2022_COMMUNITY=C:\Program Files\Microsoft Visual Studio\2022\Community"
set "VS2022_PROFESSIONAL=C:\Program Files\Microsoft Visual Studio\2022\Professional"
set "VS2022_ENTERPRISE=C:\Program Files\Microsoft Visual Studio\2022\Enterprise"

REM Find and setup compiler
set "VCVARS="
if exist "%VS2022_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Build Tools
) else if exist "%VS2022_COMMUNITY%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_COMMUNITY%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Community
) else if exist "%VS2022_PROFESSIONAL%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_PROFESSIONAL%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Professional
) else if exist "%VS2022_ENTERPRISE%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_ENTERPRISE%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Enterprise
)

if defined VCVARS (
    echo Setting up compiler environment...
    call "!VCVARS!" >nul 2>&1
    echo [OK] Compiler environment ready
) else (
    echo [WARNING] VS compiler not found in standard locations
    echo Attempting to build anyway...
)

echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check and update Nuitka
echo.
echo Checking Nuitka installation...
python -m pip show nuitka >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Nuitka not found, installing latest version...
    uv pip install nuitka
) else (
    echo [OK] Nuitka is installed
    echo Updating Nuitka to latest version...
    uv pip install --upgrade nuitka
)

REM Clean previous build
echo.
echo Cleaning previous build...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul

echo.
echo ========================================
echo Starting Nuitka Build
echo ========================================
echo.
echo This may take 10-20 minutes, please be patient...
echo.

REM Build with Nuitka using safer options
REM Using --nofollow-import-to for problematic C modules
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
    --include-package=Crypto ^
    --include-package=asyncio_throttle ^
    --include-package=qfluentwidgets ^
    --nofollow-import-to=aiohttp._websocket.reader_c ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=PIL._tkinter_finder ^
    --nofollow-import-to=test ^
    --nofollow-import-to=tests ^
    --nofollow-import-to=distutils ^
    --assume-yes-for-downloads ^
    --remove-output ^
    --output-dir=dist ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Build Complete!
    echo ========================================
    echo.
    if exist dist\main.exe (
        echo Output: dist\main.exe
        echo.
        for %%A in (dist\main.exe) do (
            set SIZE=%%~zA
            set /a SIZEMB=!SIZE! / 1048576
            echo File size: !SIZEMB! MB
        )
        echo.
        echo You can now distribute the executable!
    ) else (
        echo [WARNING] main.exe not found in dist/
    )
) else (
    echo.
    echo ========================================
    echo [ERROR] Build failed!
    echo ========================================
    echo.
    echo The build encountered an error. This is usually due to:
    echo   1. Nuitka compatibility issues with certain modules
    echo   2. Insufficient memory
    echo   3. C extension compilation errors
    echo.
    echo RECOMMENDED: Use PyInstaller instead (more reliable):
    echo   Run: build_pyinstaller.bat
    echo.
    echo Or try:
    echo   1. Close other applications to free memory
    echo   2. Update Nuitka: uv pip install --upgrade nuitka
    echo   3. Run this script again
    echo.
)

echo.
pause
