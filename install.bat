@echo off
REM IEQ Analytics CLI Installation Script for Windows
REM This script installs the IEQ Analytics CLI as a global command: ieq-analyzer

setlocal enabledelayedexpansion

echo.
echo 🏢 IEQ Analytics CLI Installation (Windows)
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python %PYTHON_VERSION% found

REM Check if pip is installed
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed
    echo Please install pip or reinstall Python with pip included
    pause
    exit /b 1
)

echo [INFO] pip found

REM Parse command line arguments
set GLOBAL_INSTALL=false
set DEV_INSTALL=false

:parse_args
if "%1"=="--global" (
    set GLOBAL_INSTALL=true
    shift
    goto parse_args
)
if "%1"=="--dev" (
    set DEV_INSTALL=true
    shift
    goto parse_args
)
if "%1"=="--help" (
    goto show_help
)
if "%1"=="-h" (
    goto show_help
)

REM Setup virtual environment if not global install
if "%GLOBAL_INSTALL%"=="false" (
    echo [INFO] Setting up virtual environment...
    
    if not exist "venv_ieq" (
        python -m venv venv_ieq
        echo [SUCCESS] Virtual environment created: venv_ieq
    ) else (
        echo [WARNING] Virtual environment already exists: venv_ieq
    )
    
    REM Activate virtual environment
    call venv_ieq\Scripts\activate.bat
    echo [SUCCESS] Virtual environment activated
    
    REM Upgrade pip
    python -m pip install --upgrade pip
) else (
    echo [WARNING] Installing globally (not recommended for production)
)

REM Install the CLI package
echo [INFO] Installing IEQ Analytics CLI...

if "%DEV_INSTALL%"=="true" (
    python -m pip install -e .
    echo [SUCCESS] IEQ Analytics CLI installed in development mode
) else (
    python -m pip install .
    echo [SUCCESS] IEQ Analytics CLI installed
)

REM Test the installation
echo [INFO] Testing installation...

where ieq-analyzer >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] ieq-analyzer command is available
    
    REM Show help
    echo [INFO] CLI Help:
    echo ==========================
    ieq-analyzer --help
    echo ==========================
) else (
    echo [ERROR] ieq-analyzer command not found in PATH
    echo [WARNING] You may need to restart your command prompt or add the installation directory to PATH
    
    REM Try to find where it was installed
    python -c "import sys; print('Python Scripts directory: ' + sys.prefix + '\\Scripts')"
)

REM Create uninstall script
echo [INFO] Creating uninstall script...

echo @echo off > uninstall.bat
echo echo [INFO] Uninstalling IEQ Analytics CLI... >> uninstall.bat
echo python -m pip uninstall ieq-analyzer -y >> uninstall.bat
echo if exist "venv_ieq" ( >> uninstall.bat
echo     set /p "choice=Remove virtual environment (venv_ieq)? [y/N]: " >> uninstall.bat
echo     if /i "!choice!"=="y" ( >> uninstall.bat
echo         rmdir /s /q venv_ieq >> uninstall.bat
echo         echo [SUCCESS] Virtual environment removed >> uninstall.bat
echo     ) >> uninstall.bat
echo ) >> uninstall.bat
echo echo [SUCCESS] IEQ Analytics CLI uninstalled >> uninstall.bat
echo pause >> uninstall.bat

echo [SUCCESS] Uninstall script created: uninstall.bat

echo.
echo [SUCCESS] 🎉 Installation completed successfully!
echo.
echo 📚 Quick Start:
echo    ieq-analyzer --help                           # Show help
echo    ieq-analyzer mapping --help                   # Map raw data
echo    ieq-analyzer analyze --help                   # Analyze data
echo    ieq-analyzer rules create --interactive       # Create rules
echo    ieq-analyzer report from-yaml --interactive   # Generate reports
echo.
echo 🗑️  To uninstall: uninstall.bat
echo.

pause
exit /b 0

:show_help
echo.
echo 🏢 IEQ Analytics CLI Installation Script (Windows)
echo.
echo Usage: %0 [OPTIONS]
echo.
echo OPTIONS:
echo     --global    Install globally (not recommended)
echo     --dev       Install in development mode
echo     --help      Show this help message
echo.
echo EXAMPLES:
echo     %0                  # Install in virtual environment (recommended)
echo     %0 --dev            # Install in development mode
echo     %0 --global         # Install globally (not recommended)
echo.
echo POST-INSTALLATION:
echo     After installation, you can use the CLI with:
echo.
echo     ieq-analyzer --help                           # Show help
echo     ieq-analyzer mapping --help                   # Map raw data
echo     ieq-analyzer analyze --help                   # Analyze data
echo     ieq-analyzer rules create --interactive       # Create rules
echo     ieq-analyzer report from-yaml --interactive   # Generate reports
echo.
pause
exit /b 0
