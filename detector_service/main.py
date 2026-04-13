"""
Enhanced Driver Drowsiness Detector - Detector Service
Per-vehicle (per-laptop) drowsiness detection using MediaPipe, head pose, and fatigue signals.
"""
import cv2
import asyncio
import logging
import time
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import aiohttp

# Import ML models
from ml_models.models import MediaPipeFaceDetector, EARCalculator, FatigueDetector
from ml_models.head_pose_calculator import HeadPoseCalculator
from ml_models.drowsiness_scorer import DrowsinessScorer

# Import shared utilities
from shared.config import settings, ThresholdConfig, DrowsinessState
from shared.logging_config import setup_logger
from shared.exceptions import DetectorServiceException


# Setup logging
logger = setup_logger(
    "drowsiness_detector",
    log_file=settings.log_file_path,
    level=logging.DEBUG if settings.log_level == "DEBUG" else logging.INFO
)


class DrownessDetectorService:
    """
    Main drowsiness detection service.
    Runs continuously, processing video frames and detecting drowsiness.
    """
    
    def __init__(
        self,
        vehicle_id: str = None,
        driver_id: str = None,
        detector_id: str = None,
        camera_index: int = 0,
        fps: int = 30,
        frame_width: int = 640,
        frame_height: int = 480,
        test_mode: bool = False
    ):
        """
        Initialize detector service.
        
        Args:
            vehicle_id: Vehicle identifier
            driver_id: Driver identifier
            detector_id: Detector instance identifier
            camera_index: Webcam device index (usually 0)
            fps: Frames per second target
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            test_mode: If True, simulates drowsiness pattern for testing
        """
        self.vehicle_id = vehicle_id or settings.vehicle_id
        self.driver_id = driver_id or settings.driver_id
        self.detector_id = detector_id or settings.detector_id
        self.camera_index = camera_index
        self.fps = fps
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_time = 1.0 / fps  # milliseconds
        self.test_mode = test_mode
        
        # ML Models
        self.face_detector = MediaPipeFaceDetector()
        self.ear_calculator = EARCalculator()
        self.head_pose_calc = HeadPoseCalculator(frame_width, frame_height)
        self.fatigue_detector = FatigueDetector()
        self.drowsiness_scorer = DrowsinessScorer()
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # State tracking
        self.current_state = DrowsinessState.ACTIVE
        self.state_frame_count = 0
        self.state_start_time: Optional[float] = None
        self.state_persistence_start: Optional[float] = None  # Track when state became drowsy/asleep
        
        # Test mode tracking
        self.test_frame_counter = 0
        self.test_location_base = (40.7128, -74.0060)  # Default to NYC, will be updated in test mode
        
        # Metrics
        self.frame_count = 0
        self.detection_latencies = []
        self.start_time = time.time()
        
        # Alert tracking
        self.last_alert_time: Optional[float] = None
        self.alert_window_drowsy = ThresholdConfig.ALERT_WINDOW_DROWSY
        self.alert_window_asleep = ThresholdConfig.ALERT_WINDOW_ASLEEP
        self.state_persistence_seconds = ThresholdConfig.STATE_PERSISTENCE_SECONDS
        
        logger.info(f"Detector initialized: vehicle={self.vehicle_id}, driver={self.driver_id}")
    
    async def initialize(self):
        """
        Initialize camera and verify setup.
        Tries multiple camera indices if default fails.
        """
        # Try up to 3 camera indices (0, 1, 2)
        for camera_idx in [self.camera_index, 0, 1, 2]:
            try:
                logger.info(f"🎥 Attempting to open camera (index {camera_idx})...")
                self.cap = cv2.VideoCapture(camera_idx)
                
                # Give camera time to initialize
                import asyncio
                await asyncio.sleep(1)
                
                if not self.cap.isOpened():
                    logger.warning(f"⚠️ Camera {camera_idx} not available")
                    if self.cap:
                        self.cap.release()
                    continue
                
                # Try to read a test frame
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    logger.warning(f"⚠️ Camera {camera_idx} opened but cannot read frames")
                    self.cap.release()
                    continue
                
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for fresh frames
                
                logger.info(f"✅ Camera {camera_idx} initialized: {self.frame_width}x{self.frame_height} @ {self.fps} FPS")
                return  # Success!
                
            except Exception as e:
                logger.warning(f"⚠️ Camera {camera_idx} initialization failed: {e}")
                continue
        
        # All camera indices failed
        logger.error("❌ No camera available at indices 0-2")
        logger.error("💡 TIP: Run with --test flag if camera is not available:")
        logger.error("   python -m detector_service.main --test")
        logger.error("   or: set TEST_MODE=true & python -m detector_service.main")
        raise DetectorServiceException(
            "No camera found. Use --test mode instead.",
            code="NO_CAMERA_AVAILABLE"
        )
    
    async def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a single video frame for drowsiness detection.
        
        Args:
            frame: Input video frame (BGR)
        
        Returns:
            Dictionary with detection results and metrics
        """
        frame_start = time.time()
        
        try:
            # Detect face landmarks
            landmarks, metadata = self.face_detector.detect(frame)
            
            if landmarks is None:
                return {
                    "success": False,
                    "frame_count": self.frame_count,
                    "reason": "No face detected",
                    "latency_ms": (time.time() - frame_start) * 1000
                }
            
            # Calculate EAR
            left_eye, right_eye = self.face_detector.get_eye_landmarks(landmarks)
            left_ear, right_ear, avg_ear = self.ear_calculator.compute_both_eyes_ear(
                landmarks,
                self.ear_calculator.RIGHT_EYE_INDICES,
                self.ear_calculator.LEFT_EYE_INDICES
            )
            
            # Estimate head pose
            pose_success, rot_vec, trans_vec, head_angles = self.head_pose_calc.estimate_pose(landmarks)
            
            if not pose_success or head_angles is None:
                head_pitch, head_yaw, head_roll = 0.0, 0.0, 0.0
            else:
                head_pitch, head_yaw, head_roll = head_angles
            
            # Compute fatigue score (placeholder for now)
            # In production, would extract eye region and run neural net
            fatigue_score = self.fatigue_detector.detect(frame)
            
            # Compute integrated drowsiness score
            instant_score, smoothed_score = self.drowsiness_scorer.compute_smoothed_score(
                ear=avg_ear,
                head_pitch=head_pitch,
                head_yaw=head_yaw,
                head_roll=head_roll,
                fatigue_score=fatigue_score,
                pitch_threshold=ThresholdConfig.HEAD_PITCH_THRESHOLD,
                yaw_threshold=ThresholdConfig.HEAD_YAW_THRESHOLD,
                roll_threshold=ThresholdConfig.HEAD_ROLL_THRESHOLD
            )
            
            # Classify state with hysteresis
            # IMPORTANT: use SCORE thresholds (0-1 combined score),
            # NOT the raw EAR value thresholds (which are 0.1-0.3).
            # Previously used EAR_ASLEEP_THRESHOLD=0.1 as drowsy_threshold,
            # which made "drowsy" unreachable (anything ≥ 0.3 jumped to "asleep").
            new_state = self.drowsiness_scorer.classify_state(
                smoothed_score,
                awake_threshold=ThresholdConfig.SCORE_ACTIVE_THRESHOLD,
                drowsy_threshold=ThresholdConfig.SCORE_ASLEEP_THRESHOLD
            )
            
            # Check for state transition (requires N consecutive frames)
            alert_generated = self._update_state(new_state, smoothed_score)
            
            latency_ms = (time.time() - frame_start) * 1000
            self.detection_latencies.append(latency_ms)
            
            result = {
                "success": True,
                "frame_count": self.frame_count,
                "timestamp": datetime.utcnow().isoformat(),
                "state": self.current_state.value,
                "ear": float(avg_ear),
                "head_pitch": float(head_pitch),
                "head_yaw": float(head_yaw),
                "head_roll": float(head_roll),
                "fatigue_score": float(fatigue_score),
                "drowsiness_score": float(smoothed_score),
                "alert_generated": alert_generated,
                "latency_ms": latency_ms,
                "landmarks_detected": len(landmarks)
            }
            
            self.frame_count += 1
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return {
                "success": False,
                "frame_count": self.frame_count,
                "reason": str(e),
                "latency_ms": (time.time() - frame_start) * 1000
            }
    
    async def _fetch_user_location_from_ip(self) -> tuple:
        """
        Fetch approximate user location based on IP address.
        Uses free IP geolocation API.
        Falls back to NYC if API unavailable.
        
        Returns:
            Tuple of (latitude, longitude)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://ip-api.com/json/?fields=lat,lon", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lat, lon = data.get("lat"), data.get("lon")
                        if lat and lon:
                            logger.info(f"📍 Detected location from IP: ({lat:.4f}, {lon:.4f})")
                            return (lat, lon)
        except asyncio.TimeoutError:
            logger.warning("⏱️ IP geolocation timeout, using default location")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch IP location: {e}, using default")
        
        logger.info("📍 Using default location (40.7128, -74.0060) - NYC")
        return (40.7128, -74.0060)
    
    def _update_state(self, new_state: str, drowsiness_score: float) -> bool:
        """
        Update drowsiness state with hysteresis.
        Only generates alerts if state persists for at least 10 seconds.
        
        Returns:
            True if alert should be generated, False otherwise
        """
        alert_generated = False
        current_time = time.time()
        
        # Convert to enum
        new_state_enum = DrowsinessState(new_state)
        
        # Check for state transition
        if new_state_enum == self.current_state:
            # Same state - check if we should alert
            self.state_frame_count = 0
            
            # If in drowsy/asleep state, check persistence time
            if new_state_enum in [DrowsinessState.DROWSY, DrowsinessState.ASLEEP]:
                if self.state_persistence_start is None:
                    self.state_persistence_start = current_time
                
                # Check if state has persisted for required time
                elapsed = current_time - self.state_persistence_start
                if elapsed >= self.state_persistence_seconds:
                    # State persisted long enough - check rate limiting
                    window = (
                        self.alert_window_asleep if new_state_enum == DrowsinessState.ASLEEP
                        else self.alert_window_drowsy
                    )
                    
                    # Rate limiting: don't alert more than once per window
                    if self.last_alert_time is None or (current_time - self.last_alert_time) > window:
                        alert_generated = True
                        self.last_alert_time = current_time
                        logger.warning(
                            f"🚨 ALERT: {new_state_enum.value.upper()} detected (score={drowsiness_score:.2f}, "
                            f"persisted for {elapsed:.1f}s)"
                        )
            else:
                # Back to active state, reset persistence timer
                self.state_persistence_start = None
        else:
            # Different state
            self.state_frame_count += 1
            
            # Check if transition threshold met (5 frames)
            if self.state_frame_count >= ThresholdConfig.STATE_CHANGE_FRAMES:
                logger.warning(
                    f"State transition: {self.current_state.value} → {new_state_enum.value} "
                    f"(after {self.state_frame_count} frames)"
                )
                
                # Update state
                self.current_state = new_state_enum
                self.state_frame_count = 0
                self.state_start_time = current_time
                
                # Reset persistence timer for new state
                if new_state_enum in [DrowsinessState.DROWSY, DrowsinessState.ASLEEP]:
                    self.state_persistence_start = current_time
                else:
                    self.state_persistence_start = None
        
        return alert_generated
    
    def _generate_test_result(self) -> Dict[str, Any]:
        """
        Generate simulated drowsiness detection for testing.
        Cycles through states: ACTIVE → DROWSY (after 60 frames) → ASLEEP (after 120 frames) → ACTIVE (repeat)
        Also generates realistic GPS coordinates cycling around your detected location.
        """
        frame_start = time.time()
        self.test_frame_counter += 1
        
        # Drowsiness pattern (cycle of 450 frames ≈ 15 seconds at 30 FPS)
        # States each last long enough to exceed STATE_PERSISTENCE_SECONDS (3s).
        cycle_position = self.test_frame_counter % 450
        
        if cycle_position < 200:
            drowsiness_score = 0.15
            state = "active"
        elif cycle_position < 340:
            drowsiness_score = 0.52
            state = "drowsy"
        else:
            drowsiness_score = 0.80
            state = "asleep"
        
        # Simulate GPS coordinates moving around user's detected location
        # Cycle through 4 different points around the location every ~15 seconds
        base_lat, base_lon = self.test_location_base
        location_cycle = (self.test_frame_counter // 450) % 4
        
        # Offsets from center (±0.005 lat/lon = ~500m depending on latitude)
        offsets = {
            0: (0.005, 0.005),      # NE point
            1: (0.005, -0.005),     # NW point
            2: (-0.005, -0.005),    # SW point
            3: (-0.005, 0.005),     # SE point
        }
        
        offset_lat, offset_lon = offsets[location_cycle]
        lat = base_lat + offset_lat + (self.test_frame_counter % 5) * 0.0002
        lon = base_lon + offset_lon - (self.test_frame_counter % 5) * 0.0002
        
        # Simulate state transition
        alert_generated = self._update_state(state, drowsiness_score)
        
        result = {
            "success": True,
            "frame_count": self.frame_count,
            "timestamp": datetime.utcnow().isoformat(),
            "state": self.current_state.value,
            "ear": 0.25 - (drowsiness_score * 0.1),
            "head_pitch": 10 + (drowsiness_score * 20),
            "head_yaw": 5 + (drowsiness_score * 10),
            "head_roll": -2,
            "fatigue_score": drowsiness_score * 0.8,
            "drowsiness_score": drowsiness_score,
            "alert_generated": alert_generated,
            "latitude": lat,
            "longitude": lon,
            "latency_ms": (time.time() - frame_start) * 1000,
            "landmarks_detected": 468
        }
        
        self.frame_count += 1
        return result
    
    async def run(self, duration_seconds: Optional[int] = None):
        """
        Run the detector main loop.
        
        Args:
            duration_seconds: Run for N seconds (None = run indefinitely)
        """
        try:
            # Only initialize camera if not in test mode
            if not self.test_mode:
                await self.initialize()
            else:
                logger.info("🧪 TEST MODE ENABLED - Simulating drowsiness detection")
            
            self.is_running = True
            
            logger.info("=" * 80)
            logger.info("Starting detection loop...")
            logger.info("=" * 80)
            
            loop_start = time.time()
            
            while self.is_running:
                # Check duration limit
                if duration_seconds and (time.time() - loop_start) > duration_seconds:
                    logger.info(f"Duration limit reached ({duration_seconds}s); stopping")
                    break
                
                # Get detection result (real or test)
                if self.test_mode:
                    # Generate simulated drowsiness results for testing
                    result = self._generate_test_result()
                    frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
                else:
                    # Real detection from camera
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        logger.warning("⚠️ Failed to read frame from camera")
                        # Try to reinitialize camera
                        try:
                            self.cap.release()
                            await asyncio.sleep(0.5)
                            await self.initialize()
                            continue
                        except Exception as e:
                            logger.error(f"❌ Cannot recover camera: {e}")
                            logger.error("💡 TIP: Try running with --test mode instead")
                            break
                    
                    # Check if frame is all black (corrupted stream)
                    if frame.mean() < 5:  # Very dark frame (0-255 scale)
                        logger.warning(f"⚠️ Received black frame (mean brightness: {frame.mean():.1f})")
                        logger.warning("   Camera may need time to warm up. Waiting 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    
                    # Resize frame if needed
                    if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                        frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                    
                    # Flip frame horizontally for mirror effect
                    frame = cv2.flip(frame, 1)
                    
                    # Process frame
                    result = await self.process_frame(frame)
                
                # Display live feed with detection info
                display_frame = self._annotate_frame(frame, result)
                cv2.imshow(f'Detector - {self.vehicle_id} ({self.driver_id})', display_frame)
                
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Detector stopped by user (q key)")
                    break
                
                # Log results
                if result["success"]:
                    logger.debug(
                        f"Frame {result['frame_count']}: "
                        f"state={result['state']}, "
                        f"score={result['drowsiness_score']:.2f}, "
                        f"latency={result['latency_ms']:.1f}ms"
                    )
                    
                    # TODO: Send alert to central API if generated
                    if result["alert_generated"]:
                        await self._send_alert(result)
                else:
                    logger.debug(f"Frame {result['frame_count']}: {result['reason']}")
                
                # Frame rate control
                await asyncio.sleep(self.frame_time)
        
        except KeyboardInterrupt:
            logger.info("Detector interrupted by user")
        except Exception as e:
            logger.error(f"❌ Detector error: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    def _annotate_frame(self, frame: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """
        Annotate frame with detection results for display.
        
        Args:
            frame: Input video frame
            result: Detection result from process_frame()
            
        Returns:
            Annotated frame ready for display
        """
        annotated = frame.copy()
        height, width = annotated.shape[:2]
        
        # Define colors
        color_alert = (0, 0, 255)  # Red for alert/drowsy
        color_normal = (0, 255, 0)  # Green for normal
        color_text = (255, 255, 255)  # White text
        
        # Choose color based on state (state values are lowercase strings)
        state = result.get("state", "active")
        if state == "asleep":
            state_color = (0, 0, 255)    # Red — critical
        elif state == "drowsy":
            state_color = (0, 128, 255)  # Orange — warning
        else:
            state_color = color_normal   # Green — active
        
        # Define text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        line_height = 30
        
        # Top-left corner for text
        y_offset = 30
        
        # Draw background for text
        cv2.rectangle(annotated, (0, 0), (width, y_offset * 6), (0, 0, 0), -1)
        
        # Frame info
        cv2.putText(
            annotated,
            f"Frame: {result.get('frame_count', 0)} | FPS: {1/(self.frame_time or 0.033):.1f}",
            (10, y_offset),
            font,
            font_scale,
            color_text,
            thickness
        )
        
        # State
        state_text = f"State: {result['state']}"
        cv2.putText(
            annotated,
            state_text,
            (10, y_offset + line_height),
            font,
            font_scale,
            state_color,
            thickness
        )
        
        # Drowsiness score
        drowsiness_score = result.get("drowsiness_score", 0)
        score_text = f"Drowsiness: {drowsiness_score:.2%}"
        cv2.putText(
            annotated,
            score_text,
            (10, y_offset + line_height * 2),
            font,
            font_scale,
            color_text,
            thickness
        )
        
        # EAR value
        ear_value = result.get("ear", 0)
        ear_text = f"EAR: {ear_value:.3f}"
        cv2.putText(
            annotated,
            ear_text,
            (10, y_offset + line_height * 3),
            font,
            font_scale,
            color_text,
            thickness
        )
        
        # Head pose
        pitch = result.get("head_pitch", 0)
        yaw = result.get("head_yaw", 0)
        roll = result.get("head_roll", 0)
        pose_text = f"Pose - Pitch: {pitch:.1f}° Yaw: {yaw:.1f}° Roll: {roll:.1f}°"
        cv2.putText(
            annotated,
            pose_text,
            (10, y_offset + line_height * 4),
            font,
            font_scale,
            color_text,
            thickness
        )
        
        # Latency
        latency = result.get("latency_ms", 0)
        latency_text = f"Latency: {latency:.1f}ms"
        cv2.putText(
            annotated,
            latency_text,
            (10, y_offset + line_height * 5),
            font,
            font_scale,
            color_text,
            thickness
        )
        
        # Alert indicator if needed
        if result.get("alert_generated", False):
            cv2.rectangle(annotated, (width - 120, 10), (width - 10, 60), (0, 0, 255), 3)
            cv2.putText(
                annotated,
                "ALERT",
                (width - 110, 45),
                font,
                1.2,
                (0, 0, 255),
                3
            )
        
        return annotated
    
    async def _send_alert(self, frame_result: Dict[str, Any]):
        """
        Send alert to central API service.
        
        Args:
            frame_result: Detection result from process_frame()
        """
        try:
            alert_data = {
                "vehicle_id": self.vehicle_id,
                "driver_id": self.driver_id,
                "timestamp": frame_result["timestamp"],
                "state": frame_result["state"],
                "ear_value": frame_result["ear"],
                "head_pitch": frame_result["head_pitch"],
                "head_yaw": frame_result["head_yaw"],
                "head_roll": frame_result["head_roll"],
                "fatigue_score": frame_result["fatigue_score"],
                "drowsiness_score": frame_result["drowsiness_score"],
                "latitude": frame_result.get("latitude"),
                "longitude": frame_result.get("longitude"),
            }
            
            # Send alert to API (use localhost for local connections, not 0.0.0.0)
            api_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
            api_url = f"http://{api_host}:{settings.api_port}/api/alerts"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=alert_data, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info(f"✅ Alert sent to API: {alert_data['state']} (score={alert_data['drowsiness_score']:.2f})")
                    else:
                        logger.warning(f"⚠️  Alert API returned {response.status}: {await response.text()}")
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Alert API timeout - detector continuing (offline?)")
        except Exception as e:
            logger.warning(f"⚠️  Error sending alert: {e} (detector continuing)")

    
    async def shutdown(self):
        """
        Gracefully shutdown the detector.
        """
        logger.info("Shutting down detector...")
        self.is_running = False
        
        if self.cap:
            self.cap.release()
            logger.info("Camera released")
        
        cv2.destroyAllWindows()
        
        # Print statistics
        uptime = time.time() - self.start_time
        avg_latency = np.mean(self.detection_latencies) if self.detection_latencies else 0
        
        logger.info("=" * 80)
        logger.info("Detector Statistics")
        logger.info("=" * 80)
        logger.info(f"Total frames processed: {self.frame_count}")
        logger.info(f"Uptime: {uptime / 60:.1f} minutes")
        logger.info(f"Avg detection latency: {avg_latency:.1f} ms")
        logger.info(f"Final state: {self.current_state.value}")
        logger.info("=" * 80)


async def main():
    """
    Main entry point.
    """
    import sys
    
    # Get config from environment
    vehicle_id = settings.vehicle_id
    driver_id = settings.driver_id
    detector_id = settings.detector_id
    
    # Check command line args for test mode
    test_mode = "--test" in sys.argv or os.getenv("TEST_MODE", "false").lower() == "true"
    
    logger.info(f"Configuration:")
    logger.info(f"  Vehicle ID: {vehicle_id}")
    logger.info(f"  Driver ID: {driver_id}")
    logger.info(f"  Detector ID: {detector_id}")
    logger.info(f"  API Endpoint: {settings.api_endpoint}")
    logger.info(f"  Test Mode: {'ENABLED 🧪' if test_mode else 'Disabled'}")
    
    # Create detector
    detector = DrownessDetectorService(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        detector_id=detector_id,
        test_mode=test_mode
    )
    
    # If test mode, fetch user's actual location for landmarks
    if test_mode:
        logger.info("🌍 Fetching your location for test mode landmarks...")
        detector.test_location_base = await detector._fetch_user_location_from_ip()
    
    try:
        # Run indefinitely (remove duration_seconds or set to None)
        await detector.run(duration_seconds=None)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
