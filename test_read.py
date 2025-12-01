import hid
import time
import os
import sys
import json

# Logitech G923 Racing Wheel
VENDOR_ID = 0x046d
PRODUCT_ID = 0xc266

# Check for command-line arguments
MONITOR_BYTE = None
CONFIG_FILE = None

if len(sys.argv) > 1:
    # Check if it's a JSON file
    if sys.argv[1].endswith('.json'):
        CONFIG_FILE = sys.argv[1]
    else:
        # Try to parse as byte number
        try:
            MONITOR_BYTE = int(sys.argv[1])
            if MONITOR_BYTE < 0 or MONITOR_BYTE > 63:
                print(f"Error: Byte must be between 0 and 63")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid argument '{sys.argv[1]}'")
            print("Usage: py test_read.py [<byte_number> | <config.json>]")
            sys.exit(1)

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_bar(value, max_value=255, bar_width=50):
    """Draw a bar chart for a value."""
    filled = int((value / max_value) * bar_width)
    bar = '█' * filled + '░' * (bar_width - filled)
    return f"{bar} {value:3d}"

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

def parse_control_value(control_config, data):
    """Parse a control value from HID data based on its configuration."""
    ctrl_type = control_config.get('type')
    
    if ctrl_type == 'analog':
        byte_idx = control_config['byte']
        if byte_idx < len(data):
            return data[byte_idx]
    
    elif ctrl_type == 'analog_16bit':
        lsb_idx = control_config['byte_lsb']
        msb_idx = control_config['byte_msb']
        if msb_idx < len(data):
            return data[lsb_idx] | (data[msb_idx] << 8)
    
    elif ctrl_type == 'button':
        byte_idx = control_config['byte']
        bit_idx = control_config['bit']
        active_val = control_config['active_value']
        if byte_idx < len(data):
            bit_val = 1 if data[byte_idx] & (1 << bit_idx) else 0
            return bit_val == active_val
    
    elif ctrl_type == 'dpad_lut':
        byte_idx = control_config['byte']
        mask = control_config['mask']
        lut = control_config['lut']
        if byte_idx < len(data):
            value = data[byte_idx] & mask
            return lut.get(str(value), 'unknown')
    
    return None

def format_control_value(name, control_config, value):
    """Format control value for display."""
    ctrl_type = control_config.get('type')
    
    if ctrl_type == 'analog' or ctrl_type == 'analog_16bit':
        min_val = control_config.get('min', 0)
        max_val = control_config.get('max', 255)
        neutral = control_config.get('neutral', (min_val + max_val) // 2)
        
        # Calculate percentage from neutral
        if value < neutral:
            pct = -100 * (neutral - value) / (neutral - min_val) if neutral != min_val else 0
        else:
            pct = 100 * (value - neutral) / (max_val - neutral) if max_val != neutral else 0
        
        return f"{name}: {value:5d} ({pct:+6.1f}%)"
    
    elif ctrl_type == 'button':
        return f"{name}: {'PRESSED' if value else 'released'}"
    
    elif ctrl_type == 'dpad_lut':
        return f"{name}: {value}"
    
    return f"{name}: {value}"

print("Opening device...")
devices = hid.enumerate()
matching = [d for d in devices if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID]

if len(matching) >= 4:
    chosen = matching[3]
    print(f"Opening: {chosen['path']}")
    
    h = hid.device()
    h.open_path(chosen['path'])
    
    # Non-blocking mode
    h.set_nonblocking(1)
    
    if CONFIG_FILE is not None:
        # Config-based monitoring mode
        config = load_config(CONFIG_FILE)
        controls = config.get('controls', {})
        
        print(f"\nLoaded configuration from: {CONFIG_FILE}")
        print(f"Monitoring {len(controls)} controls (press Ctrl+C to exit)...")
        print("=" * 60)
        
        try:
            count = 0
            last_values = {}
            
            while True:
                data = h.read(64)
                if data:
                    for name, ctrl_config in controls.items():
                        value = parse_control_value(ctrl_config, data)
                        if value is not None:
                            last_val = last_values.get(name)
                            if last_val != value:
                                count += 1
                                last_values[name] = value
                                print(f"[{count:5d}] {format_control_value(name, ctrl_config, value)}")
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        
        print(f"\nReceived {count} changes")
    
    elif MONITOR_BYTE is not None:
        # Monitor specific byte mode
        print(f"\nMonitoring byte {MONITOR_BYTE} (press Ctrl+C to exit)...")
        print("=" * 60)
        
        try:
            count = 0
            last_value = None
            
            while True:
                data = h.read(64)
                if data and len(data) > MONITOR_BYTE:
                    value = data[MONITOR_BYTE]
                    if value != last_value:
                        count += 1
                        last_value = value
                        print(f"[{count:5d}] Byte {MONITOR_BYTE}: {value:3d}")
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        
        print(f"\nReceived {count} changes")
    else:
        # Visual bar chart mode
        print("\nReading data (move wheel or press buttons)...")
        print("Tip: Run with 'py test_read.py <byte_number>' to monitor a specific byte")
        print("      Run with 'py test_read.py wheel_config.json' to monitor controls")
        print("Press Ctrl+C to exit\n")
        time.sleep(2)
        
        try:
            count = 0
            last_data = None
            
            while True:
                data = h.read(64)
                if data:
                    # Check if data changed (ignoring byte 4)
                    should_update = False
                    if last_data is None:
                        should_update = True
                    else:
                        for i in range(min(len(data), len(last_data))):
                            if i != 4 and data[i] != last_data[i]:
                                should_update = True
                                break
                    
                    if should_update:
                        count += 1
                        last_data = list(data)
                        
                        # Clear screen and redraw
                        clear_screen()
                        print(f"USB HID Data Visualization - Message #{count}")
                        print("=" * 60)
                        
                        # Show first 12 bytes as bar charts
                        for i in range(min(12, len(data))):
                            print(f"Byte {i:2d}: {draw_bar(data[i])}")
                        
                        print("=" * 60)
                        print("Press Ctrl+C to exit")
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        
        print(f"\nReceived {count} messages")
    
    h.close()
else:
    print(f"Error: Need at least 4 interfaces, found {len(matching)}")
