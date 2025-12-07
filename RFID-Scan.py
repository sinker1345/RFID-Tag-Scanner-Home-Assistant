import requests
import evdev
import os
from evdev import InputDevice, categorize, ecodes

# ------------------------------
# CONFIGURATION
# ------------------------------

HOME_ASSISTANT_URL = "http://HOMEASSISTANTIP:8123/api/events/tag_scanned"
LONG_LIVED_TOKEN = "PUT AUTH TOKEN HERE"

# Match part of your reader name in /dev/input/by-id/
# Example names you will typically see:
#   usb-13ba_Barcode_Reader-event-kbd
#   usb-XXXX_RFID_Reader-event-kbd
READER_NAME_MATCH = "RFID"     # <-- CHANGE THIS to match your reader name


# ------------------------------
# FUNCTIONS
# ------------------------------

def find_reader():
    """
    Find the RFID reader in /dev/input/by-id based on name fragment.
    Returns the device path to open.
    """
    base_path = "/dev/input/by-id"
    for entry in os.listdir(base_path):
        entry_lower = entry.lower()
        if READER_NAME_MATCH.lower() in entry_lower and "event" in entry_lower:
            full_path = os.path.join(base_path, entry)
            print(f"Using RFID device: {full_path}")
            return full_path

    raise Exception(
        f"No RFID reader found in /dev/input/by-id matching '{READER_NAME_MATCH}'. "
        f"Run: ls -l /dev/input/by-id to check available names."
    )


def send_to_homeassistant(tag_id: str):
    headers = {
        "Authorization": f"Bearer {LONG_LIVED_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "tag_id": tag_id,
        "device_id": "rfid_reader_py"
    }

    try:
        requests.post(HOME_ASSISTANT_URL, json=payload, headers=headers)
        print(f"Sent tag: {tag_id}")
    except Exception as e:
        print(f"Error: {e}")


def read_rfid():
    device_path = find_reader()
    dev = InputDevice(device_path)
    buffer = ""

    print("RFID reader active (via /dev/input/by-id).")

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)

            if key.keystate == key.key_down:
                # Enter = send tag
                if key.keycode == "KEY_ENTER":
                    if buffer:
                        send_to_homeassistant(buffer)
                        buffer = ""
                else:
                    # Convert KEY_2 to "2", etc.
                    code = key.keycode.replace("KEY_", "")
                    if len(code) == 1:  # Only accept normal characters
                        buffer += code


if __name__ == "__main__":
    read_rfid()
