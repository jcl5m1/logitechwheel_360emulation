========================================
Wheel Emulator - README
========================================

This package contains everything needed to emulate your Logitech G923 Racing Wheel as an Xbox 360 controller.

========================================
CONTENTS
========================================

1. WheelEmulator.exe     - Main application
2. wheel_config.json     - Configuration file
3. setup_vigem.bat       - ViGEmBus driver installer
4. README.txt            - This file

========================================
FIRST TIME SETUP
========================================

1. Run setup_vigem.bat (ONE TIME ONLY)
   - This downloads and installs the ViGEmBus driver
   - Administrator privileges required
   - Restart computer if prompted

2. After restart, you're ready to use the emulator!

========================================
HOW TO USE
========================================

1. Connect your Logitech G923 Racing Wheel to PC
2. Double-click WheelEmulator.exe
3. The program will create a virtual Xbox 360 controller
4. Your wheel buttons/pedals are now mapped to gamepad inputs
5. Launch your game and use the wheel!
6. Press Ctrl+C in the console window to stop

========================================
BUTTON MAPPING
========================================

Physical Wheel          →  Xbox 360 Controller
----------------           -------------------
Cross (X)              →  A Button
Circle (O)             →  B Button
Square (□)             →  X Button
Triangle (△)           →  Y Button
L2                     →  Left Bumper (LB)
R2                     →  Right Bumper (RB)
L3                     →  Left Stick Click
R3                     →  Right Stick Click
Share                  →  Back Button
Options                →  Start Button
PS Button              →  Guide Button
D-Pad                  →  D-Pad (all 8 directions)
Brake Pedal            →  Left Trigger (LT)
Throttle Pedal         →  Right Trigger (RT)

========================================
TROUBLESHOOTING
========================================

Problem: "Device not found" error
Solution: Ensure wheel is plugged in and powered on

Problem: Buttons don't work
Solution: Check wheel_config.json is in same folder as .exe

Problem: Virtual controller not detected
Solution: Run setup_vigem.bat again to reinstall driver

Problem: Application won't start
Solution: Make sure wheel_config.json exists

========================================
CONFIGURATION
========================================

Edit wheel_config.json to customize button mappings or add new controls.
Do not modify if you're not familiar with JSON format.

========================================
SYSTEM REQUIREMENTS
========================================

- Windows 10/11
- Logitech G923 Racing Wheel
- ViGEmBus Driver (installed via setup_vigem.bat)

========================================
CREDITS
========================================

Created using:
- Python with hidapi, vgamepad libraries
- ViGEmBus virtual gamepad driver

========================================
SUPPORT
========================================

For issues, ensure:
1. ViGEmBus driver is installed
2. Wheel is connected and recognized by Windows
3. wheel_config.json is present
4. You have administrator privileges

========================================
