import hid
import time
import json

# Logitech G923 Racing Wheel
VENDOR_ID = 0x046d
PRODUCT_ID = 0xc266
MAX_REPORT_LENGTH = 64

# Define all inputs to calibrate
ANALOG_INPUTS = [
    ('steering', 'Turn the steering wheel LEFT or RIGHT'),
    ('throttle', 'Press the THROTTLE pedal'),
    ('brake', 'Press the BRAKE pedal'),
    ('clutch', 'Press the CLUTCH pedal')
]

BUTTON_INPUTS = [
    ('up', 'Press D-PAD UP'),
    ('down', 'Press D-PAD DOWN'),
    ('left', 'Press D-PAD LEFT'),
    ('right', 'Press D-PAD RIGHT'),
    ('square', 'Press SQUARE button'),
    ('triangle', 'Press TRIANGLE button'),
    ('circle', 'Press CIRCLE button'),
    ('cross', 'Press CROSS button'),
    ('paddleLeft', 'Pull LEFT PADDLE'),
    ('paddleRight', 'Pull RIGHT PADDLE'),
    ('L2', 'Press L2 button'),
    ('L3', 'Press L3 button'),
    ('R2', 'Press R2 button'),
    ('R3', 'Press R3 button'),
    ('plus', 'Press PLUS button'),
    ('minus', 'Press MINUS button'),
    ('scrollRight', 'Scroll RIGHT'),
    ('scrollLeft', 'Scroll LEFT'),
    ('enter', 'Press ENTER button'),
    ('share', 'Press SHARE button'),
    ('option', 'Press OPTION button'),
    ('PS', 'Press PS button')
]

def open_device():
    """Open the HID device and return the handle."""
    devices = hid.enumerate()
    matching = [d for d in devices if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID]
    
    if not matching:
        raise IOError(f"No device found with VID=0x{VENDOR_ID:04x} PID=0x{PRODUCT_ID:04x}")
    
    if len(matching) < 4:
        raise IOError(f"Expected at least 4 interfaces, but found only {len(matching)}")
    
    chosen = matching[3]  # Interface 4 (MI_00)
    h = hid.device()
    h.open_path(chosen['path'])
    h.set_nonblocking(0)  # Blocking mode for reliable reads
    return h

def clear_buffer(h):
    """Clear any pending data from the read buffer."""
    h.set_nonblocking(1)
    while h.read(MAX_REPORT_LENGTH):
        pass
    h.set_nonblocking(0)

def read_data_stream(h, duration=1.0):
    """Read data for a duration and return all samples."""
    samples = []
    start = time.time()
    while time.time() - start < duration:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=100)
        if data:
            samples.append(list(data))
    return samples

def find_analog_byte(samples):
    """Find which byte varies the most (analog input)."""
    if not samples:
        return None, None, None
    
    # Calculate variance for each byte position
    variances = {}
    num_bytes = len(samples[0])
    
    for byte_idx in range(num_bytes):
        values = [s[byte_idx] for s in samples]
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            variances[byte_idx] = {
                'variance': variance,
                'min': min(values),
                'max': max(values),
                'mean': mean
            }
    
    if not variances:
        return None, None, None
    
    # Find byte with highest variance
    sorted_vars = sorted(variances.items(), key=lambda x: x[1]['variance'], reverse=True)
    byte_idx, info = sorted_vars[0]
    
    return byte_idx, info['min'], info['max']

def get_neutral_baseline(samples, analog_bytes):
    """Get baseline from samples where analog values are near neutral."""
    if not samples or not analog_bytes:
        return samples[-1] if samples else None
    
    # Find samples where analog bytes are near their neutral/center
    neutral_samples = []
    for sample in samples:
        is_neutral = True
        for byte_idx, (min_val, max_val, neutral) in analog_bytes.items():
            value = sample[byte_idx]
            # Check if value is close to neutral (within 10% of range)
            range_size = max_val - min_val
            tolerance = max(5, range_size * 0.1)
            if abs(value - neutral) > tolerance:
                is_neutral = False
                break
        if is_neutral:
            neutral_samples.append(sample)
    
    # Return the most common neutral sample
    if neutral_samples:
        return neutral_samples[-1]
    return samples[-1]

def calibrate_steering(h):
    """Calibrate steering (16-bit: byte 4=LSB, byte 5=MSB) and establish baseline."""
    print("\n" + "="*60)
    print("PART 1: STEERING & BASELINE")
    print("="*60)
    print("\n[1/26] STEERING (16-bit)")
    print("  → Turn the steering wheel LEFT")
    print("  Waiting for input...", end='', flush=True)
    
    # Wait for any data (steering movement) - no timeout, wait as long as needed
    data = h.read(MAX_REPORT_LENGTH)
    if not data:
        print("  ⚠ Failed to read data")
        return None, None, None
    
    print(" ✓ Detected!", flush=True)
    print("  → Keep turning to MAXIMUM LEFT (hold at limit until auto-advance)...")
    
    # Collect samples while turning left - wait for 1 second of no data
    left_samples = []
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=1000)  # 1 second timeout
        if data:
            left_samples.append(list(data))
        else:
            # No data for 1 second - advance
            break
    
    print("  → Now turn to CENTER (hold until auto-advance)...")
    center_samples = []
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=1000)
        if data:
            center_samples.append(list(data))
        else:
            break
    
    print("  → Now turn to MAXIMUM RIGHT (hold until auto-advance)...")
    right_samples = []
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=1000)
        if data:
            right_samples.append(list(data))
        else:
            break
    
    print("  → Return to CENTER (hold until auto-advance)...")
    final_center = []
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=1000)
        if data:
            final_center.append(list(data))
        else:
            break
    
    # Steering is 16-bit: byte 4 (LSB) + byte 5 (MSB)
    all_samples = left_samples + center_samples + right_samples + final_center
    
    if not all_samples:
        print("  ⚠ No samples collected")
        return None, None, None
    
    # Calculate 16-bit values from all samples
    steering_values = []
    for sample in all_samples:
        if len(sample) > 5:
            # Combine byte 4 (LSB) and byte 5 (MSB) into 16-bit value
            value_16bit = sample[4] | (sample[5] << 8)
            steering_values.append(value_16bit)
    
    if not steering_values:
        print("  ⚠ Failed to extract steering values")
        return None, None, None
    
    min_val = min(steering_values)
    max_val = max(steering_values)
    
    # Calculate neutral from center samples
    center_values = []
    for sample in (center_samples + final_center):
        if len(sample) > 5:
            value_16bit = sample[4] | (sample[5] << 8)
            center_values.append(value_16bit)
    
    neutral = sum(center_values) // len(center_values) if center_values else (min_val + max_val) // 2
    
    steering_config = {
        'type': 'analog_16bit',
        'byte_lsb': 4,
        'byte_msb': 5,
        'min': min_val,
        'max': max_val,
        'neutral': neutral
    }
    
    print(f"  ✓ Bytes 4 (LSB) + 5 (MSB), range [{min_val}-{max_val}], neutral={neutral}")
    
    # Get baseline from final center position
    baseline = final_center[-1] if final_center else all_samples[-1]
    
    # Mark both bytes 4 and 5 as analog so they're ignored during button detection
    analog_bytes = {
        4: (0, 255, baseline[4]),  # LSB
        5: (0, 255, baseline[5])   # MSB
    }
    
    print(f"\n✓ Baseline established from neutral position")
    print(f"  Data: {baseline[:12]}...")
    
    return steering_config, baseline, analog_bytes

def calibrate_analog(h, input_name, instruction, baseline, analog_bytes, index, total):
    """Calibrate an analog input (pedals)."""
    print(f"\n[{index}/{total}] {input_name.upper()}")
    print(f"  → {instruction}")
    print("  Waiting for input...", end='', flush=True)
    
    # Wait for initial detection - no timeout, wait as long as needed
    samples = []
    detected = False
    
    while not detected:
        data = h.read(MAX_REPORT_LENGTH)
        if data:
            # Check if we've seen a significant change in any non-analog byte (threshold > 50, any direction)
            for i in range(len(data)):
                if i not in analog_bytes:
                    change = abs(data[i] - baseline[i])
                    if change > 50:
                        detected = True
                        print(" ✓ Detected!", flush=True)
                        print("  → Press to MAXIMUM (hold until auto-advance)...")
                        samples.append(list(data))
                        break
    
    # Keep reading until 1 second of no data
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=1000)  # 1 second timeout
        if data:
            samples.append(list(data))
        else:
            # No data for 1 second - they've stopped moving
            break
    
    # Find which byte changed the most
    byte_idx, min_val, max_val = find_analog_byte(samples)
    
    if byte_idx is None or byte_idx in analog_bytes:
        print("  ⚠ Failed to detect channel")
        return None
    
    analog_bytes[byte_idx] = (min_val, max_val, baseline[byte_idx])
    
    config = {
        'type': 'analog',
        'byte': byte_idx,
        'min': min(baseline[byte_idx], min_val, max_val),
        'max': max(baseline[byte_idx], min_val, max_val),
        'neutral': baseline[byte_idx]
    }
    
    print(f"  ✓ Byte {byte_idx}, range [{config['min']}-{config['max']}]")
    print("  ✓ Ready")
    
    # Clear buffer before next step
    clear_buffer(h)
    
    return config

def calibrate_button(h, button_name, instruction, baseline, analog_bytes, used_buttons, index, total):
    """Calibrate a button input - requires 3 consistent presses."""
    print(f"\n[{index}/{total}] {button_name.upper()}")
    print(f"  → {instruction} (press 3 times)")
    
    detections = []
    press_num = 0
    
    while press_num < 3:
        print(f"  Press #{press_num+1}/3: Waiting...", end='', flush=True)
        
        # Wait for button press - no timeout, wait as long as needed
        pressed_data = None
        detected_config = None
        
        while not detected_config:
            data = h.read(MAX_REPORT_LENGTH)
            if data:
                # Check for change in non-analog bytes
                for i in range(len(data)):
                    if i not in analog_bytes and data[i] != baseline[i]:
                        pressed_data = data
                        break
                
                if pressed_data:
                    # Find which bit changed
                    found_duplicate = False
                    for byte_idx in range(len(pressed_data)):
                        if byte_idx in analog_bytes:
                            continue
                        if pressed_data[byte_idx] != baseline[byte_idx]:
                            xor = pressed_data[byte_idx] ^ baseline[byte_idx]
                            for bit_idx in range(8):
                                if xor & (1 << bit_idx):
                                    bit_value = 1 if pressed_data[byte_idx] & (1 << bit_idx) else 0
                                    button_key = (byte_idx, bit_idx)
                                    
                                    # Check if this position is already used
                                    if button_key in used_buttons:
                                        # Mark as duplicate and break (ignore silently)
                                        found_duplicate = True
                                        break
                                    else:
                                        # Valid unused button
                                        detected_config = {
                                            'byte': byte_idx,
                                            'bit': bit_idx,
                                            'value': bit_value
                                        }
                                        break
                            # Break from byte loop if we found something
                            if detected_config or found_duplicate:
                                break
                    
                    # If we found a duplicate, wait a bit and continue looking
                    if found_duplicate:
                        time.sleep(0.3)
        
        print(" ✓", flush=True)
        detections.append(detected_config)
        print(f"  Detected: Byte {detected_config['byte']}, bit {detected_config['bit']}")
        press_num += 1
        
        # Wait for release before next press
        if press_num < 3:
            print(f"  Release and wait...", end='', flush=True)
            time.sleep(0.5)
            print(" ✓")
    
    # Verify all 3 detections match
    if len(detections) == 3:
        first = detections[0]
        if all(d['byte'] == first['byte'] and d['bit'] == first['bit'] for d in detections):
            # Mark this position as used
            button_key = (first['byte'], first['bit'])
            used_buttons[button_key] = button_name
            
            config = {
                'type': 'button',
                'byte': first['byte'],
                'bit': first['bit'],
                'active_value': first['value']
            }
            print(f"  ✓ Confirmed: Byte {first['byte']}, bit {first['bit']}")
            
            # Clear buffer before next step
            clear_buffer(h)
            
            return config
        else:
            print(f"  ⚠ Inconsistent detections:")
            for i, d in enumerate(detections, 1):
                print(f"    Press {i}: Byte {d['byte']}, bit {d['bit']}")
            return None
    else:
        print(f"  ⚠ Failed to collect 3 valid presses")
        return None

def main():
    print("\n" + "="*60)
    print("  LOGITECH G923 WHEEL CALIBRATION")
    print("="*60)
    print("\nThis will calibrate all controls on your wheel.")
    print("Follow the prompts and move/press only the requested input.\n")
    
    try:
        h = open_device()
        print("✓ Device connected\n")
        
        config = {
            'device': {
                'name': 'Logitech G923 Racing Wheel',
                'vendor_id': VENDOR_ID,
                'product_id': PRODUCT_ID,
                'interface': 3
            },
            'controls': {}
        }
        
        # Start with steering to get baseline
        steering_config, baseline, analog_bytes = calibrate_steering(h)
        if steering_config:
            config['controls']['steering'] = steering_config
        else:
            print("\n❌ Failed to calibrate steering")
            return
        
        # Calibrate remaining analog inputs
        print("\n" + "="*60)
        print("PART 2: PEDALS (3)")
        print("="*60)
        
        index = 2
        for input_name, instruction in ANALOG_INPUTS[1:]:  # Skip steering
            result = calibrate_analog(h, input_name, instruction, baseline, analog_bytes, index, 26)
            if result:
                config['controls'][input_name] = result
            index += 1
        
        print(f"\nℹ Analog channels: {sorted(analog_bytes.keys())}")
        
        # Calibrate buttons
        print("\n" + "="*60)
        print("PART 3: BUTTONS (22)")
        print("="*60)
        
        used_buttons = {}  # Track which button positions have been used
        
        for button_name, instruction in BUTTON_INPUTS:
            result = calibrate_button(h, button_name, instruction, baseline, analog_bytes, used_buttons, index, 26)
            if result:
                config['controls'][button_name] = result
            index += 1
        
        # Save configuration
        config_file = 'wheel_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n" + "="*60)
        print("✓ CALIBRATION COMPLETE!")
        print("="*60)
        print(f"\nConfiguration saved to: {config_file}")
        
        analog_count = sum(1 for c in config['controls'].values() if c.get('type') == 'analog')
        button_count = sum(1 for c in config['controls'].values() if c.get('type') == 'button')
        print(f"\nMapped controls:")
        print(f"  • Analog: {analog_count}/{len(ANALOG_INPUTS)}")
        print(f"  • Buttons: {button_count}/{len(BUTTON_INPUTS)}")
        print(f"  • Total: {len(config['controls'])}/26")
        
        h.close()
        
    except IOError as ex:
        print(f"\n❌ Error: {ex}")
    except KeyboardInterrupt:
        print("\n\n⚠ Calibration interrupted by user")
    except Exception as ex:
        print(f"\n❌ Unexpected error: {ex}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
