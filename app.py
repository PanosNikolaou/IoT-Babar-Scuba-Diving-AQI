import json
import time

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from xbreemw import ser

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iot_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# Database model for general sensor data
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dust = db.Column(db.Float, nullable=True)
    pm2_5 = db.Column(db.Float, nullable=True)
    pm10 = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Database model for MQ sensor data
class MQSensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lpg = db.Column(db.Float, nullable=True)
    co = db.Column(db.Float, nullable=True)
    smoke = db.Column(db.Float, nullable=True)
    co_mq7 = db.Column(db.Float, nullable=True)
    ch4 = db.Column(db.Float, nullable=True)
    co_mq9 = db.Column(db.Float, nullable=True)
    co2 = db.Column(db.Float, nullable=True)
    nh3 = db.Column(db.Float, nullable=True)
    nox = db.Column(db.Float, nullable=True)
    alcohol = db.Column(db.Float, nullable=True)
    benzene = db.Column(db.Float, nullable=True)
    h2 = db.Column(db.Float, nullable=True)
    air = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# Create the database tables
with app.app_context():
    db.create_all()

@app.route("/api/data", methods=["POST"])
@limiter.limit("10 per second")  # Limit to 10 requests per second
def receive_data():
    try:
        # Parse incoming JSON data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        # Store general sensor data
        new_sensor_data = SensorData(
            dust=data.get("dust_density", 0.0),
            pm2_5=data.get("pm2_5", 0.0),
            pm10=data.get("pm10", 0.0)
        )
        db.session.add(new_sensor_data)

        # Store MQ sensor data
        new_mq_data = MQSensorData(
            lpg=data.get("LPG"),
            co=data.get("CO"),
            smoke=data.get("Smoke"),
            co_mq7=data.get("CO_MQ7"),
            ch4=data.get("CH4"),
            co_mq9=data.get("CO_MQ9"),
            co2=data.get("CO2"),
            nh3=data.get("NH3"),
            nox=data.get("NOx"),
            alcohol=data.get("Alcohol"),
            benzene=data.get("Benzene"),
            h2=data.get("H2"),
            air=data.get("Air"),
            temperature = data.get("Temperature"),
            humidity = data.get("Humidity")
        )
        db.session.add(new_mq_data)

        db.session.commit()

        return jsonify({"status": "success", "message": "Data saved"}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/data", methods=["GET"])
def get_data():
    try:
        # Pagination parameters
        page = request.args.get("page", 1, type=int)  # Default to page 1
        per_page = request.args.get("per_page", 50, type=int)  # Default to 50 records per page

        # Fetch paginated data for general sensor data
        pagination = SensorData.query.order_by(SensorData.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
        general_records = pagination.items  # Get the items for the current page

        # Fetch paginated data for MQ sensor data
        mq_pagination = MQSensorData.query.order_by(MQSensorData.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
        mq_records = mq_pagination.items

        # Format data for JSON response, skipping records where all values are 0
        general_data = [{
            "timestamp": r.timestamp.isoformat(),
            "dust": r.dust if r.dust is not None else 0,
            "pm2_5": r.pm2_5 if r.pm2_5 is not None else 0,
            "pm10": r.pm10 if r.pm10 is not None else 0
        } for r in general_records if not (r.dust == 0 and r.pm2_5 == 0 and r.pm10 == 0)]

        mq_data = [{
            "timestamp": r.timestamp.isoformat(),
            "LPG": r.lpg if r.lpg is not None else 0,
            "CO": r.co if r.co is not None else 0,
            "Smoke": r.smoke if r.smoke is not None else 0,
            "CO_MQ7": r.co_mq7 if r.co_mq7 is not None else 0,
            "CH4": r.ch4 if r.ch4 is not None else 0,
            "CO_MQ9": r.co_mq9 if r.co_mq9 is not None else 0,
            "CO2": r.co2 if r.co2 is not None else 0,
            "NH3": r.nh3 if r.nh3 is not None else 0,
            "NOx": r.nox if r.nox is not None else 0,
            "Alcohol": r.alcohol if r.alcohol is not None else 0,
            "Benzene": r.benzene if r.benzene is not None else 0,
            "H2": r.h2 if r.h2 is not None else 0,
            "Air": r.air if r.air is not None else 0,
            "temperature": r.temperature if r.temperature is not None else 0,
            "humidity": r.humidity if r.humidity is not None else 0
        } for r in mq_records]

        return jsonify({
            "general_data": general_data,
            "mq_data": mq_data,
            "general_total": len(general_data),       # Total valid records for general sensor data
            "mq_total": mq_pagination.total,         # Total records for MQ sensor data
            "page": pagination.page,                 # Current page
            "per_page": pagination.per_page,         # Records per page
            "pages": pagination.pages                # Total pages
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mq-data")
def mq_data():

    return render_template("mq_data.html")

@app.route("/api/mq-data", methods=["GET"])
def get_mq_data():
    try:
        # Filter out records where fields are None
        mq_records = MQSensorData.query.filter(
            MQSensorData.lpg.isnot(None),
            MQSensorData.co.isnot(None),
            MQSensorData.smoke.isnot(None),
            MQSensorData.co_mq7.isnot(None),
            MQSensorData.ch4.isnot(None),
            MQSensorData.co_mq9.isnot(None),
            MQSensorData.co2.isnot(None),
            MQSensorData.nh3.isnot(None),
            MQSensorData.nox.isnot(None),
            MQSensorData.alcohol.isnot(None),
            MQSensorData.benzene.isnot(None),
            MQSensorData.h2.isnot(None),
            MQSensorData.air.isnot(None),
            MQSensorData.temperature.isnot(None),
            MQSensorData.humidity.isnot(None)
        ).order_by(MQSensorData.timestamp.desc()).all()

        # Format data for the response
        mq_data = [{
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "humidity": r.humidity,
            "LPG": r.lpg,
            "CO": r.co,
            "Smoke": r.smoke,
            "CO_MQ7": r.co_mq7,
            "CH4": r.ch4,
            "CO_MQ9": r.co_mq9,
            "CO2": r.co2,
            "NH3": r.nh3,
            "NOx": r.nox,
            "Alcohol": r.alcohol,
            "Benzene": r.benzene,
            "H2": r.h2,
            "Air": r.air
        } for r in mq_records]

        return jsonify({"mq_data": mq_data}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/evaluation")
def evaluation():
    return render_template("evaluation.html")

@app.route("/api/evaluation-data", methods=["GET"])
def evaluation_data():
    try:
        # Fetch the latest sensor data
        latest_pm_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        latest_mq_data = MQSensorData.query.order_by(MQSensorData.timestamp.desc()).first()

        # Combine data for evaluation
        evaluation_data = {
            "temperature": latest_mq_data.temperature if latest_mq_data else None,
            "humidity": latest_mq_data.humidity if latest_mq_data else None,
            "pm2_5": latest_pm_data.pm2_5 if latest_pm_data else None,
            "pm10": latest_pm_data.pm10 if latest_pm_data else None,
            "lpg": latest_mq_data.lpg if latest_mq_data else None,
            "co": latest_mq_data.co if latest_mq_data else None,
        }

        return jsonify(evaluation_data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# XBee Listener Function
def xbee_listener():
    """Continuously listen for data from XBee and send it to the Flask API."""
    while True:
        try:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()  # Read and decode the data
                parsed_data = parse_xbee_data(raw_data)
                if parsed_data:
                    send_to_flask(parsed_data)
        except Exception as e:
            print(f"Error reading from XBee: {e}")
        time.sleep(0.1)

def parse_xbee_data(raw_data):
    """Parse data received from XBee."""
    try:
        # Assuming the XBee sends data in JSON format
        data = json.loads(raw_data)
        print("Received data from XBee:", data)
        return data
    except json.JSONDecodeError:
        print("Invalid data format. Skipping:", raw_data)
        return None

def send_to_flask(data):
    """Simulate an internal POST request by directly inserting into the database."""
    try:
        new_data = SensorData(
            dust=data.get("dust_density", 0.0),
            pm2_5=data.get("pm2_5", 0.0),
            pm10=data.get("pm10", 0.0)
        )
        with app.app_context():
            db.session.add(new_data)
            db.session.commit()
        print("Data successfully saved to the database:", data)
    except Exception as e:
        print(f"Error saving XBee data to database: {e}")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
