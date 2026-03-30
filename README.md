# Driver Drowsiness Detection System with Real-Time Dashboard

A computer-vision based system that monitors driver alertness in real-time using a webcam and facial landmark analysis. When drowsiness or sleep is detected, the system triggers audio alerts and pushes notifications to a live web dashboard — enabling remote fleet monitoring.

---

## How It Works

1. **Calibration** — On launch, the driver is guided through a short calibration (eyes open → half-closed → fully closed) to personalise detection thresholds.
2. **Eye Aspect Ratio (EAR)** — The system uses dlib's 68-point facial landmark model to compute the EAR every frame. A moving-average filter smooths out noise.
3. **State Classification** — Based on the smoothed EAR and calibrated thresholds, the driver is classified as **Active**, **Drowsy**, or **Sleeping**.
4. **Alerts** — If drowsiness persists beyond a configurable duration, an audible alarm plays and the event (with GPS location & driver info) is logged and pushed to the dashboard in real-time via WebSockets.

## Features

- Real-time webcam-based drowsiness detection (OpenCV + dlib)
- Personalised per-driver calibration for reliable thresholds
- Audio alarm on prolonged sleep detection
- Live web dashboard (Flask + Socket.IO) with:
  - Alert statistics (sleeping / drowsy counts)
  - Google Maps integration with driver path tracking
  - Real-time push notifications via WebSockets
- GPS location tracking with reverse-geocoded addresses
- Driver credential management via a Tkinter GUI
- Alert history persisted to JSON

## Tech Stack

| Layer | Technologies |
|---|---|
| Detection | Python, OpenCV, dlib, NumPy |
| Backend | Flask, Flask-SocketIO |
| Frontend | Bootstrap 5, Socket.IO, Google Maps JS API |
| Location | Windows Location API (PowerShell), Geopy |

## Project Structure

```
.
├── main.py               # Entry point — launches server & detector together
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
├── config/
│   └── driver.json       # Stored driver configuration
├── data/
│   └── alerts.json       # Persisted alert history
├── scripts/
│   └── get_location.ps1  # PowerShell script for GPS coordinates
├── src/
│   ├── detector.py       # Core drowsiness detection engine
│   ├── server.py         # Flask web dashboard server
│   └── setup_driver.py   # Tkinter GUI for driver credentials
└── templates/
    └── dashboard.html    # Dashboard UI template
```

## Getting Started

### Prerequisites

- Python 3.8+
- Windows OS (for `winsound` audio alerts and location API)
- Webcam
- [shape_predictor_68_face_landmarks.dat](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) — download, extract, and place in the project root directory

### Installation

```bash
pip install -r requirements.txt
```

Create a `.env` file for the Google Maps API key (optional, needed for map on dashboard):
```
GOOGLE_MAPS_API_KEY=your_key_here
```

### Running

**1. Configure driver credentials (optional)**
```bash
python src/setup_driver.py
```

**2. Start both the dashboard and detection together**
```bash
python main.py
```
This launches the Flask dashboard (`src/server.py`) and the detection engine (`src/detector.py`) as parallel processes. Dashboard will be available at `http://localhost:5000`.

Alternatively, run each component separately:
```bash
python src/server.py    # dashboard only
python src/detector.py  # detection only
```
Follow the on-screen calibration prompts, then detection begins automatically. Press `ESC` to stop.

## Configuration

| Parameter | Location | Default |
|---|---|---|
| Sleep alert threshold | `src/detector.py` | 5 seconds |
| Drowsy alert threshold | `src/detector.py` | 7 seconds |
| Location update interval | `src/detector.py` | 5 seconds |
| Camera resolution | `src/detector.py` | 640 × 480 |
| EAR smoothing buffer | `src/detector.py` | 5 frames |

## Future Scope

- Cross-platform audio alerts (replace `winsound`)
- Multi-driver / fleet support
- Cloud deployment with database-backed alert history
- SMS / phone call integration for emergency contacts

## License

MIT
