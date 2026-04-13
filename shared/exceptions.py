"""
Custom exceptions for the drowsiness detector system.
"""


class DrowsinessDetectorException(Exception):
    """Base exception for drowsiness detector."""
    
    def __init__(self, message: str, code: str = "DETECTOR_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DetectorServiceException(DrowsinessDetectorException):
    """Exception from detector service."""
    code = "DETECTOR_SERVICE_ERROR"


class APIServiceException(DrowsinessDetectorException):
    """Exception from API service."""
    code = "API_SERVICE_ERROR"


class DatabaseException(DrowsinessDetectorException):
    """Database operation exception."""
    code = "DATABASE_ERROR"


class ModelLoadException(DrowsinessDetectorException):
    """Exception when loading ML models."""
    code = "MODEL_LOAD_ERROR"


class CalibrationException(DrowsinessDetectorException):
    """Exception during calibration."""
    code = "CALIBRATION_ERROR"


class LocationServiceException(DrowsinessDetectorException):
    """Exception from location service."""
    code = "LOCATION_SERVICE_ERROR"


class AudioException(DrowsinessDetectorException):
    """Exception from audio service."""
    code = "AUDIO_ERROR"


class ValidationException(DrowsinessDetectorException):
    """Data validation exception."""
    code = "VALIDATION_ERROR"


class ConfigurationException(DrowsinessDetectorException):
    """Configuration error."""
    code = "CONFIGURATION_ERROR"


class CacheException(DrowsinessDetectorException):
    """Local cache exception."""
    code = "CACHE_ERROR"


class WebSocketException(DrowsinessDetectorException):
    """WebSocket communication exception."""
    code = "WEBSOCKET_ERROR"


class TimeoutException(DrowsinessDetectorException):
    """Operation timeout exception."""
    code = "TIMEOUT_ERROR"


class AuthenticationException(DrowsinessDetectorException):
    """Authentication/Authorization exception."""
    code = "AUTH_ERROR"
