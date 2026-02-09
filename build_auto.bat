@echo off
REM M3U8 to MP4 Converter - Nuitka Build Script with Auto Compiler Detection
echo ========================================
echo Nuitka Build - Auto Compiler Detection
echo ========================================
echo.

REM Find and setup C compiler
set "COMPILER_FOUND="

REM Check if cl.exe is already in PATH
where cl.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MSVC compiler found in PATH
    set "COMPILER_FOUND=1"
    goto :build
)

REM Try to find Visual Studio 2022 Build Tools
set "VS2022_VCvars=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist "%VS2022_VCvars%" (
    echo [FOUND] Visual Studio 2022 Build Tools
    echo Setting up compiler environment...
    call "%VS2022_VCvars%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Compiler environment setup successful
        set "COMPILER_FOUND=1"
        goto :build
    )
)

REM Try to find Visual Studio 2019 Build Tools
set "VS2019_VCvars=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist "%VS2019_VCvars%" (
    echo [FOUND] Visual Studio 2019 Build Tools
    echo Setting up compiler environment...
    call "%VS2019_VCvars%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Compiler environment setup successful
        set "COMPILER_FOUND=1"
        goto :build
    )
)

REM Try to find Visual Studio 2022 Community/Professional
set "VS2022_Community=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
if exist "%VS2022_Community%" (
    echo [FOUND] Visual Studio 2022 Community
    echo Setting up compiler environment...
    call "%VS2022_Community%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Compiler environment setup successful
        set "COMPILER_FOUND=1"
        goto :build
    )
)

REM Check for gcc (MinGW)
where gcc.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MinGW GCC found
    set "COMPILER_FOUND=1"
    goto :build
)

REM No compiler found
echo ========================================
echo [ERROR] No C compiler found!
echo ========================================
echo.
echo Nuitka requires a C compiler to build executables.
echo.
echo Please install Visual Studio Build Tools:
echo   1. Download: https://visualstudio.microsoft.com/downloads/
echo   2. Select "Desktop development with C++"
echo   3. Run this script again
echo.
echo Detailed guide: INSTALL_COMPILER.md
echo.
pause
exit /b 1

:build
echo.
echo Starting Nuitka build...
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Check Nuitka installation
echo Checking Nuitka installation...
python -m pip show nuitka >nul 2>&1
if errorlevel 1 (
    echo Nuitka not found, installing...
    uv pip install nuitka
)

REM Clean previous build
if exist build (
    echo Cleaning previous build...
    rmdir /s /q build
)

if exist dist (
    echo Cleaning previous dist...
    rmdir /s /q dist
)

echo.
echo Building with Nuitka...
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
    --include-package=pycryptodome ^
    --include-package=asyncio_throttle ^
    --include-package=colorthief ^
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
    echo Output: dist\main.exe
    echo.
    echo File size:
    dir dist\main.exe | find "main.exe"
    echo.
    echo You can now distribute the executable!
) else (
    echo.
    echo ========================================
    echo [ERROR] Build failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo   - Missing dependencies (run: uv pip install -r requirements.txt)
    echo   - Compiler not properly installed
    echo   - Insufficient disk space
    echo.
)

echo.
pause
