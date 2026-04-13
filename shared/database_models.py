"""
Database models and Pydantic schemas for the drowsiness detector system.
Uses MongoEngine for MongoDB document definitions and Pydantic for API validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from mongoengine import (
    Document, StringField, FloatField, IntField, DateTimeField,
    ListField, DictField, BooleanField, EmbeddedDocument, EmbeddedDocumentField
)


# ============================================================================
# PYDANTIC SCHEMAS (for API validation and serialization)
# ============================================================================

class DriverCalibration(BaseModel):
    """Per-driver drowsiness detection calibration settings."""
    ear_awake_threshold: float = 0.3
    ear_drowsy_threshold: float = 0.2
    ear_asleep_threshold: float = 0.1
    head_pitch_threshold: float = 25.0
    head_yaw_threshold: float = 40.0
    fatigue_threshold: float = 0.6
    last_calibrated: datetime = Field(default_factory=datetime.utcnow)


class DriverSchema(BaseModel):
    """API schema for driver data."""
    driver_id: str
    name: str
    email: str
    phone: Optional[str] = None
    calibration: Optional[DriverCalibration] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "driver_001",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "is_active": True
            }
        }


class VehicleSchema(BaseModel):
    """API schema for vehicle data."""
    vehicle_id: str
    driver_id: str
    make: str
    model: str
    year: int
    license_plate: str
    is_active: bool = True
    detector_status: Optional[str] = "offline"  # offline, online, drowsy, asleep
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "vehicle_id": "vehicle_001",
                "driver_id": "driver_001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "license_plate": "ABC123"
            }
        }


class LocationData(BaseModel):
    """Location information."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DrowsinessAlertSchema(BaseModel):
    """API schema for drowsiness alerts."""
    alert_id: str
    vehicle_id: str
    driver_id: str
    timestamp: datetime
    state: str  # active, drowsy, asleep
    severity: str  # warning, critical
    ear_value: float
    head_pitch: float
    head_yaw: float
    fatigue_score: float
    drowsiness_score: float
    location: Optional[LocationData] = None
    duration_seconds: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert_001",
                "vehicle_id": "vehicle_001",
                "driver_id": "driver_001",
                "timestamp": datetime.utcnow(),
                "state": "drowsy",
                "severity": "warning",
                "ear_value": 0.25,
                "drowsiness_score": 0.65
            }
        }


class SessionSchema(BaseModel):
    """API schema for driving session data."""
    session_id: str
    vehicle_id: str
    driver_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_minutes: float = 0.0
    total_drowsy_time_seconds: float = 0.0
    total_asleep_time_seconds: float = 0.0
    drowsy_incidents: int = 0
    asleep_incidents: int = 0
    max_drowsiness_score: float = 0.0
    avg_drowsiness_score: float = 0.0
    is_completed: bool = False
    notes: Optional[str] = None


class AnomalyPredictionSchema(BaseModel):
    """API schema for predictive alerts."""
    prediction_id: str
    vehicle_id: str
    timestamp: datetime
    predicted_drowsiness_prob: float
    confidence: float
    time_to_drowsiness_seconds: Optional[float] = None
    recommendation: Optional[str] = None


class DetectorHeartbeatSchema(BaseModel):
    """API schema for detector service heartbeat."""
    detector_id: str
    vehicle_id: str
    driver_id: str
    timestamp: datetime
    uptime_seconds: float
    eye_landmarks_detected_count: int
    current_ear: float
    current_drowsiness_score: float
    current_state: str  # active, drowsy, asleep
    api_latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    has_local_cache: bool
    local_cache_size: int


# ============================================================================
# MONGOENGINE DOCUMENTS (for MongoDB storage)
# ============================================================================

class DriverDocument(Document):
    """MongoDB document for driver data."""
    driver_id = StringField(primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    phone = StringField(null=True)
    calibration_ear_awake = FloatField(default=0.3)
    calibration_ear_drowsy = FloatField(default=0.2)
    calibration_ear_asleep = FloatField(default=0.1)
    calibration_head_pitch = FloatField(default=25.0)
    calibration_head_yaw = FloatField(default=40.0)
    calibration_fatigue = FloatField(default=0.6)
    last_calibrated = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'drivers',
        'indexes': ['driver_id', 'email']
    }


class VehicleDocument(Document):
    """MongoDB document for vehicle data."""
    vehicle_id = StringField(primary_key=True)
    driver_id = StringField(required=True)
    make = StringField(required=True)
    model = StringField(required=True)
    year = IntField(required=True)
    license_plate = StringField(required=True, unique=True)
    is_active = BooleanField(default=True)
    detector_status = StringField(default="offline")  # offline, online, drowsy, asleep
    last_heartbeat = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'vehicles',
        'indexes': ['vehicle_id', 'driver_id', 'license_plate']
    }


class DrowsinessAlertDocument(Document):
    """MongoDB document for drowsiness alerts."""
    alert_id = StringField(primary_key=True)
    vehicle_id = StringField(required=True)
    driver_id = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow, required=True)
    state = StringField(required=True)  # active, drowsy, asleep
    severity = StringField(required=True)  # warning, critical
    ear_value = FloatField(required=True)
    head_pitch = FloatField(required=True)
    head_yaw = FloatField(required=True)
    fatigue_score = FloatField(required=True)
    drowsiness_score = FloatField(required=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    address = StringField(null=True)
    city = StringField(null=True)
    country = StringField(null=True)
    duration_seconds = FloatField(null=True)
    notes = StringField(null=True)
    
    meta = {
        'collection': 'drowsiness_alerts',
        'indexes': [
            'vehicle_id',
            'driver_id',
            'timestamp',
            ('vehicle_id', 'timestamp'),
            ('driver_id', 'timestamp')
        ]
    }


class SessionDocument(Document):
    """MongoDB document for driving sessions."""
    session_id = StringField(primary_key=True)
    vehicle_id = StringField(required=True)
    driver_id = StringField(required=True)
    start_time = DateTimeField(default=datetime.utcnow, required=True)
    end_time = DateTimeField(null=True)
    total_duration_minutes = FloatField(default=0.0)
    total_drowsy_time_seconds = FloatField(default=0.0)
    total_asleep_time_seconds = FloatField(default=0.0)
    drowsy_incidents = IntField(default=0)
    asleep_incidents = IntField(default=0)
    max_drowsiness_score = FloatField(default=0.0)
    avg_drowsiness_score = FloatField(default=0.0)
    is_completed = BooleanField(default=False)
    notes = StringField(null=True)
    
    meta = {
        'collection': 'sessions',
        'indexes': [
            'vehicle_id',
            'driver_id',
            'start_time',
            ('vehicle_id', 'start_time'),
            ('driver_id', 'start_time')
        ]
    }


class AnomalyPredictionDocument(Document):
    """MongoDB document for predictive anomalies."""
    prediction_id = StringField(primary_key=True)
    vehicle_id = StringField(required=True)
    driver_id = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow, required=True)
    predicted_drowsiness_prob = FloatField(required=True)
    confidence = FloatField(required=True)
    time_to_drowsiness_seconds = FloatField(null=True)
    recommendation = StringField(null=True)
    was_accurate = BooleanField(null=True)  # Set after actual drowsiness detected
    
    meta = {
        'collection': 'anomaly_predictions',
        'indexes': [
            'vehicle_id',
            'driver_id',
            'timestamp'
        ]
    }


class DetectorHeartbeatDocument(Document):
    """MongoDB document for detector service heartbeats."""
    heartbeat_id = StringField(primary_key=True)
    detector_id = StringField(required=True)
    vehicle_id = StringField(required=True)
    driver_id = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow, required=True)
    uptime_seconds = FloatField(required=True)
    eye_landmarks_detected_count = IntField(required=True)
    current_ear = FloatField(required=True)
    current_drowsiness_score = FloatField(required=True)
    current_state = StringField(required=True)
    api_latency_ms = FloatField(required=True)
    memory_usage_mb = FloatField(required=True)
    cpu_usage_percent = FloatField(required=True)
    has_local_cache = BooleanField(default=False)
    local_cache_size = IntField(default=0)
    
    meta = {
        'collection': 'detector_heartbeats',
        'indexes': [
            'detector_id',
            'vehicle_id',
            'timestamp',
            ('detector_id', 'timestamp')
        ]
    }
