import serial
import requests
import json

# Serial port settings for the XBee
PORT = "/dev/ttyUSB0"  # Replace with your XBee's port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
BAUD_RATE = 9600

# Flask API endpoint
FLASK_API_URL = "http://127.0.0.1:5000/api/data"

# Initialize serial connection
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"Connected to XBee on {PORT} at {BAUD_RATE} baud.")
except Exception as e:
    print(f"Error connecting to XBee: {e}")
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
