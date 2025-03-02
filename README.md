Scuba Diving Air Quality Monitoring System – IoT Babar

Overview
This project monitors air quality using a combination of MQ gas sensors and a GP2Y1014AU dust sensor to detect potential contamination in diving tanks filled from compressors. By calculating a standard Air Quality Index (AQI) and a specialized Scuba Diving Air Quality Index (SD-AQI), the system identifies harmful gases that could pose risks to divers. IoT Babar, an IoT-based dashboard built using Flask, provides real-time graphing, monitoring, and sensor data analysis.

System Architecture
The project comprises hardware sensors, communication modules, data processing, and a web-based IoT dashboard for visualization.

Hardware Components
Gas Sensors:
- MQ2 (LPG, Smoke, CO detection)
- MQ7 (Carbon Monoxide)
- MQ4 (Methane)
- MQ9 (Carbon Monoxide & Flammable Gases)
- MQ135 (Air Quality, VOCs, CO2, NH3, NOx, Alcohol, Benzene)
- MQ8 (Hydrogen)
Particulate Matter Sensor:
- GP2Y1014AU Dust Sensor for PM2.5 detection.
Environmental Sensor:
- DHT11 for Temperature and Humidity measurement.
Development Boards & Communication:
- Arduino with XBee for wireless sensor data transmission.
- Arduino UNO+WiFi R3 (ATmega328P + ESP8266, 32Mb Memory, USB-TTL CH340G) for handling WiFi communication.

Software & Backend Implementation
- **Flask Web Framework**: Serves as the backend for API endpoints and web-based visualization.
- **SQLite Database with SQLAlchemy**: Stores sensor readings for historical tracking.
- **XBee Data Listener**:
  - Continuously receives sensor data from XBee-enabled devices.
  - Parses and stores received data into the database.
- **Rate Limiting & Security**:
  - Flask-Limiter prevents excessive API requests.
  - Data Validation ensures only correct values are stored.

IoT Dashboard – IoT Babar
A web-based monitoring platform designed for real-time visualization, evaluation, and historical tracking of air quality metrics.
1. **Evaluation Metrics Page**
   - Displays Scuba Diving Air Quality Index (SD-AQI) and Air Quality Index (AQI).
   - SD-AQI assesses diving safety based on gas contamination levels.
   - AQI is computed using PM2.5, PM10, and gas concentrations.
2. **Particulate Matter (PM) Sensors Page**
   - Live Chart displays dust density, PM2.5, and PM10 in real time.
   - Pause/Resume Buttons to control data updates.
   - Data Table logs PM sensor readings with timestamps.
3. **MQ (Gas) Sensors Page**
   - Live Chart tracks temperature, humidity, and gas levels (CO, CO2, NOx, NH3, CH4, alcohol, benzene, H2, etc.).
   - Filter Options to isolate specific sensor data.
   - Data Table provides paginated historical records with timestamps.

SD-AQI Calculation
The SD-AQI is calculated based on the detected gas levels:
- **CO (MQ-2, MQ-7, MQ-9)**
- **CH4 (MQ-4)**
- **H2 (MQ-8)**
- **CO2 (MQ-135)**
- **NOx (MQ-135)**
- **Air Quality Index (Hypothetical MQ-8 Measurement)**
- The formula used:
  ```
  SD-AQI = (CO * 0.05) + (CO_MQ7 * 0.1) + (CO_MQ9 * 0.1) + (CH4 * 0.1) + (H2 * 0.05) + (CO2 * 0.5) + (NOx * 0.1) + (Air * 0.05);
  ```

API Endpoints & Data Management
Data Storage
- **SensorData Model**: Stores particulate matter readings (dust, PM2.5, PM10) with timestamps.
- **MQSensorData Model**: Stores gas sensor values (CO, LPG, NH3, NOx, etc.) along with temperature and humidity.

REST API Endpoints
- **POST /api/data** – Receives sensor data and stores it in the database.
- **GET /api/data** – Retrieves paginated sensor readings.
- **GET /api/evaluation-data** – Fetches latest sensor values for AQI & SD-AQI calculation.
- **GET /api/mq-data** – Provides filtered MQ sensor data for visualization.

Impact & Benefits
👉 **Diver Safety** – Ensures that air used in dive tanks is free from hazardous gases.
👉 **Compressor Quality Control** – Assists dive centers in maintaining clean, breathable air.
👉 **Real-Time & Remote Monitoring** – Enables continuous tracking of air quality levels.
👉 **Scalable & Automated** – Can be expanded to multiple compressor locations for widespread monitoring.

Next Steps & Future Enhancements
- **Cloud Storage Integration** for large-scale historical data analysis.
- **Mobile-Friendly UI** for easier monitoring on smartphones and tablets.
- **Automated Alerts** for unsafe air quality conditions.

