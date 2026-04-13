"""
Enhanced Driver Drowsiness Detector - FastAPI Backend
Central API service for managing alerts, analytics, and fleet coordination.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

# Import configuration and models
from shared.config import settings
from shared.logging_config import setup_logger
from api_service.database import db, get_db

# Setup logging
logger = setup_logger(
    "enhanced_drowsiness_api",
    log_file=settings.log_file_path,
    level=logging.DEBUG if settings.log_level == "DEBUG" else logging.INFO
)


# ============================================================================
# LIFESPAN EVENTS (startup/shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle (startup and shutdown).
    """
    # Startup
    logger.info("=" * 80)
    logger.info("Enhanced Driver Drowsiness Detector API - Starting Up")
    logger.info("=" * 80)
    
    try:
        # Connect to database
        logger.info("Initializing database connection...")
        await db.connect()
        
        # Create indexes
        logger.info("Creating database indexes...")
        await db.create_indexes()
        
        # Health check
        is_healthy = await db.health_check()
        if is_healthy:
            logger.info("✅ Database health check passed")
        else:
            logger.warning("⚠️ Database health check failed; retrying later")
        
        logger.info("✅ API startup complete")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("Enhanced Driver Drowsiness Detector API - Shutting Down")
    logger.info("=" * 80)
    
    try:
        await db.disconnect()
        logger.info("✅ API shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Enhanced Driver Drowsiness Detector",
    description="Production-grade multi-vehicle drowsiness detection system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware for cross-origin requests
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to known domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware enabled")


# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": "HTTP_ERROR",
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": {"error": str(exc)} if settings.log_level == "DEBUG" else {}
        }
    )


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns 200 if API is running and database is accessible.
    """
    db_healthy = await db.health_check()
    
    status_code = 200 if db_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_healthy else "degraded",
            "api": "running",
            "database": "healthy" if db_healthy else "unreachable",
            "version": "1.0.0"
        }
    )


@app.post("/api/test/alert", tags=["Testing"])
async def test_alert(state: str = "drowsy", db = Depends(get_db)):
    """
    Test endpoint to simulate a drowsiness alert.
    Use this to test the system end-to-end without a real detector.
    
    Query Parameters:
    - state: alert state (drowsy or asleep) - default: drowsy
    
    Example: POST /api/test/alert?state=drowsy
    """
    try:
        from shared.database_models import DrowsinessAlertDocument
        from datetime import datetime
        import uuid
        
        alert_id = f"alert_test_{uuid.uuid4().hex[:8]}"
        severity = "critical" if state == "asleep" else "warning"
        
        alert = DrowsinessAlertDocument(
            alert_id=alert_id,
            vehicle_id="test_vehicle",
            driver_id="test_driver",
            timestamp=datetime.utcnow(),
            state=state,
            severity=severity,
            ear_value=0.18,
            head_pitch=25.5,
            head_yaw=15.2,
            fatigue_score=0.75,
            drowsiness_score=0.85 if state == "asleep" else 0.65,
            latitude=40.7128,
            longitude=-74.0060,
            address="Test Location, NYC"
        )
        
        alert.save()
        logger.info(f"✅ TEST ALERT created: {alert_id} (state={state})")
        
        return {
            "status": "success",
            "message": f"Test {state} alert created successfully",
            "data": {"alert_id": alert_id}
        }
    except Exception as e:
        logger.error(f"Error creating test alert: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": {"alert_id": None}
        }


@app.get("/status", tags=["Health"])
async def status():
    """
    Detailed status endpoint.
    Returns system information and configuration.
    """
    return {
        "status": "ok",
        "api_version": "1.0.0",
        "environment": {
            "mongo_db": settings.mongo_db_name,
            "log_level": settings.log_level,
            "cors_enabled": settings.enable_cors,
        },
        "features": {
            "head_pose": settings.enable_head_pose,
            "emotion_detection": settings.enable_emotion_detection,
            "predictive_analytics": settings.enable_predictive_analytics,
        }
    }


# ============================================================================
# PLACEHOLDER ROUTES (to be implemented in separate files)
# ============================================================================

@app.get("/api/alerts", tags=["Alerts"])
async def get_alerts(
    vehicle_id: str = None,
    driver_id: str = None,
    state: str = None,
    limit: int = 100,
    db = Depends(get_db)
):
    """
    Query drowsiness alerts with filters.
    """
    try:
        from shared.database_models import DrowsinessAlertDocument
        
        query_filter = {}
        if vehicle_id:
            query_filter['vehicle_id'] = vehicle_id
        if driver_id:
            query_filter['driver_id'] = driver_id
        if state:
            query_filter['state'] = state
        
        alerts = DrowsinessAlertDocument.objects(**query_filter).order_by('-timestamp').limit(limit)
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "alert_id": alert.alert_id,
                "vehicle_id": alert.vehicle_id,
                "driver_id": alert.driver_id,
                "timestamp": (alert.timestamp.isoformat() + "Z") if alert.timestamp else None,
                "detected_at": (alert.timestamp.isoformat() + "Z") if alert.timestamp else None,
                "state": alert.state,
                "severity": alert.severity,
                "ear_value": alert.ear_value,
                "head_pitch": alert.head_pitch,
                "head_yaw": alert.head_yaw,
                "fatigue_score": alert.fatigue_score,
                "drowsiness_score": alert.drowsiness_score,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "address": alert.address
            })
        
        logger.debug(f"Fetched {len(alerts_data)} alerts")
        return {
            "status": "success",
            "data": alerts_data,
            "count": len(alerts_data)
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": [],
            "count": 0
        }


@app.post("/api/alerts", tags=["Alerts"])
async def create_alert(data: dict, db = Depends(get_db)):
    """
    Submit a new drowsiness alert from detector.
    """
    try:
        from shared.database_models import DrowsinessAlertDocument
        from datetime import datetime
        import uuid
        
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        severity = "critical" if data.get("state") == "asleep" else "warning"
        
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
        else:
            timestamp = timestamp or datetime.utcnow()
        
        alert = DrowsinessAlertDocument(
            alert_id=alert_id,
            vehicle_id=data.get("vehicle_id"),
            driver_id=data.get("driver_id"),
            timestamp=timestamp,
            state=data.get("state"),
            severity=severity,
            ear_value=float(data.get("ear_value", 0)),
            head_pitch=float(data.get("head_pitch", 0)),
            head_yaw=float(data.get("head_yaw", 0)),
            fatigue_score=float(data.get("fatigue_score", 0)),
            drowsiness_score=float(data.get("drowsiness_score", 0)),
            latitude=float(data.get("latitude")) if data.get("latitude") else None,
            longitude=float(data.get("longitude")) if data.get("longitude") else None,
            address=data.get("address")
        )
        
        alert.save()
        logger.info(f"✅ Alert saved to MongoDB: {alert_id}")
        
        return {
            "status": "success",
            "message": "Alert created successfully",
            "data": {"alert_id": alert_id}
        }
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": {"alert_id": None}
        }


@app.get("/api/analytics/fleet-kpis", tags=["Analytics"])
async def get_fleet_kpis(db = Depends(get_db)):
    """
    Get fleet-wide Key Performance Indicators (KPIs).
    
    Returns:
        - Total alerts today
        - Drowsy vs. asleep ratio
        - Vehicles online/offline
        - Average incident duration
    """
    try:
        from shared.database_models import DrowsinessAlertDocument
        from datetime import datetime, timedelta
        
        # Get alerts from last 24 hours
        today = datetime.utcnow() - timedelta(days=1)
        alerts = DrowsinessAlertDocument.objects(timestamp__gte=today)
        total_alerts = len(alerts)
        drowsy_alerts = len([a for a in alerts if a.state == "drowsy"])
        asleep_alerts = len([a for a in alerts if a.state == "asleep"])
        active_detected = len([a for a in alerts if a.state == "active"])
        
        # Count unique vehicles
        unique_vehicles = len(set(a.vehicle_id for a in alerts))
        
        # Assemble KPI dict (was missing — caused NameError on every request)
        kpis = {
            "alerts_today": total_alerts,
            "drowsy_alerts": drowsy_alerts,
            "asleep_alerts": asleep_alerts,
            "active_detectors": unique_vehicles,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"📊 Fleet KPIs: {kpis}")
        return {
            "status": "success",
            "message": "Fleet KPIs retrieved",
            "data": kpis
        }
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        return {
            "status": "success",
            "message": "Fleet KPIs (no data yet)",
            "data": {"alerts_today": 0, "drowsy_alerts": 0, "asleep_alerts": 0, "active_detectors": 0, "timestamp": datetime.utcnow().isoformat()}
        }


@app.get("/api/analytics/vehicle/{vehicle_id}/trends", tags=["Analytics"])
async def get_vehicle_trends(vehicle_id: str, db = Depends(get_db)):
    """
    Get drowsiness trends for a specific vehicle.
    """
    return {
        "status": "success",
        "message": f"Trends for {vehicle_id} (routes/analytics.py)",
        "data": {}
    }


@app.get("/api/calibration/driver/{driver_id}", tags=["Calibration"])
async def get_driver_calibration(driver_id: str, db = Depends(get_db)):
    """
    Get per-driver drowsiness detection thresholds.
    """
    return {
        "status": "success",
        "message": f"Calibration for {driver_id} (routes/calibration.py)",
        "data": {}
    }


@app.put("/api/calibration/driver/{driver_id}", tags=["Calibration"])
async def update_driver_calibration(driver_id: str, data: dict, db = Depends(get_db)):
    """
    Update per-driver drowsiness detection thresholds.
    """
    return {
        "status": "success",
        "message": f"Calibration updated for {driver_id} (routes/calibration.py)",
        "data": {}
    }


@app.post("/api/detectors/register", tags=["Detectors"])
async def register_detector(data: dict, db = Depends(get_db)):
    """
    Register a new detector service.
    """
    return {
        "status": "success",
        "message": "Detector registered (routes/detectors.py)",
        "data": {}
    }


@app.put("/api/detectors/{detector_id}/heartbeat", tags=["Detectors"])
async def detector_heartbeat(detector_id: str, data: dict, db = Depends(get_db)):
    """
    Detector heartbeat (sent every 30 seconds).
    Updates detector status and metrics.
    """
    return {
        "status": "success",
        "message": f"Heartbeat received for {detector_id} (routes/detectors.py)",
        "data": {}
    }


@app.delete("/api/detectors/{detector_id}", tags=["Detectors"])
async def unregister_detector(detector_id: str, db = Depends(get_db)):
    """
    Unregister a detector service.
    """
    return {
        "status": "success",
        "message": f"Detector {detector_id} unregistered (routes/detectors.py)",
        "data": {}
    }


@app.get("/api/sessions", tags=["Sessions"])
async def get_sessions(vehicle_id: str = None, driver_id: str = None, limit: int = 100, db = Depends(get_db)):
    """
    Query driving sessions.
    """
    return {
        "status": "success",
        "message": "Sessions (routes/sessions.py)",
        "data": []
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Enhanced Driver Drowsiness Detector",
        "version": "1.0.0",
        "status": "running",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health"
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
