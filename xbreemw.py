import serial
import serial.tools.list_ports
import requests
import json
import time

# List of possible serial ports
BAUD_RATE = 9600
FLASK_API_URL = "http://127.0.0.1:5000/api/data"


def find_xbee_port():
    """Finds the FT231X USB UART device, which is likely an XBee."""
    available_ports = list(serial.tools.list_ports.comports())

    for port in available_ports:
        print(f"Checking port: {port.device} ({port.description})")

        if "FT231X USB UART" in port.description:
            print(f"Possible XBee detected on {port.device}")
            return port.device

    print("No XBee module detected.")
    return None


def verify_xbee(port):
    """Verifies if the device on the given port is an XBee by sending an '+++' command."""
    try:
        with serial.Serial(port, BAUD_RATE, timeout=2) as ser:
            ser.write(b'+++')  # Enter command mode
            time.sleep(1)  # Wait for response
            response = ser.read(10).decode('utf-8').strip()

            if "OK" in response:
                print(f"XBee module confirmed on {port}!")
                return True
            else:
                print(f"No response from {port}. Might not be an XBee.")
                return False
    except Exception as e:
        print(f"Error verifying XBee on {port}: {e}")
        return False


# Find a valid XBee port
PORT = find_xbee_port()

if PORT and verify_xbee(PORT):
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print(f"Connected to XBee on {PORT} at {BAUD_RATE} baud.")
    except Exception as e:
        print(f"Error connecting to XBee: {e}")
        exit(1)
else:
    print("No valid XBee module found. Exiting...")
    exit(1)


def send_to_flask(data):
    try:
        response = requests.post(FLASK_API_URL, json=data)
        if response.status_code == 200:
            print("Data successfully sent to Flask:", data)
        else:
            print(f"Error sending data to Flask: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error communicating with Flask: {e}")


def parse_xbee_data(raw_data):
    try:
        # Assuming the XBee sends data in JSON format
        data = json.loads(raw_data)
        print("Received data from XBee:", data)
        return data
    except json.JSONDecodeError:
        print("Invalid data format. Skipping:", raw_data)
        return None


def main():
    while True:
        try:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()  # Read and decode the data
                parsed_data = parse_xbee_data(raw_data)
                if parsed_data:
                    send_to_flask(parsed_data)
        except Exception as e:
            print(f"Error reading from XBee: {e}")


if __name__ == "__main__":
    main()
