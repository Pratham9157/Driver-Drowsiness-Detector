# Drowsiness Detection System - Complete Startup Guide

## 🎯 Overview

This is a **real-time drowsiness detection system** with:
- 🎥 **Detector Service** - Video processing & ML detection (or test mode simulation)
- 🔌 **API Service** - Alert storage in MongoDB
- 📊 **React Dashboard** - Real-time alerts with audio notifications

---

## ⚙️ Prerequisites

✅ Python 3.14+ installed
✅ Node.js 18+ installed
✅ MongoDB Atlas account (cloud) or local MongoDB
✅ `.env` file configured with MongoDB URI

---

## 🚀 Startup - 3 Terminal Setup

### **Terminal 1: API Service (Port 8000)**

```bash
cd c:\Users\Pratham\Desktop\My_learning\CourseImplementations\OpenEndedProject\enhanced_project
python -m uvicorn api_service.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify:** Open browser → http://localhost:8000/docs

---

### **Terminal 2: Detector Service**

**Option A: TEST MODE (Simulates Drowsiness)**
```bash
cd c:\Users\Pratham\Desktop\My_learning\CourseImplementations\OpenEndedProject\enhanced_project
$env:PYTHONPATH = '.'; python -m detector_service.main --test
```

**TEST MODE BEHAVIOR:**
- ✅ No camera needed
- ✅ Cycles through states: ACTIVE → DROWSY → ASLEEP
- ✅ Sends real alerts to API every ~4 seconds
- ✅ Perfect for **testing without a webcam**

**Expected Output:**
```
🧪 TEST MODE ENABLED - Simulating drowsiness detection
...
✅ Alert sent to API: drowsy (score=0.65)
```

---

**Option B: REAL MODE (Real Webcam Detection)**
```bash
cd c:\Users\Pratham\Desktop\My_learning\CourseImplementations\OpenEndedProject\enhanced_project
$env:PYTHONPATH = '.'; python -m detector_service.main
```

**REAL MODE BEHAVIOR:**
- 📷 Uses your webcam for face detection
- 🧠 Uses MediaPipe for landmark detection
- 📊 Calculates real drowsiness metrics
- ⚠️ Only sends alerts when actual drowsiness detected
- ⚠️ Requires good lighting and clear view of face

**Expected Output:**
```
✅ Camera initialized: 640x480 @ 30 FPS
...
[Live camera window appears]
```

---

### **Terminal 3: React Dashboard (Port 3000)**

```bash
cd c:\Users\Pratham\Desktop\My_learning\CourseImplementations\OpenEndedProject\enhanced_project\admin_dashboard
npm run dev
```

**Expected Output:**
```
VITE v5.4.21 ready in 331 ms
➜  Local: http://localhost:3000/
```

**Open:** http://localhost:3000

---

## ✅ What To Expect

### **Test Mode Timeline**
When running detector with `--test`, every 4 seconds you'll see:

1. **0-2 sec:** ACTIVE state (green) ✅
   - Drowsiness: 30%
   - Dashboard shows green status

2. **3 sec:** DROWSY alert (orange) ⚠️
   - Drowsiness: 65%
   - **🔊 Beep sound** from speaker
   - Alert appears in Alerts List (orange)
   - Map anchors to vehicle location

3. **3.5 sec:** ASLEEP alert (red) 🚨
   - Drowsiness: 85%
   - **🔊 Double beep** (urgent tone)
   - Alert appears in Alerts List (red)

4. **4 sec:** Cycle repeats

---

## 📊 MongoDB Compass

Verify alerts are being saved:

1. Open **MongoDB Compass**
2. Connect to your MongoDB instance
3. Navigate to: `drowsiness_detector.drowsiness_alerts`
4. You should see alert documents appearing in real-time

**Example Document:**
```json
{
  "_id": ObjectId("..."),
  "alert_id": "alert_a1b2c3d4",
  "vehicle_id": "vehicle_001",
  "driver_id": "driver_001",
  "state": "drowsy",
  "severity": "warning",
  "drowsiness_score": 0.65,
  "timestamp": "2026-04-12T17:36:13.779Z"
}
```

---

## 🔧 Troubleshooting

### **NO Alerts on Dashboard**
1. ✅ Check all 3 terminals are running
2. ✅ Check API health: `curl http://localhost:8000/health`
3. ✅ Check detector sends alerts: Look for "✅ Alert sent to API" in detector terminal
4. ✅ Refresh browser (Ctrl+F5)

### **NO Sounds Playing**
1. ✅ Check speaker volume (unmute)
2. ✅ Check browser permissions for audio
3. ✅ Try creating test alert manually:
   ```bash
   curl -X POST "http://localhost:8000/api/alerts" \
     -H "Content-Type: application/json" \
     -d '{"vehicle_id":"test","driver_id":"d1","state":"drowsy","ear_value":0.22,"head_pitch":15,"head_yaw":5,"head_roll":-2,"fatigue_score":0.3,"drowsiness_score":0.65,"timestamp":"2026-04-12T17:36:13Z"}'
   ```

### **Detector Says ASLEEP When I'm Awake**
- **If using `--test` mode:** This is normal! Test mode cycles through all states (ACTIVE → DROWSY → ASLEEP → repeat). It's simulating drowsiness patterns.
- **If using real mode:** Face detection may be having issues. Try:
  - Better lighting
  - Clear view of face
  - Move closer to camera
  - Restart detector

### **Detector Not Starting**
- Check PYTHONPATH is set: `$env:PYTHONPATH = '.'`
- Check working directory is correct: `cd /path/to/enhanced_project`
- Check aiohttp installed: `pip install aiohttp>=3.9.0`

### **Cannot Connect to MongoDB**
- Check `.env` file has `MONGO_URI` set
- Check MongoDB Atlas is accessible
- Check internet connection
- Verify credentials in MONGO_URI

---

## 📈 System Data Flow

```
┌─────────────────────────┐
│   Detector Service      │
│  (Test or Real Mode)    │
│                         │
│  Detects Drowsiness     │
│  ↓                      │
│  Sends Alert via HTTP   │
└──────────────┬──────────┘
               │ POST /api/alerts
               ↓
┌──────────────────────────────┐
│    API Service (Port 8000)   │
│                              │
│  Receives Alert              │
│  ↓                           │
│  Saves to MongoDB            │
└──────────────┬───────────────┘
               │ Collection: drowsiness_alerts
               ↓
┌──────────────────────────────┐
│   React Dashboard (Port 3000)│
│                              │
│  Polls GET /api/alerts       │
│  every 2 seconds             │
│  ↓                           │
│  Displays Alert              │
│  Plays Beep Sound 🔊         │
│  Centers Map on Vehicle      │
│  Updates KPI Metrics         │
└──────────────────────────────┘
```

---

## 🎮 Control Keys

### **In Detector Window**
- **Q** - Quit detector gracefully
- (Window shows real-time metrics and video)

### **In Dashboard**
- **Click vehicle on map** - Select vehicle for trends
- **Settings icon** - Calibration modal (optional)
- **Auto-refresh** - Fetches alerts every 2 seconds
- **Beep mute** - Browser settings → Audio (if needed)

---

## 🔍 API Endpoints Reference

### **Create Alert (Detector sends to here)**
```
POST /api/alerts

Content-Type: application/json

{
  "vehicle_id": "vehicle_001",
  "driver_id": "driver_001",
  "state": "drowsy",
  "ear_value": 0.22,
  "head_pitch": 15,
  "head_yaw": 5,
  "head_roll": -2,
  "fatigue_score": 0.3,
  "drowsiness_score": 0.65,
  "timestamp": "2026-04-12T17:36:13Z"
}
```

### **Get Alerts (Dashboard fetches from here)**
```
GET /api/alerts?limit=50

Response:
{
  "status": "success",
  "data": [
    {
      "alert_id": "alert_xxx",
      "vehicle_id": "vehicle_001",
      "state": "drowsy",
      "drowsiness_score": 0.65,
      "detected_at": "2026-04-12T17:36:13Z",
      ...
    }
  ],
  "count": 1
}
```

### **Health Check**
```
GET /health

Response:
{
  "status": "healthy",
  "api": "running",
  "database": "healthy"
}
```

---

## 📋 Checklist

- [ ] API running on port 8000 (curl http://localhost:8000/health returns 200)
- [ ] Detector running with `--test` mode
- [ ] Dashboard running on port 3000
- [ ] Can access http://localhost:3000 in browser
- [ ] MongoDB Compass shows alerts being saved
- [ ] Beep sounds playing from speaker
- [ ] Alerts visible on dashboard within 2 seconds
- [ ] Map centers on vehicle location

---

## 🎓 Understanding Drowsiness Scores

| Score | State | Color | Action |
|-------|-------|-------|--------|
| 0.0-0.4 | ACTIVE | 🟢 Green | Normal driving |
| 0.4-0.7 | DROWSY | 🟠 Orange | Send alert, suggest break |
| 0.7-1.0 | ASLEEP | 🔴 Red | Critical alert, immediate action |

Scores are calculated from:
- **EAR (Eye Aspect Ratio)** - Eye openness
- **Head Pose** - Head angle & droop
- **Fatigue** - Complex facial patterns

---

## 🚀 Next Steps

1. **Run all 3 services together** - You'll see real-time alerts!
2. **Test with real webcam** - Remove `--test` flag
3. **Calibrate for your face** - Settings modal on dashboard
4. **Add to vehicle** - Deploy detector on car hardware

---

## 📞 Debugging Notes

If things don't work:

1. **Check Terminal 2 (Detector)** - Look for error messages
   - Connection errors? Check API on port 8000
   - Module errors? Check PYTHONPATH
   - Alert sending? Look for "✅ Alert sent" message

2. **Check MongoDB** - Empty? Detector isn't sending
   - Manually send test alert with curl
   - Check API receiving it

3. **Check Dashboard** - Blank? Not fetching alerts
   - Browser console (F12) for errors
   - Check if API responding to GET /api/alerts

4. **Check Network** - Ports busy?
   ```bash
   # Kill processes on ports if needed
   Get-Process node | Stop-Process -Force    # Port 3000
   Get-Process python | Stop-Process -Force  # Port 8000
   ```

---

## ✨ System Status

When everything is working:

```
✅ API:      Running on port 8000
✅ Detector: Sending alerts via HTTP
✅ MongoDB:  Storing alerts
✅ Dashboard: Displaying alerts + Audio
```

**You now have a working drowsiness detection system!** 🎉
