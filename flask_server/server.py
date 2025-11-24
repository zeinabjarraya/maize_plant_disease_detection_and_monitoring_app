from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db
import random
import threading
import time
from datetime import datetime

app = Flask(__name__)

# 🔑 Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://agridoc-25932-default-rtdb.europe-west1.firebasedatabase.app"
})

# References
sensor_ref = db.reference("environmental_data/all_sensors")
user_id = "9DX5VF9VEKedGnrxYnGBDtfWOLx1"
pump_ref = db.reference(f"pump_control/{user_id}")

# -----------------------------
# Sensor data simulation
# -----------------------------
def generate_sensor_data():
    return {
        "temperature": round(random.uniform(18, 30), 2),
        "humidity": random.randint(40, 85),
        "soil_moisture": random.randint(20, 60),
        "co2": random.randint(350, 1000),
        "timestamp": datetime.utcnow().isoformat()
    }

def send_data_loop(interval=5):
    while True:
        data = generate_sensor_data()
        timestamp = int(time.time())
        sensor_ref.child(str(timestamp)).set(data)
        print(f"📤 Sent sensor data: {data} at {timestamp}")
        time.sleep(interval)

# -----------------------------
# Pump state monitoring for both pumps
# -----------------------------
def check_pump_state_loop(interval=2):
    last_state = {"water": None, "fertilizer": None}
    while True:
        snapshot = pump_ref.get() or {}
        water_state = snapshot.get("water")
        fertilizer_state = snapshot.get("fertilizer")

        if water_state != last_state["water"]:
            print(f"🚰 Water Pump state changed: {water_state}")
            last_state["water"] = water_state

        if fertilizer_state != last_state["fertilizer"]:
            print(f"🌱 Fertilizer Pump state changed: {fertilizer_state}")
            last_state["fertilizer"] = fertilizer_state

        time.sleep(interval)

# -----------------------------
# Flask routes
# -----------------------------
@app.route("/simulate")
def simulate():
    data = generate_sensor_data()
    timestamp = int(time.time())
    sensor_ref.child(str(timestamp)).set(data)
    return jsonify({"status": "success", "sent_data": data, "stored_at": timestamp})

@app.route("/pump_state")
def pump_state():
    snapshot = pump_ref.get() or {}
    return jsonify({
        "water": snapshot.get("water"),
        "fertilizer": snapshot.get("fertilizer")
    })

# -----------------------------
# Start threads for continuous loops
# -----------------------------
sensor_thread = threading.Thread(target=send_data_loop, args=(5,), daemon=True)
sensor_thread.start()

pump_thread = threading.Thread(target=check_pump_state_loop, daemon=True)
pump_thread.start()

# -----------------------------
# Run Flask app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
