"""
Deep learning models for drowsiness detection.
Includes MediaPipe Face Mesh, head pose estimation, and fatigue detection.
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import urllib.request
import pickle


class MediaPipeFaceDetector:
    """
    MediaPipe-based face detection and landmark extraction.
    Detects 468 3D facial landmarks with high accuracy.
    
    NOTE: For now, this is a stub implementation due to mediapipe version incompatibility.
    The actual mediapipe integration will be added when compatible version is available.
    """
    
    def __init__(self):
        """Initialize MediaPipe Face Mesh."""
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.use_stub = False
        except (ImportError, AttributeError):
            print("WARNING: MediaPipe not properly initialized, using stub implementation")
            self.use_stub = True
            self.face_mesh = None
        
        # Eye landmark indices
        self.RIGHT_EYE_LANDMARKS = list(range(33, 133))  # Right eye
        self.LEFT_EYE_LANDMARKS = list(range(362, 382))  # Left eye
        
        # Face bounding box landmarks
        self.FACE_BOUNDS = [10, 234, 454, 200, 430, 424, 176, 226]
    
    def detect(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Detect face and extract landmarks.
        
        Args:
            frame: Input frame (BGR from OpenCV)
        
        Returns:
            Tuple of (face_landmarks array, metadata dict)
            Returns (None, None) if no face detected
        """
        if self.use_stub:
            # Return stub data for testing - random landmarks
            h, w, c = frame.shape
            # Create 468 random landmarks (468 is MediaPipe's standard)
            landmarks_xy = np.random.rand(468, 3).astype(np.float32)
            landmarks_xy[:, 0] *= w
            landmarks_xy[:, 1] *= h
            landmarks_xy[:, 2] *= w
            
            metadata = {
                "num_landmarks": 468,
                "confidence": 0.9,
                "frame_shape": frame.shape,
                "stub": True
            }
            return landmarks_xy, metadata
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks or len(results.multi_face_landmarks) == 0:
                return None, None
            
            # Get first face
            landmarks = results.multi_face_landmarks[0].landmark
            h, w, c = frame.shape
            
            # Convert normalized coordinates to pixel coordinates
            landmarks_xy = np.array([
                [lm.x * w, lm.y * h, lm.z * w] for lm in landmarks
            ], dtype=np.float32)
            
            # Metadata
            metadata = {
                "num_landmarks": len(landmarks),
                "confidence": 0.9,
                "frame_shape": frame.shape,
            }
            
            return landmarks_xy, metadata
        except Exception as e:
            print(f"MediaPipe detection error: {e}")
            return None, None
    
    def get_eye_landmarks(self, landmarks: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract left and right eye landmarks from full face landmarks.
        
        Args:
            landmarks: 468x3 array of face landmarks
        
        Returns:
            Tuple of (left_eye_landmarks, right_eye_landmarks)
        """
        left_eye = landmarks[self.LEFT_EYE_LANDMARKS]
        right_eye = landmarks[self.RIGHT_EYE_LANDMARKS]
        return left_eye, right_eye


class EARCalculator:
    """
    Eye Aspect Ratio (EAR) calculation.
    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    """
    
    # Standard EAR point indices from 468 MediaPipe landmarks
    # Right eye (33-133, using 33=inner corner, 133=outer corner, 160=top, 145=bottom)
    RIGHT_EYE_INDICES = {
        "left": 33,    # Inner corner
        "right": 133,  # Outer corner
        "top": 160,    # Top eyelid
        "bottom": 145, # Bottom eyelid
    }
    
    # Left eye (362-263)
    LEFT_EYE_INDICES = {
        "left": 362,   # Inner corner
        "right": 263,  # Outer corner
        "top": 386,    # Top eyelid
        "bottom": 374, # Bottom eyelid
    }
    
    @staticmethod
    def distance(p1: np.ndarray, p2: np.ndarray) -> float:
        """Euclidean distance between two points."""
        return np.linalg.norm(p1 - p2)
    
    @classmethod
    def compute_eye_ear(cls, eye_landmarks: np.ndarray) -> float:
        """
        Compute EAR for a single eye using the 6-point formula.
        
        Args:
            eye_landmarks: (n, 3) array of eye landmarks ordered:
                           [left_corner, top1, top2, right_corner, bot2, bot1]
        
        Returns:
            EAR value (0.0 - 1.0)
        """
        if len(eye_landmarks) < 6:
            return 0.0
        
        # Vertical distances (two pairs: top-to-bottom)
        p2, p6 = eye_landmarks[1][:2], eye_landmarks[5][:2]
        p3, p5 = eye_landmarks[2][:2], eye_landmarks[4][:2]
        vertical = cls.distance(p2, p6) + cls.distance(p3, p5)
        
        # Horizontal distance (left corner to right corner)
        p1, p4 = eye_landmarks[0][:2], eye_landmarks[3][:2]
        horizontal = cls.distance(p1, p4)
        
        # Standard EAR formula: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        ear = vertical / (2.0 * horizontal) if horizontal > 0 else 0.0
        return float(np.clip(ear, 0.0, 1.0))
    
    @classmethod
    def compute_both_eyes_ear(
        cls,
        landmarks: np.ndarray,
        right_eye_indices: Dict[str, int],
        left_eye_indices: Dict[str, int],
    ) -> Tuple[float, float, float]:
        """
        Compute EAR for both eyes.
        
        Args:
            landmarks: (468, 3) array of face landmarks
            right_eye_indices: Dict with "top", "bottom", "left", "right" keys
            left_eye_indices: Dict with "top", "bottom", "left", "right" keys
        
        Returns:
            Tuple of (left_ear, right_ear, average_ear)
        """
        # Right eye
        r_top = landmarks[right_eye_indices["top"]][:2]
        r_bottom = landmarks[right_eye_indices["bottom"]][:2]
        r_left = landmarks[right_eye_indices["left"]][:2]
        r_right = landmarks[right_eye_indices["right"]][:2]
        
        right_vertical = cls.distance(r_top, r_bottom)
        right_horizontal = cls.distance(r_left, r_right)
        right_ear = right_vertical / (2.0 * right_horizontal) if right_horizontal > 0 else 0.0
        
        # Left eye
        l_top = landmarks[left_eye_indices["top"]][:2]
        l_bottom = landmarks[left_eye_indices["bottom"]][:2]
        l_left = landmarks[left_eye_indices["left"]][:2]
        l_right = landmarks[left_eye_indices["right"]][:2]
        
        left_vertical = cls.distance(l_top, l_bottom)
        left_horizontal = cls.distance(l_left, l_right)
        left_ear = left_vertical / (2.0 * left_horizontal) if left_horizontal > 0 else 0.0
        
        avg_ear = (left_ear + right_ear) / 2.0
        
        return float(np.clip(left_ear, 0.0, 1.0)), \
               float(np.clip(right_ear, 0.0, 1.0)), \
               float(np.clip(avg_ear, 0.0, 1.0))


class FatigueDetector:
    """
    Fatigue/drowsiness detection using pre-trained MobileNetV2.
    This is a placeholder implementation; in production would use
    a fine-tuned model trained on drowsy/alert eye images.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize fatigue detector.
        
        Args:
            model_path: Path to pre-trained model (optional)
        """
        self.model_path = model_path
        self.model = None
        
        # For now, using a simple heuristic based on eye closure
        # In production, would load a neural network model
    
    def detect(self, eye_roi: np.ndarray) -> float:
        """
        Detect fatigue from eye region.
        
        Args:
            eye_roi: Eye region image (224x224 or similar)
        
        Returns:
            Fatigue score (0.0 - 1.0)
        """
        if eye_roi is None or eye_roi.size == 0:
            return 0.0
        
        # Placeholder: Use simple Laplacian variance (blur/focus)
        # Blurry eye = likely fatigue
        # In production: return self.model.predict(eye_roi)
        
        gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1 range
        # Higher variance = sharper image = more alert
        fatigue_score = 1.0 - min(laplacian_var / 500.0, 1.0)
        
        return float(np.clip(fatigue_score, 0.0, 1.0))


class ModelRegistry:
    """
    Registry for managing model versions and downloads.
    """
    
    MODELS = {
        "mediapipe_face_mesh": {
            "version": "0.8.9",
            "size_mb": 5,
            "description": "MediaPipe Face Mesh 468-point detector"
        },
        "mobilenet_v2_fatigue": {
            "version": "1.0.0",
            "size_mb": 4,
            "url": "https://example.com/models/mobilenet_v2_fatigue.h5",
            "description": "MobileNetV2 fine-tuned on fatigue detection"
        }
    }
    
    @staticmethod
    def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific model."""
        return ModelRegistry.MODELS.get(model_name)
    
    @staticmethod
    def list_models() -> Dict[str, Dict[str, Any]]:
        """List all available models."""
        return ModelRegistry.MODELS.copy()
