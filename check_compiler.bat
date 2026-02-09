@echo off
REM Check for C compiler installation
echo ========================================
echo Checking C Compiler Installation
echo ========================================
echo.

REM Check for cl.exe (MSVC)
echo Checking for Microsoft Visual C++ Compiler...
where cl.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Microsoft Visual C++ Compiler found
    cl.exe 2>&1 | findstr /C:"Microsoft (R) C/C++"
    goto :found_msvc
)

REM Try to find VS Build Tools
echo MSVC not in PATH, checking for VS Build Tools installation...
set "VS2022_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
set "VS2019_PATH=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools"

if exist "%VS2022_PATH%" (
    echo [FOUND] Visual Studio 2022 Build Tools installed at:
    echo %VS2022_PATH%
    echo.
    echo To use it, run one of these commands:
    echo   call "%VS2022_PATH%\VC\Auxiliary\Build\vcvars64.bat"
    echo.
    echo Or use "Developer Command Prompt for VS 2022" from Start Menu
    goto :need_setup
)

if exist "%VS2019_PATH%" (
    echo [FOUND] Visual Studio 2019 Build Tools installed at:
    echo %VS2019_PATH%
    echo.
    echo To use it, run one of these commands:
    echo   call "%VS2019_PATH%\VC\Auxiliary\Build\vcvars64.bat"
    goto :need_setup
)

REM Check for gcc (MinGW)
echo.
echo Checking for MinGW GCC...
where gcc.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] MinGW GCC found
    gcc.exe --version | findstr "gcc"
    goto :found_gcc
)

REM No compiler found
echo.
echo ========================================
echo [ERROR] No C compiler found!
echo ========================================
echo.
echo Nuitka requires a C compiler to build executables.
echo.
echo Please install one of the following:
echo.
echo 1. Visual Studio Build Tools (Recommended)
echo    - Download: https://visualstudio.microsoft.com/downloads/
echo    - Select: "Desktop development with C++"
echo    - Size: ~6-8 GB download, 15 GB installed
echo.
echo 2. MinGW-w64 (Lighter alternative)
echo    - Download: https://www.msys2.org/
echo    - Install: pacman -S mingw-w64-x86_64-gcc
echo.
echo Detailed installation guide: INSTALL_COMPILER.md
echo.
pause
exit /b 1

:found_msvc
echo.
echo ========================================
echo [OK] MSVC compiler is ready!
echo You can now run: build.bat
echo ========================================
pause
exit /b 0

:found_gcc
echo.
echo ========================================
echo [OK] MinGW GCC compiler is ready!
echo You can now run: build.bat
echo ========================================
pause
exit /b 0

:need_setup
echo.
echo ========================================
echo [INFO] Compiler installed but not in PATH
echo ========================================
echo.
echo You need to setup the compiler environment first:
echo.
echo Option 1 - Use Developer Command Prompt:
echo   1. Press Win key and search: "Developer Command Prompt for VS 2022"
echo   2. Open it and navigate to this project
echo   3. Run: build.bat
echo.
echo Option 2 - Setup in current session:
echo   Run: call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo   Then run: build.bat
echo.
echo Option 3 - Use improved build script:
echo   Run: build_auto.bat  (This will auto-setup the compiler)
echo.
pause
exit /b 0
