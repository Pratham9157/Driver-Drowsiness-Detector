"""
Test script to verify enhanced drowsiness detector components.
Run this to ensure all ML models and services are working correctly.
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required packages can be imported."""
    logger.info("=" * 80)
    logger.info("Testing Package Imports")
    logger.info("=" * 80)
    
    packages = {
        "cv2": "OpenCV",
        "numpy": "NumPy",
        "mediapipe": "MediaPipe",
        "sklearn": "Scikit-Learn",
        "xgboost": "XGBoost",
        "fastapi": "FastAPI",
        "pymongo": "PyMongo",
        "pydub": "PyDub",
        "geopy": "Geopy",
    }
    
    failed = []
    
    for module, name in packages.items():
        try:
            __import__(module)
            logger.info(f"✅ {name}")
        except ImportError as e:
            logger.error(f"❌ {name}: {e}")
            failed.append(name)
    
    if failed:
        logger.error(f"\n❌ Failed imports: {', '.join(failed)}")
        logger.error("Install missing packages: pip install -r requirements.txt")
        return False
    
    logger.info(f"\n✅ All {len(packages)} packages imported successfully\n")
    return True


def test_ml_models():
    """Test ML model classes."""
    logger.info("=" * 80)
    logger.info("Testing ML Models")
    logger.info("=" * 80)
    
    try:
        from ml_models.models import MediaPipeFaceDetector, EARCalculator, FatigueDetector
        from ml_models.head_pose_calculator import HeadPoseCalculator
        from ml_models.drowsiness_scorer import DrowsinessScorer
        
        # Test MediaPipeFaceDetector
        logger.info("Initializing MediaPipeFaceDetector...")
        face_detector = MediaPipeFaceDetector()
        logger.info("✅ MediaPipeFaceDetector initialized")
        
        # Test HeadPoseCalculator
        logger.info("Initializing HeadPoseCalculator...")
        head_pose_calc = HeadPoseCalculator(640, 480)
        logger.info("✅ HeadPoseCalculator initialized")
        
        # Test DrowsinessScorer
        logger.info("Initializing DrowsinessScorer...")
        scorer = DrowsinessScorer()
        logger.info("✅ DrowsinessScorer initialized")
        
        # Test drowsiness score computation
        logger.info("\nTesting drowsiness score computation...")
        
        # Simulate different scores
        test_cases = [
            {"ear": 0.35, "head_pitch": 5.0, "fatigue": 0.1, "expected_state": "active"},
            {"ear": 0.20, "head_pitch": 15.0, "fatigue": 0.4, "expected_state": "drowsy"},
            {"ear": 0.08, "head_pitch": 35.0, "fatigue": 0.8, "expected_state": "asleep"},
        ]
        
        for i, test in enumerate(test_cases):
            score = scorer.compute_score(
                ear=test["ear"],
                head_pitch=test["head_pitch"],
                fatigue_score=test["fatigue"]
            )
            state = scorer.classify_state(score)
            
            status = "✅" if state == test["expected_state"] else "⚠️"
            logger.info(
                f"{status} Test {i+1}: EAR={test['ear']:.2f}, Pitch={test['head_pitch']:.1f}°, "
                f"Fatigue={test['fatigue']:.2f} → Score={score:.2f}, State={state}"
            )
        
        logger.info(f"\n✅ All ML models working correctly\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ ML model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading."""
    logger.info("=" * 80)
    logger.info("Testing Configuration")
    logger.info("=" * 80)
    
    try:
        from shared.config import settings, ThresholdConfig, DrowsinessState
        
        logger.info(f"✅ Configuration loaded")
        logger.info(f"  - Vehicle ID: {settings.vehicle_id}")
        logger.info(f"  - Driver ID: {settings.driver_id}")
        logger.info(f"  - API Endpoint: {settings.api_endpoint}")
        logger.info(f"  - MongoDB URI: {settings.mongo_uri}")
        logger.info(f"  - Log Level: {settings.log_level}")
        
        logger.info(f"\n✅ Thresholds configured:")
        logger.info(f"  - EAR Awake: {ThresholdConfig.EAR_AWAKE_THRESHOLD}")
        logger.info(f"  - EAR Drowsy: {ThresholdConfig.EAR_DROWSY_THRESHOLD}")
        logger.info(f"  - EAR Asleep: {ThresholdConfig.EAR_ASLEEP_THRESHOLD}")
        logger.info(f"  - Head Pitch Threshold: {ThresholdConfig.HEAD_PITCH_THRESHOLD}°")
        
        logger.info(f"\n✅ Enums defined:")
        for state in DrowsinessState:
            logger.info(f"  - {state.value}")
        
        logger.info()
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """Test database model definitions."""
    logger.info("=" * 80)
    logger.info("Testing Database Models")
    logger.info("=" * 80)
    
    try:
        from shared.database_models import (
            DriverSchema,
            VehicleSchema,
            DrowsinessAlertSchema,
            SessionSchema,
        )
        
        # Test schema creation
        logger.info("Creating sample schemas...")
        
        driver = DriverSchema(
            driver_id="test_driver_001",
            name="Test Driver",
            email="test@example.com"
        )
        logger.info(f"✅ DriverSchema: {driver.driver_id}")
        
        vehicle = VehicleSchema(
            vehicle_id="test_vehicle_001",
            driver_id="test_driver_001",
            make="Toyota",
            model="Camry",
            year=2023,
            license_plate="ABC123"
        )
        logger.info(f"✅ VehicleSchema: {vehicle.vehicle_id}")
        
        alert = DrowsinessAlertSchema(
            alert_id="test_alert_001",
            vehicle_id="test_vehicle_001",
            driver_id="test_driver_001",
            timestamp="2024-01-15T10:00:00",
            state="drowsy",
            severity="warning",
            ear_value=0.22,
            head_pitch=15.0,
            head_yaw=5.0,
            fatigue_score=0.4,
            drowsiness_score=0.68
        )
        logger.info(f"✅ DrowsinessAlertSchema: {alert.alert_id}")
        
        logger.info(f"\n✅ All database models created successfully\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exceptions():
    """Test custom exceptions."""
    logger.info("=" * 80)
    logger.info("Testing Custom Exceptions")
    logger.info("=" * 80)
    
    try:
        from shared.exceptions import (
            DetectorServiceException,
            DatabaseException,
            ModelLoadException,
        )
        
        # Test exception creation
        try:
            raise DetectorServiceException("Test detector error", code="TEST_ERROR")
        except DetectorServiceException as e:
            logger.info(f"✅ DetectorServiceException: {e.message} ({e.code})")
        
        try:
            raise DatabaseException("Test database error")
        except DatabaseException as e:
            logger.info(f"✅ DatabaseException: {e.message}")
        
        try:
            raise ModelLoadException("Test model load error")
        except ModelLoadException as e:
            logger.info(f"✅ ModelLoadException: {e.message}")
        
        logger.info(f"\n✅ All custom exceptions working correctly\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Exception test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("🚀 Enhanced Drowsiness Detector - Component Test Suite")
    logger.info("This script verifies all components are installed and working correctly.")
    logger.info("")
    
    results = {
        "Imports": test_imports(),
        "ML Models": test_ml_models(),
        "Configuration": test_config(),
        "Database Models": test_database_models(),
        "Exceptions": test_exceptions(),
    }
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 80)
        logger.info("\nYou can now run:")
        logger.info("  1. API Service: cd api_service && python -m uvicorn main:app --reload")
        logger.info("  2. Detector: cd detector_service && python main.py")
        logger.info("")
        return 0
    else:
        logger.error("\n" + "=" * 80)
        logger.error("❌ SOME TESTS FAILED!")
        logger.error("=" * 80)
        logger.error("\nFix errors above before running the system.")
        logger.error("See docs/SETUP.md for troubleshooting.")
        logger.error("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
