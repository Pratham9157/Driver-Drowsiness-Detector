# Phase 6: React Admin Dashboard - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd admin_dashboard
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The dashboard will open at `http://localhost:3000`

### 3. Build for Production
```bash
npm run build
npm run preview
```

---

## Dashboard Features

### 🗺️ Fleet Map
- Real-time vehicle locations
- Color-coded status indicators:
  - 🟢 Green: Active (awake)
  - 🟠 Orange: Drowsy
  - 🔴 Red: Asleep
- Click markers to select vehicles
- Zoom and pan controls

### 📊 KPI Dashboard
- Total alerts today
- Drowsy alert count
- Asleep alert count
- Active detector count
- Auto-refresh every 5 seconds

### 🚨 Alerts List
- Recent drowsiness alerts
- Sorted by recency
- Shows EAR value, fatigue score, location
- Click to select vehicle and view trends

### 📈 Trend Charts
- Drowsiness score over time
- Eye Aspect Ratio (EAR) values
- Visual representation of driver state changes
- Time-series analysis

### ⚙️ Calibration Settings
- Per-driver threshold adjustment
- EAR thresholds (awake/drowsy)
- Head pose angle limits
- Alert hysteresis frames
- One-click calibration modal

---

## Architecture

```
admin_dashboard/
├── src/
│   ├── components/        # React components
│   │   ├── FleetMap.tsx
│   │   ├── AlertsList.tsx
│   │   ├── TrendChart.tsx
│   │   ├── KPIDashboard.tsx
│   │   ├── CalibrationModal.tsx
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   ├── api/
│   │   └── client.ts       # API calls
│   ├── types/
│   │   └── index.ts        # TypeScript types
│   ├── App.tsx             # Main app
│   ├── main.tsx            # Entry point
│   └── index.css           # Tailwind styles
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── package.json
```

---

## API Integration

The dashboard communicates with the FastAPI backend at `http://localhost:8000`.

### Endpoints Used:
- `GET /api/alerts` - Fetch alerts
- `GET /api/analytics/fleet-kpis` - KPI metrics
- `GET /api/analytics/vehicle/{id}/trends` - Vehicle trends
- `GET /api/calibration/driver/{id}` - Get settings
- `PUT /api/calibration/driver/{id}` - Update settings

**Note**: If API endpoints return 404 or error, it means the backend implementation from QUICKSTART.md hasn't been done yet.

---

## Styling

Uses **Tailwind CSS** for styling with custom color theme:
- Blue: Primary actions
- Orange: Drowsy alerts
- Red: Asleep alerts
- Green: Active/safe

Edit `tailwind.config.js` to customize colors.

---

## Development

### Adding a New Component

1. Create component in `src/components/`
2. Export from `src/components/index.ts`
3. Import in `src/App.tsx`
4. Use in JSX

### Modifying API Calls

Edit `src/api/client.ts` to change backend endpoints.

### Styling Components

All components use Tailwind CSS classes. No CSS files needed.

---

## Troubleshooting

### "Cannot find module 'leaflet'"
```bash
npm install leaflet @types/leaflet react-leaflet
```

### "API not responding (CORS error)"
- Make sure backend is running: `python -m uvicorn api_service.main:app`
- Verify proxy in `vite.config.ts` points to correct backend URL

### Dashboard shows "No data"
- Backend endpoints haven't been implemented (see QUICKSTART.md)
- Use mock data during development

### Slow performance
- Reduce alert limit in `App.tsx`
- Disable real-time polling (change 5000ms interval)

---

## Next Steps

1. ✅ Run `npm install` and `npm run dev`
2. ✅ Verify it connects to API
3. ✅ Test with real alerts from detector
4. ❌ (Optional) Deploy to production

---

**Created as part of Phase 6**
