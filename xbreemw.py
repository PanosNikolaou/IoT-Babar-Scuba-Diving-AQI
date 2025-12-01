import serial
import serial.tools.list_ports
import requests
import json
import time
import os
import logging
from datetime import datetime

# List of possible serial ports
BAUD_RATE = 9600
FLASK_API_URL = "http://127.0.0.1:5000/api/data"

# module logger: quiet by default, enable verbose by setting XBEE_VERBOSE or XBEE_DEBUG
logger = logging.getLogger(__name__)
if os.getenv("XBEE_VERBOSE") or os.getenv("XBEE_DEBUG"):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


def find_xbee_port():
    """Finds the FT231X USB UART device, which is likely an XBee."""
    available_ports = list(serial.tools.list_ports.comports())

    for port in available_ports:
        logger.debug("Checking port: %s (%s)", port.device, port.description)

        if "FT231X USB UART" in port.description:
            logger.info("Possible XBee detected on %s", port.device)
            return port.device

    logger.debug("No XBee module detected.")
    return None


def verify_xbee(port):
    """Verifies if the device on the given port is an XBee by sending an '+++' command."""
    try:
        with serial.Serial(port, BAUD_RATE, timeout=2) as ser:
            ser.write(b'+++')  # Enter command mode
            time.sleep(1)  # Wait for response
            response = ser.read(10).decode('utf-8').strip()

            if "OK" in response:
                logger.info("XBee module confirmed on %s!", port)
                return True
            else:
                logger.debug("No response from %s. Might not be an XBee.", port)
                return False
    except Exception as e:
        logger.warning("Error verifying XBee on %s: %s", port, e)
        return False


# Serial object and internal port tracker
ser = None
_port = None
_buffer = ""  # accumulate incoming serial data

def connect_xbee(retries=3, delay=2):
    """Attempt to find, verify and connect to an XBee device.

    Returns True if connected, False otherwise. Does not exit the process on failure.
    """
    global ser, _port
    for attempt in range(1, retries + 1):
        PORT = find_xbee_port()
        if PORT and verify_xbee(PORT):
            try:
                ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
                _port = PORT
                logger.info("Connected to XBee on %s at %d baud.", PORT, BAUD_RATE)
                return True
            except Exception as e:
                logger.warning("Error connecting to XBee: %s", e)
        else:
            logger.debug("XBee not found or verification failed.")

        if attempt < retries:
            time.sleep(delay)

    logger.debug("Could not connect to XBee after retries. Continuing without serial connection.")
    ser = None
    return False

# Do not attempt an automatic connection at import time; let the caller
# control when to start the listener/connect. Some environments import
# this module without intending to immediately open serial ports.
# connect_xbee(retries=1, delay=1)


def send_to_flask(data):
    try:
        response = requests.post(FLASK_API_URL, json=data)
        if response.status_code == 200:
            logger.debug("Data successfully sent to Flask: %s", data)
        else:
            logger.warning("Error sending data to Flask: %s %s", response.status_code, response.text)
    except Exception as e:
        logger.warning("Error communicating with Flask: %s", e)


def parse_xbee_data(raw_data):
    try:
        # Assuming the XBee sends data in JSON format
        data = json.loads(raw_data)
        logger.debug("Received raw data from XBee: %s", data)

        # Normalize keys to the format expected by the Flask app (/api/data)
        # Accept either lowercase or mixed-case incoming keys
        key_map = {
            'lpg': 'LPG', 'co': 'CO', 'smoke': 'Smoke', 'co_mq7': 'CO_MQ7', 'ch4': 'CH4', 'co_mq9': 'CO_MQ9',
            'co2': 'CO2', 'nh3': 'NH3', 'nox': 'NOx', 'alcohol': 'Alcohol', 'benzene': 'Benzene',
            'h2': 'H2', 'air': 'Air', 'temperature': 'Temperature', 'humidity': 'Humidity',
            'sd_aqi': 'SD_AQI', 'sd_aqi_level': 'SD_AQI_level', 'timestamp_ms': 'timestamp_ms'
        }

        normalized = {}
        for k, v in data.items():
            if not isinstance(k, str):
                continue
            lk = k.lower()
            if lk in key_map:
                normalized[key_map[lk]] = v
            else:
                # Preserve unknown keys as-is
                normalized[k] = v

        # Coerce numeric fields to numbers where possible
        numeric_keys = ['LPG','CO','Smoke','CO_MQ7','CH4','CO_MQ9','CO2','NH3','NOx','Alcohol','Benzene','H2','Air','Temperature','Humidity','SD_AQI']
        for nk in numeric_keys:
            if nk in normalized:
                try:
                    # ensure floats for numeric fields
                    normalized[nk] = float(normalized[nk])
                except Exception:
                    # leave as-is if coercion fails
                    pass

        # If device provided a timestamp_ms, attach a server-side ISO timestamp for ordering
        if 'timestamp_ms' in normalized:
            try:
                # Use server receive time as authoritative timestamp (can't derive absolute time from millis)
                normalized['timestamp'] = datetime.utcnow().isoformat()
            except Exception:
                pass

        logger.debug("Normalized data to send to Flask: %s", normalized)
        return normalized
    except json.JSONDecodeError:
        logger.debug("Invalid data format. Skipping: %s", raw_data)
        return None


def _extract_json_from_buffer(buf):
    """Extract the first complete JSON object from buf if present.
    Returns (json_str, remaining_buf) where json_str is None if no complete
    JSON object was found.
    """
    # find first opening brace
    start = buf.find('{')
    if start == -1:
        # no JSON start yet, discard any leading garbage
        return None, buf

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(buf)):
        ch = buf[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            # otherwise remain in string
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    # found a complete JSON object from start..i
                    return buf[start:i+1], buf[i+1:]
    # no complete object yet
    return None, buf


def main():
    # modify module-level `ser` and `_buffer`
    global ser, _buffer

    while True:
        try:
            if ser is None:
                # Try to reconnect if serial is not available
                connect_xbee(retries=1, delay=1)
                time.sleep(1)
                continue

            if ser.in_waiting > 0:
                # read all available bytes and append to buffer
                try:
                    chunk = ser.read(ser.in_waiting)
                    chunk = chunk.decode('utf-8', errors='replace')
                except Exception as e:
                    logger.warning("Error reading serial chunk: %s", e)
                    chunk = ''
                _buffer += chunk

                # Try extracting any complete JSON objects from the buffer
                while True:
                    json_str, _buffer = _extract_json_from_buffer(_buffer)
                    if json_str is None:
                        break
                    json_str = json_str.strip()
                    parsed_data = parse_xbee_data(json_str)
                    if parsed_data:
                        send_to_flask(parsed_data)
            else:
                # avoid busy spin
                time.sleep(0.05)
        except Exception as e:
            logger.warning("Error reading from XBee: %s", e)


if __name__ == "__main__":
    main()
