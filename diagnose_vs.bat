@echo off
REM Visual Studio Installation Diagnostic Tool

echo ========================================
echo Visual Studio Diagnostic Tool
echo ========================================
echo.

echo Checking Visual Studio installations...
echo.

REM Check VS 2022 Build Tools
set "VS_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
if exist "%VS_PATH%" (
    echo [FOUND] Visual Studio 2022 Build Tools
    echo   Path: %VS_PATH%
    echo.
    echo Checking VC tools...
    if exist "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" (
        echo   [OK] vcvars64.bat exists
        echo.
        echo Testing compiler setup...
        call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
        where cl.exe >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo   [SUCCESS] Compiler setup works!
            cl.exe 2>&1 | findstr /C:"Microsoft (R) C/C++"
        ) else (
            echo   [ERROR] Compiler setup failed
            echo.
            echo   Workaround: Use "x64 Native Tools Command Prompt for VS 2022"
            echo   1. Press Win key
            echo   2. Search: "x64 Native Tools Command Prompt for VS 2022"
            echo   3. Open it and navigate to this project
            echo   4. Run: build_with_compiler.bat
        )
    ) else (
        echo   [ERROR] vcvars64.bat not found
        echo   Visual Studio installation may be incomplete
    )
) else (
    echo [NOT FOUND] Visual Studio 2022 Build Tools
    echo   Expected path: %VS_PATH%
)

echo.
echo.

REM Check VS 2022 Community
set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
if exist "%VS_PATH%" (
    echo [FOUND] Visual Studio 2022 Community
    echo   Path: %VS_PATH%
    if exist "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat" (
        echo   [OK] vcvars64.bat exists
    )
)

echo.
echo.

REM Check required workloads
echo Checking for C++ tools...
echo.

set "VS_DEV_CMD=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist "%VS_DEV_CMD%" (
    echo Testing C++ compiler availability...
    call "%VS_DEV_CMD%" >nul 2>&1
    where cl.exe 2>nul | findstr /C:"cl.exe" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] cl.exe is available after setup
        for /f "delims=" %%i in ('where cl.exe 2^>nul') do echo     Location: %%i
    ) else (
        echo [WARNING] cl.exe not found
        echo.
        echo This usually means "Desktop development with C++" workload
        echo was not installed during Visual Studio setup.
        echo.
        echo To fix:
        echo 1. Run Visual Studio Installer
        echo 2. Click "Modify" on your installation
        echo 3. Select "Desktop development with C++"
        echo 4. Click "Modify" to install
    )
)

echo.
echo ========================================
echo Recommended Actions:
echo ========================================
echo.
echo Option 1: Use x64 Native Tools Command Prompt (RECOMMENDED)
echo   1. Press Win key
echo   2. Search: "x64 Native Tools Command Prompt for VS 2022"
echo   3. Open it
echo   4. Navigate to: cd /d "D:\Project\m3u8-to-mp4-converter"
echo   5. Run: build_with_compiler.bat
echo.
echo Option 2: Use improved build script
echo   Run: build_with_compiler.bat
echo.
echo Option 3: Use PyInstaller (No compiler needed)
echo   Run: build_pyinstaller.bat
echo.
pause
