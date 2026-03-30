from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALERTS_FILE = os.path.join(BASE_DIR, "data", "alerts.json")

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'drowsiness_detection_secret')
socketio = SocketIO(app)

current_driver_status = {
    "status": "Active",
    "location": None,
    "last_update": None
}


def get_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


@app.route('/')
def index():
    return render_template('dashboard.html',
                           alerts=get_alerts(),
                           current_status=current_driver_status)


@app.route('/alert', methods=['POST'])
def receive_alert():
    alert_data = request.json
    if not alert_data:
        return jsonify({"status": "error", "message": "No JSON body provided"}), 400

    required_fields = ["status", "driver", "location"]
    missing = [f for f in required_fields if f not in alert_data]
    if missing:
        return jsonify({"status": "error", "message": f"Missing fields: {', '.join(missing)}"}), 400

    current_driver_status["status"] = alert_data.get("status", "Unknown")
    socketio.emit('new_alert', alert_data)

    return jsonify({"status": "success"})


@app.route('/location_update', methods=['POST'])
def location_update():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON body provided"}), 400

    required_fields = ["latitude", "longitude"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"status": "error", "message": f"Missing fields: {', '.join(missing)}"}), 400

    current_driver_status["location"] = data
    current_driver_status["last_update"] = datetime.datetime.now().isoformat()

    socketio.emit('location_update', {
        "location": data,
        "status": current_driver_status["status"],
        "timestamp": current_driver_status["last_update"]
    })

    return jsonify({"status": "success"})


if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False)
