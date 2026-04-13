"""
Shared configuration and constants across the enhanced drowsiness detector system.
"""
from enum import Enum
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# Explicitly load .env into environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


class DrowsinessState(str, Enum):
    """States in the drowsiness detection state machine."""
    ACTIVE = "active"
    DROWSY = "drowsy"
    ASLEEP = "asleep"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    WARNING = "warning"  # Drowsy
    CRITICAL = "critical"  # Asleep


class DetectionMode(str, Enum):
    """Detection model modes."""
    MEDIAPIPE = "mediapipe"
    DLIB = "dlib"


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017/drowsiness_detector"
    mongo_db_name: str = "drowsiness_detector"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    log_level: str = "DEBUG"
    
    # Detector
    detector_id: str = "detector_001"
    vehicle_id: str = "vehicle_001"
    driver_id: str = "driver_001"
    api_endpoint: str = "http://localhost:8000"
    
    # Location
    enable_gps: bool = True
    gps_update_interval: int = 5
    
    # Alerts
    alert_audio_enabled: bool = True
    alert_volume: int = 100
    
    # Models
    model_confidence_threshold: float = 0.5
    ear_calculation_mode: str = "mediapipe"
    
    # Local Cache
    local_cache_db: str = "detector_cache.db"
    cache_sync_interval: int = 30
    
    # Audio
    audio_format: str = "wav"
    audio_sample_rate: int = 44100
    
    # Logging
    log_file_path: str = "./logs/detector.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Security
    api_key: str = "your_secret_key_here"
    enable_cors: bool = True
    
    # Feature Flags
    enable_predictive_analytics: bool = True
    enable_emotion_detection: bool = True
    enable_head_pose: bool = True
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        case_sensitive=False,
        extra="ignore"
    )


# Drowsiness Detection Thresholds
class ThresholdConfig:
    """Default thresholds for drowsiness detection."""
    
    # State machine hysteresis
    STATE_CHANGE_FRAMES = 5  # Require 5 consecutive frames to transition states
    STATE_PERSISTENCE_SECONDS = 3.0  # Require state to persist for 3 seconds before alerting
    
    # EAR (Eye Aspect Ratio) raw value thresholds — used for normalization only
    EAR_AWAKE_THRESHOLD = 0.30   # EAR >= this → fully awake
    EAR_DROWSY_THRESHOLD = 0.20  # EAR between this and awake → drowsy
    EAR_ASLEEP_THRESHOLD = 0.12  # EAR <= this → eyes closed / asleep
    
    # ── Drowsiness SCORE thresholds (0-1 combined score, NOT raw EAR values) ──
    # These are what classify_state() and _update_state() should use.
    SCORE_ACTIVE_THRESHOLD = 0.35   # Score below this  → "active"
    SCORE_ASLEEP_THRESHOLD = 0.62   # Score above this  → "asleep"; between → "drowsy"
    
    # Head Pose thresholds (degrees)
    HEAD_PITCH_THRESHOLD = 25.0  # Forward nod
    HEAD_YAW_THRESHOLD = 40.0  # Side turn
    HEAD_ROLL_THRESHOLD = 30.0  # Tilt
    
    # Fatigue Score threshold
    FATIGUE_THRESHOLD = 0.6
    
    # Drowsiness Score calculation weights
    DROWSINESS_WEIGHTS = {
        "ear": 0.6,
        "head_pose": 0.2,
        "fatigue": 0.2
    }
    
    # Alert timing
    ALERT_WINDOW_DROWSY = 3.0  # seconds
    ALERT_WINDOW_ASLEEP = 1.0  # seconds
    
    # Location update interval
    LOCATION_UPDATE_INTERVAL = 5  # seconds
    
    # Calibration frames
    CALIBRATION_FRAMES = 300  # 10 seconds at 30 FPS


# API Response Templates
class ResponseTemplates:
    """Standard API response structures."""
    
    @staticmethod
    def success(data: dict, message: str = "Success") -> dict:
        return {
            "status": "success",
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message: str, code: str = "ERROR", details: Optional[dict] = None) -> dict:
        return {
            "status": "error",
            "message": message,
            "code": code,
            "details": details or {}
        }


# Get settings instance
settings = Settings()
