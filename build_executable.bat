@echo off
echo ========================================
echo Building Wheel Emulator Executable
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found in PATH. Downloading Python 3.11 installer...
    curl -# -o python-installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if exist python-installer.exe (
        echo Installing Python silently. This may take a few minutes...
        start /wait python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
        del python-installer.exe
        echo Python installation complete!
        echo Reloading environment variables to detect Python...
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do call set "PATH=%%B;%%PATH%%"
    ) else (
        echo Failed to download Python installer. Please install manually from python.org
        pause
        exit /b
    )
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    echo.
)

echo Building executable...
echo.

python -m PyInstaller --onefile --add-data "wheel_config.json;." --console --name "WheelEmulator" --clean emulate.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\WheelEmulator.exe
echo.
echo To run the emulator:
echo 1. Copy wheel_config.json to the same folder as WheelEmulator.exe
echo 2. Run WheelEmulator.exe
echo.
echo Note: ViGEmBus driver must be installed on the target system
echo.
pause
