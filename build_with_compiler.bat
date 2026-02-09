@echo off
REM M3U8 to MP4 Converter - Improved Nuitka Build Script
REM This script will automatically setup the MSVC compiler environment

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
set "VS2019_BUILDTOOLS=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools"

REM Function to setup compiler
:setup_compiler
set "VCVARS="
if exist "%VS2022_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Build Tools
    goto :compiler_found
)
if exist "%VS2022_COMMUNITY%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_COMMUNITY%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Community
    goto :compiler_found
)
if exist "%VS2022_PROFESSIONAL%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_PROFESSIONAL%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Professional
    goto :compiler_found
)
if exist "%VS2022_ENTERPRISE%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2022_ENTERPRISE%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2022 Enterprise
    goto :compiler_found
)
if exist "%VS2019_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=%VS2019_BUILDTOOLS%\VC\Auxiliary\Build\vcvars64.bat"
    echo [FOUND] Visual Studio 2019 Build Tools
    goto :compiler_found
)

echo [ERROR] Visual Studio not found!
echo.
echo Please install Visual Studio Build Tools:
echo   1. Download: https://aka.ms/vs/17/release/vs_buildtools.exe
echo   2. Select: "Desktop development with C++"
echo.
pause
exit /b 1

:compiler_found
echo.
echo Setting up compiler environment...
call "!VCVARS!" >nul 2>&1

REM Verify compiler is available
where cl.exe >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to setup compiler environment!
    echo.
    echo Please try using "Developer Command Prompt for VS 2022":
    echo   1. Press Win key
    echo   2. Search: "Developer Command Prompt for VS 2022"
    echo   3. Open it and run: build_with_compiler.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Compiler environment setup successful
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

REM Check Nuitka installation
echo.
echo Checking Nuitka installation...
python -m pip show nuitka >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Nuitka not found, installing...
    uv pip install nuitka
) else (
    echo [OK] Nuitka is installed
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
echo This may take 5-15 minutes, please be patient...
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
    --include-package=Crypto ^
    --include-package=asyncio_throttle ^
    --include-package=qfluentwidgets ^
    --nofollow-import-to=tkinter ^
    --nofollow-import-to=matplotlib ^
    --nofollow-import-to=PIL._tkinter_finder ^
    --nofollow-import-to=test ^
    --nofollow-import-to=tests ^
    --remove-output ^
    --output-dir=dist ^
    --show-progress ^
    --show-memory ^
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
        echo File size:
        for %%A in (dist\main.exe) do echo %%~zA bytes
        dir dist\main.exe | find "main.exe"
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
    echo Please check the error messages above.
    echo.
    echo Common issues:
    echo   - Missing dependencies
    echo     Run: uv pip install -r requirements.txt
    echo.
    echo   - Compiler not properly installed
    echo     Check: check_compiler.bat
    echo.
    echo   - Insufficient disk space
    echo.
)

echo.
pause
