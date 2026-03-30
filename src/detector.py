import cv2
import numpy as np
import dlib
from imutils import face_utils
import time
import os
import json
import datetime
from collections import deque
from geopy.geocoders import Nominatim
import threading
import requests
import subprocess

try:
    import winsound
except ImportError:
    winsound = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "driver.json")
ALERTS_FILE = os.path.join(BASE_DIR, "data", "alerts.json")
BEEP_SOUND_PATH = os.path.join(BASE_DIR, "assets", "beep.wav")
SHAPE_PREDICTOR_PATH = os.path.join(BASE_DIR, "assets", "shape_predictor_68_face_landmarks.dat")
LOCATION_SCRIPT_PATH = os.path.join(BASE_DIR, "scripts", "get_location.ps1")

STATE_CHANGE_FRAMES = 3
ear_buffer = deque(maxlen=5)


def load_driver_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading driver config: {e}")
    return {
        "name": "John Doe",
        "id": "DRV12345",
        "vehicle": "TN-01-AB-1234",
        "phone": "+1-555-123-4567"
    }


DRIVER_INFO = load_driver_config()
print(f"Driver : {DRIVER_INFO['name']} ({DRIVER_INFO['id']})")
print(f"Vehicle: {DRIVER_INFO['vehicle']}")
print(f"Contact: {DRIVER_INFO['phone']}")

SLEEP_ALERT_THRESHOLD = DRIVER_INFO.get("sleep_alert_threshold", 5)
DROWSY_ALERT_THRESHOLD = DRIVER_INFO.get("drowsy_alert_threshold", 7)
CAMERA_WIDTH = DRIVER_INFO.get("camera_width", 640)
CAMERA_HEIGHT = DRIVER_INFO.get("camera_height", 480)
LOCATION_UPDATE_INTERVAL = DRIVER_INFO.get("location_update_interval", 5)

alert_start_time = None
drowsy_alert_start_time = None
alert_sent = False
drowsy_alert_sent = False

geolocator = Nominatim(user_agent="driver_drowsiness_detector")
current_location = {"latitude": 0, "longitude": 0, "address": "Unknown"}


def get_windows_location():
    try:
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", LOCATION_SCRIPT_PATH],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        if data.get("error") is None:
            return data["latitude"], data["longitude"]
        print(f"Location error: {data['error']}")
    except Exception as e:
        print(f"Error getting location: {e}")
    return None, None


def update_location():
    lat, lon = get_windows_location()
    if lat is None:
        return
    current_location["latitude"] = lat
    current_location["longitude"] = lon
    try:
        loc = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
        current_location["address"] = loc.address if loc else f"{lat}, {lon}"
    except Exception:
        current_location["address"] = f"{lat}, {lon}"
    print(f"Location updated: {current_location['address']}")
    try:
        requests.post("http://localhost:5000/location_update", json=current_location, timeout=1)
    except Exception:
        pass


def _location_loop():
    while True:
        update_location()
        time.sleep(LOCATION_UPDATE_INTERVAL)


threading.Thread(target=_location_loop, daemon=True).start()


def log_alert(status, duration):
    alert_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "driver": DRIVER_INFO,
        "status": status,
        "duration": duration,
        "location": current_location,
    }
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    try:
        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = []
    alerts.insert(0, alert_data)
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)
    try:
        requests.post("http://localhost:5000/alert", json=alert_data, timeout=1)
    except Exception:
        pass
    print(f"Alert logged: {status} - {current_location['address']}")


def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)


def get_ear(landmarks):
    left = compute(landmarks[37], landmarks[41]) + compute(landmarks[38], landmarks[40])
    right = compute(landmarks[43], landmarks[47]) + compute(landmarks[44], landmarks[46])
    down_left = compute(landmarks[36], landmarks[39])
    down_right = compute(landmarks[42], landmarks[45])
    return (left + right) / (2.0 * (down_left + down_right))


def smooth_ear(value):
    ear_buffer.append(value)
    return sum(ear_buffer) / len(ear_buffer)


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

detector = dlib.get_frontal_face_detector()

if not os.path.exists(SHAPE_PREDICTOR_PATH):
    raise FileNotFoundError(
        f"Shape predictor model not found at '{SHAPE_PREDICTOR_PATH}'. "
        "Download from http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 "
        "and place the .dat file in assets/."
    )
predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)


def calibrate_phase(message, duration=10):
    ear_values = []
    deadline = time.time() + duration

    while time.time() < deadline:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        remaining = int(deadline - time.time())

        cv2.putText(frame, message, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
        cv2.putText(frame, f"Time left: {remaining}s", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for face in detector(gray):
            landmarks = face_utils.shape_to_np(predictor(gray, face))
            ear = get_ear(landmarks)
            ear_values.append(ear)
            cv2.putText(frame, f"EAR: {ear:.2f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        cv2.imshow("Calibration", frame)
        if cv2.waitKey(1) == 27:
            break

    return float(np.mean(ear_values)) if ear_values else 0.2


awake_ear = calibrate_phase("Look straight, eyes open...")
drowsy_ear = calibrate_phase("Half-close your eyes (simulate drowsiness)...")
sleep_ear = calibrate_phase("Close your eyes completely...")

cv2.destroyAllWindows()

sleep = 0
drowsy = 0
active = 0
status = ""
color = (0, 0, 0)
beep_played = False
prev_time = time.time()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        fps = 1 / (now - prev_time)
        prev_time = now

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        height, width = frame.shape[:2]

        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        (tw, th), _ = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        sx = (width - tw) // 2
        cv2.rectangle(frame, (sx - 10, 10), (sx + tw + 10, 60), (0, 0, 0), -1)
        cv2.putText(frame, status, (sx, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

        for face in faces:
            landmarks = face_utils.shape_to_np(predictor(gray, face))
            ear = get_ear(landmarks)
            smoothed_ear = smooth_ear(ear)

            if smoothed_ear >= awake_ear * 0.85:
                sleep = 0
                drowsy = 0
                active = min(active + 1, STATE_CHANGE_FRAMES)
                if active >= STATE_CHANGE_FRAMES:
                    status = "Active :)"
                    color = (0, 255, 0)
                    beep_played = False
                    alert_start_time = drowsy_alert_start_time = None
                    alert_sent = drowsy_alert_sent = False
            elif smoothed_ear > sleep_ear * 1.1:
                sleep = 0
                active = 0
                drowsy = min(drowsy + 1, STATE_CHANGE_FRAMES)
                if drowsy >= STATE_CHANGE_FRAMES:
                    status = "Drowsy !"
                    color = (0, 255, 255)
                    if drowsy_alert_start_time is None:
                        drowsy_alert_start_time = time.time()
                    elif not drowsy_alert_sent and time.time() - drowsy_alert_start_time > DROWSY_ALERT_THRESHOLD:
                        log_alert(status, time.time() - drowsy_alert_start_time)
                        drowsy_alert_sent = True
            else:
                active = 0
                drowsy = 0
                sleep = min(sleep + 1, STATE_CHANGE_FRAMES)
                if sleep >= STATE_CHANGE_FRAMES:
                    status = "SLEEPING !!!"
                    color = (0, 0, 255)
                    if not beep_played:
                        if winsound:
                            winsound.PlaySound(BEEP_SOUND_PATH, winsound.SND_ASYNC)
                        else:
                            print("\a")
                        beep_played = True
                    if alert_start_time is None:
                        alert_start_time = time.time()
                    elif not alert_sent and time.time() - alert_start_time > SLEEP_ALERT_THRESHOLD:
                        log_alert(status, time.time() - alert_start_time)
                        alert_sent = True

            ear_text = f"EAR: {smoothed_ear:.2f} (Raw: {ear:.2f})"
            (ew, _), _ = cv2.getTextSize(ear_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            ex = (width - ew) // 2
            cv2.rectangle(frame, (ex - 5, 70), (ex + ew + 5, 105), (0, 0, 0), -1)
            cv2.putText(frame, ear_text, (ex, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Driver Drowsiness Detector", frame)
        if cv2.waitKey(1) == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Cleanup complete.")
