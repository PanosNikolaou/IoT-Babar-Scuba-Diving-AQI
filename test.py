import requests

# URL of the Flask app
url = "http://127.0.0.1:5000/api/data"

# Example JSON payload
data = {
    "voltage": 1.234,
    "dust": 100.45,
    "pm2_5": 80.36,
    "pm10": 95.42
}

# Send POST request
response = requests.post(url, json=data)

# Print response
print(f"Status Code: {response.status_code}")
print(f"Response JSON: {response.json()}")
