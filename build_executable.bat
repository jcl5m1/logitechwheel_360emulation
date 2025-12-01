@echo off
echo ========================================
echo Building Wheel Emulator Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

echo Building executable...
echo.

pyinstaller --onefile --add-data "wheel_config.json;." --console --name "WheelEmulator" --clean emulate.py

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
