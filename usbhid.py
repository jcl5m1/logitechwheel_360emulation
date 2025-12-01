import hid
import time

# --- Part 1: Enumerate Devices to Find VID/PID ---
print("--- 1. Enumerating HID Devices ---")
devices = hid.enumerate()
if not devices:
    print("No HID devices found.")

# Print details of all found devices
for dev_dict in devices:
    print(f"Device Path: {dev_dict['path']}")
    print(f"  Vendor ID: 0x{dev_dict['vendor_id']:04x}")
    print(f"  Product ID: 0x{dev_dict['product_id']:04x}")
    print(f"  Manufacturer: {dev_dict['manufacturer_string']}")
    print(f"  Product String: {dev_dict['product_string']}")
    print("-" * 20)

# --- Part 2: Reading Data from a Specific Device ---

# Logitech G923 Racing Wheel
VENDOR_ID = 0x046d
PRODUCT_ID = 0xc266

# Set the maximum report length (buffer size) for the read operation.
MAX_REPORT_LENGTH = 64
READ_TIMEOUT_MS = 100  # Shorter timeout for faster response

try:
    print(f"\n--- 2. Attempting to find and read from device: VID=0x{VENDOR_ID:04x}, PID=0x{PRODUCT_ID:04x} ---")
    
    # Find all matching devices
    matching = [d for d in devices if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID]
    if not matching:
        raise IOError(f"No device found with VID=0x{VENDOR_ID:04x} PID=0x{PRODUCT_ID:04x}")

    print(f"Found {len(matching)} interface(s) for this device.")
    
    # Use interface 4 (index 3) which is MI_00 - the one that works
    if len(matching) < 4:
        raise IOError(f"Expected at least 4 interfaces, but found only {len(matching)}")
    
    chosen = matching[3]  # Interface 4 (0-indexed)
    print(f"\n--- Using interface 4 (MI_00) ---")
    print(f"Device path: {chosen['path']}")
    
    h = hid.device()
    h.open_path(chosen['path'])
    print(f"Successfully opened: {h.get_product_string()} ({h.get_manufacturer_string()})")
    h.set_nonblocking(0)
    
    # Continuously read and print data
    print("\nReading data continuously (Press Ctrl+C to exit)...")
    print("Move the steering wheel or press buttons to generate data.\n")
    
    message_count = 0
    
    while True:
        data = h.read(MAX_REPORT_LENGTH, timeout_ms=READ_TIMEOUT_MS)
        
        if data:
            message_count += 1
            ts = time.strftime('%H:%M:%S')
            data_list = list(data)
            
            print(f"[{message_count}] {ts} | {data_list}")

except IOError as ex:
    print(f"\nError: {ex}")
    print("Could not open the device. Common reasons: incorrect VID/PID, device not plugged in, or insufficient permissions.")
except KeyboardInterrupt:
    print("\nRead process interrupted by user.")
except Exception as ex:
    print(f"\nUnexpected error: {ex}")
finally:
    if 'h' in locals() and h:
        try:
            h.close()
        except:
            pass

print("\nProgram finished.")
