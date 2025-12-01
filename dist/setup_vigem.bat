@echo off
echo ========================================
echo ViGEmBus Driver Setup
echo ========================================
echo.
echo This script will download and install ViGEmBus driver
echo which is required for virtual gamepad functionality.
echo.
pause

echo.
echo Downloading ViGEmBus installer...
echo.

REM Download ViGEmBus installer using PowerShell
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/ViGEmBus_1.22.0_x64_x86_arm64.exe' -OutFile 'ViGEmBus_Setup.exe'}"

if not exist ViGEmBus_Setup.exe (
    echo.
    echo ERROR: Failed to download ViGEmBus installer.
    echo.
    echo Please manually download from:
    echo https://github.com/nefarius/ViGEmBus/releases/latest
    echo.
    pause
    exit /b 1
)

echo.
echo Download complete!
echo.
echo Installing ViGEmBus driver...
echo (Administrator privileges required)
echo.

REM Run installer
ViGEmBus_Setup.exe

echo.
echo ========================================
echo Setup Complete
echo ========================================
echo.
echo After ViGEmBus installation completes:
echo 1. Restart your computer if prompted
echo 2. Run WheelEmulator.exe
echo.
echo Note: Keep wheel_config.json in the same folder as WheelEmulator.exe
echo.
pause

REM Clean up installer
if exist ViGEmBus_Setup.exe del ViGEmBus_Setup.exe
