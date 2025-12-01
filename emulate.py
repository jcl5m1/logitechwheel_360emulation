import hid
import time
import json
import sys

try:
    import vgamepad as vg
except ImportError:
    print("Error: vgamepad library not installed")
    print("Install it with: pip install vgamepad")
    sys.exit(1)

try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    print("Error: win32gui or psutil library not installed")
    print("Install them with: pip install pywin32 psutil")
    sys.exit(1)

# Controller type selection
USE_XBOX_CONTROLLER = True  # Set to False to use DS4 controller

CONFIG_FILE = 'wheel_config.json'

def load_config(filename):
    """Load wheel configuration from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{filename}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filename}': {e}")
        sys.exit(1)

def parse_button_value(control_config, data):
    """Parse a button value from HID data based on its configuration."""
    if control_config.get('type') != 'button':
        return False
    
    byte_idx = control_config['byte']
    bit_idx = control_config['bit']
    active_val = control_config['active_value']
    
    if byte_idx < len(data):
        bit_val = 1 if data[byte_idx] & (1 << bit_idx) else 0
        return bit_val == active_val
    
    return False

def parse_dpad_value(control_config, data):
    """Parse D-pad value from HID data and convert to 4-bit direction state."""
    if control_config.get('type') != 'dpad_lut':
        return {'up': False, 'down': False, 'left': False, 'right': False}
    
    byte_idx = control_config['byte']
    mask = control_config['mask']
    lut = control_config['lut']
    
    # Default state: all directions off
    directions = {'up': False, 'down': False, 'left': False, 'right': False}
    
    if byte_idx < len(data):
        value = data[byte_idx] & mask
        dpad_string = lut.get(str(value), 'none')
        
        # Convert LUT string to individual direction states
        if dpad_string != 'none':
            if 'up' in dpad_string:
                directions['up'] = True
            if 'down' in dpad_string:
                directions['down'] = True
            if 'left' in dpad_string:
                directions['left'] = True
            if 'right' in dpad_string:
                directions['right'] = True
    
    return directions

def parse_analog_value(control_config, data):
    """Parse an analog value from HID data."""
    if control_config.get('type') != 'analog':
        return 0
    
    byte_idx = control_config['byte']
    min_val = control_config.get('min', 0)
    max_val = control_config.get('max', 255)
    neutral = control_config.get('neutral', 255)
    
    if byte_idx < len(data):
        raw_value = data[byte_idx]
        # Invert value: neutral (255) = 0, fully pressed (0) = 255
        inverted = max_val - raw_value
        return inverted
    
    return 0

def get_foreground_application():
    """Get the name of the currently active foreground application."""
    try:
        # Get foreground window handle
        hwnd = win32gui.GetForegroundWindow()
        
        # Get process ID from window handle
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Get process info
        process = psutil.Process(pid)
        app_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)
        
        return {
            'name': app_name,
            'title': window_title,
            'pid': pid
        }
    except Exception as e:
        return {
            'name': 'Unknown',
            'title': '',
            'pid': 0
        }

# Button mapping for DS4 controller
DS4_BUTTON_MAP = {
    'cross': vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
    'circle': vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
    'square': vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
    'triangle': vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
    'L2': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
    'R2': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
    'L3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
    'R3': vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
    'share': vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
    'option': vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
    'PS': vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
    'paddleLeft': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
    'paddleRight': vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
    # D-pad directions as buttons
    'dpad-up': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
    'dpad-down': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
    'dpad-left': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
    'dpad-right': vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST,
}

# Button mapping for Xbox controller
XBOX_BUTTON_MAP = {
    'cross': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'circle': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'square': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    'triangle': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    'L2': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'R2': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'L3': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    'R3': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    'share': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    'option': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    'PS': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    'paddleLeft': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'paddleRight': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    # D-pad directions as buttons
    'dpad-up': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    'dpad-down': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    'dpad-left': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    'dpad-right': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

def main():
    # Load configuration
    print(f"Loading configuration from {CONFIG_FILE}...")
    config = load_config(CONFIG_FILE)
    
    device_config = config['device']
    controls = config['controls']
    
    VENDOR_ID = device_config['vendor_id']
    PRODUCT_ID = device_config['product_id']
    INTERFACE = device_config['interface']
    
    # Find and open the HID device
    print(f"Opening {device_config['name']}...")
    devices = hid.enumerate()
    matching = [d for d in devices if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID]
    
    if len(matching) < INTERFACE + 1:
        print(f"Error: Need at least {INTERFACE + 1} interfaces, found {len(matching)}")
        sys.exit(1)
    
    chosen = matching[INTERFACE]
    print(f"Opening interface {INTERFACE}: {chosen['path']}")
    
    h = hid.device()
    h.open_path(chosen['path'])
    h.set_nonblocking(1)
    
    # Create virtual gamepad based on controller type
    if USE_XBOX_CONTROLLER:
        print("Creating virtual Xbox 360 gamepad...")
        gamepad = vg.VX360Gamepad()
        BUTTON_MAP = XBOX_BUTTON_MAP
        controller_name = "Xbox 360"
    else:
        print("Creating virtual DualShock 4 gamepad...")
        gamepad = vg.VDS4Gamepad()
        BUTTON_MAP = DS4_BUTTON_MAP
        controller_name = "DualShock 4"
    
    print(f"\nGamepad emulation started ({controller_name})!")
    print("Press wheel buttons to emulate gamepad buttons")
    print("Press Ctrl+C to exit\n")
    print("=" * 60)
    
    # Extract button and dpad controls
    button_controls = {name: ctrl for name, ctrl in controls.items() if ctrl.get('type') == 'button'}
    dpad_control = None
    dpad_name = None
    for name, ctrl in controls.items():
        if ctrl.get('type') == 'dpad_lut':
            dpad_control = ctrl
            dpad_name = name
            break
    
    # Extract analog controls (throttle and brake)
    throttle_control = controls.get('throttle') if 'throttle' in controls else None
    brake_control = controls.get('brake') if 'brake' in controls else None
    
    # Track button states (unified for regular buttons and d-pad directions)
    last_button_states = {name: False for name in button_controls.keys()}
    last_button_states['dpad-up'] = False
    last_button_states['dpad-down'] = False
    last_button_states['dpad-left'] = False
    last_button_states['dpad-right'] = False
    
    # Track analog trigger values
    last_throttle_value = 0
    last_brake_value = 0
    
    # Track last data for change detection
    last_data = None
    
    # Track foreground application
    last_foreground_app = None
    app_check_counter = 0
    APP_CHECK_INTERVAL = 100  # Check every 100 iterations
    
    try:
        update_count = 0
        
        while True:
            # Check foreground application periodically
            app_check_counter += 1
            if app_check_counter >= APP_CHECK_INTERVAL:
                app_check_counter = 0
                current_app = get_foreground_application()
                
                if last_foreground_app is None or current_app['name'] != last_foreground_app['name']:
                    print(f"\n{'='*60}")
                    print(f"[FOREGROUND APP CHANGED]")
                    print(f"  Application: {current_app['name']}")
                    print(f"  Window Title: {current_app['title']}")
                    print(f"  PID: {current_app['pid']}")
                    print(f"{'='*60}\n")
                    last_foreground_app = current_app
            
            data = h.read(64)
            if data:
                # Convert to mutable list for modification
                data = list(data)
                
                # Store byte 5 (steering MSB) before zeroing byte 4
                steering_msb = data[5] if len(data) > 5 else 0
                
                # Zero out byte 4 (steering LSB) before comparison
                data[4] = 0
                
                # Change detection: skip if data hasn't changed
                # But always process if byte 5 (steering MSB) has changed
                steering_changed = False
                if last_data is not None:
                    if len(last_data) > 5:
                        steering_changed = (steering_msb != last_data[5])
                    
                    if data == last_data and not steering_changed:
                        time.sleep(0.001)  # Shorter sleep since we're skipping processing
                        continue
                
                # Store current data for next comparison
                last_data = data.copy()
                
                # Parse steering MSB (byte 5) and map to left joystick X-axis with 5x sensitivity
                if USE_XBOX_CONTROLLER and len(data) > 5:
                    # Apply 5x sensitivity: Map 0-255 to -32768 to 32767 with 5x multiplier
                    # Center at 128: 0→-32768, 128→0, 255→32767
                    joystick_raw = (steering_msb - 128) * 5 * (32767 / 127)
                    
                    # Clamp to prevent wrap-around
                    joystick_x = int(max(-32768, min(32767, joystick_raw)))
                    
                    gamepad.left_joystick(x_value=joystick_x, y_value=0)
                    
                    # Send update if steering changed
                    if steering_changed:
                        gamepad.update()
                
                # Create current state dictionary
                current_states = {}
                
                # Parse D-pad state first (special handling using LUT)
                if dpad_control:
                    dpad_directions = parse_dpad_value(dpad_control, data)
                    current_states['dpad-up'] = dpad_directions['up']
                    current_states['dpad-down'] = dpad_directions['down']
                    current_states['dpad-left'] = dpad_directions['left']
                    current_states['dpad-right'] = dpad_directions['right']
                else:
                    current_states['dpad-up'] = False
                    current_states['dpad-down'] = False
                    current_states['dpad-left'] = False
                    current_states['dpad-right'] = False
                
                # Parse all regular button states
                for name, ctrl_config in button_controls.items():
                    current_states[name] = parse_button_value(ctrl_config, data)
                
                # Parse analog triggers (Xbox only)
                trigger_updated = False
                if USE_XBOX_CONTROLLER:
                    if throttle_control:
                        throttle_value = parse_analog_value(throttle_control, data)
                        if throttle_value != last_throttle_value:
                            gamepad.right_trigger(value=throttle_value)
                            last_throttle_value = throttle_value
                            trigger_updated = True
                    
                    if brake_control:
                        brake_value = parse_analog_value(brake_control, data)
                        if brake_value != last_brake_value:
                            gamepad.left_trigger(value=brake_value)
                            last_brake_value = brake_value
                            trigger_updated = True
                    
                    # Update gamepad if triggers changed
                    if trigger_updated:
                        gamepad.update()
                
                # Process all button state changes (unified handling)
                for name, new_state in current_states.items():
                    old_state = last_button_states.get(name, False)
                    
                    if new_state != old_state and name in BUTTON_MAP:
                        gamepad_button = BUTTON_MAP[name]
                        
                        if new_state:
                            gamepad.press_button(button=gamepad_button)
                            print(f"[{update_count:5d}] {name:15s} -> PRESSED")
                        else:
                            gamepad.release_button(button=gamepad_button)
                            print(f"[{update_count:5d}] {name:15s} -> released")
                        
                        gamepad.update()
                        update_count += 1
                        last_button_states[name] = new_state
                
                # Print D-pad state when it changes (for Xbox, dpad buttons are handled above)
                if not USE_XBOX_CONTROLLER:
                    dpad_changed = (
                        current_states.get('dpad-up', False) != last_button_states.get('dpad-up', False) or
                        current_states.get('dpad-down', False) != last_button_states.get('dpad-down', False) or
                        current_states.get('dpad-left', False) != last_button_states.get('dpad-left', False) or
                        current_states.get('dpad-right', False) != last_button_states.get('dpad-right', False)
                    )
                    
                    if dpad_changed:
                        # Print current virtual gamepad D-pad state
                        active_dirs = []
                        if current_states.get('dpad-up', False):
                            active_dirs.append('up')
                        if current_states.get('dpad-down', False):
                            active_dirs.append('down')
                        if current_states.get('dpad-left', False):
                            active_dirs.append('left')
                        if current_states.get('dpad-right', False):
                            active_dirs.append('right')
                        
                        state_str = '-'.join(active_dirs) if active_dirs else 'none'
                        print(f"[{update_count:5d}] Virtual D-pad: {state_str}")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nStopping gamepad emulation...")
    
    # Clean up
    print("Releasing all buttons...")
    for name in list(button_controls.keys()) + ['dpad-up', 'dpad-down', 'dpad-left', 'dpad-right']:
        if name in BUTTON_MAP:
            gamepad.release_button(button=BUTTON_MAP[name])
    
    gamepad.update()
    
    h.close()
    print(f"\nTotal updates: {update_count}")
    print("Gamepad emulation stopped")

if __name__ == '__main__':
    main()
