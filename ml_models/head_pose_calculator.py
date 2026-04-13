"""
Head pose estimation using Perspective-n-Point (PnP).
Computes 3D head orientation (pitch, yaw, roll) from facial landmarks.
"""
import cv2
import numpy as np
from typing import Tuple, Optional


class HeadPoseCalculator:
    """
    Estimate 3D head orientation (pitch, yaw, roll) using PnP.
    Uses facial landmarks to solve the pose estimation problem.
    """
    
    # 3D model points of human face (from standard face model)
    # These are generic reference points representing face geometry
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),           # Nose tip
        (0.0, -330.0, -65.0),      # Chin
        (-225.0, 170.0, -135.0),   # Left eye left corner
        (225.0, 170.0, -135.0),    # Right eye right corner
        (-150.0, -150.0, -125.0),  # Left mouth corner
        (150.0, -150.0, -125.0)    # Right mouth corner
    ], dtype="double")
    
    # MediaPipe landmark indices mapping to face model points
    # (nose, chin, left_eye, right_eye, left_mouth, right_mouth)
    LANDMARK_INDICES = [1, 199, 33, 263, 61, 291]
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        """
        Initialize head pose calculator.
        
        Args:
            frame_width: Video frame width
            frame_height: Video frame height
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Camera intrinsic matrix (assumes built-in laptop camera)
        # These are typical values; adjust based on actual camera calibration
        focal_length = frame_width
        center = (frame_width / 2, frame_height / 2)
        
        self.camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        
        # Distortion coefficients (no distortion assumed)
        self.dist_coeffs = np.zeros((4, 1))
    
    def estimate_pose(
        self,
        landmarks: np.ndarray
    ) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray], Optional[Tuple[float, float, float]]]:
        """
        Estimate head pose from facial landmarks.
        
        Args:
            landmarks: (468, 3) array of MediaPipe face landmarks
        
        Returns:
            Tuple of (success, rotation_vector, translation_vector, (pitch, yaw, roll))
            Angles in degrees. Returns (False, None, None, None) if pose estimation fails.
        """
        try:
            if landmarks is None or len(landmarks) < max(self.LANDMARK_INDICES):
                return False, None, None, None
            
            # Extract specific landmarks
            image_points = landmarks[self.LANDMARK_INDICES][:, :2]  # Use only x, y
            
            # Validate image points
            if image_points.shape != (6, 2) or np.any(np.isnan(image_points)) or np.any(np.isinf(image_points)):
                return False, None, None, None
            
            # Ensure points are float32
            image_points = image_points.astype(np.float32)
            
            # Solve PnP problem
            success, rotation_vec, translation_vec = cv2.solvePnP(
                self.MODEL_POINTS,
                image_points,
                self.camera_matrix,
                self.dist_coeffs,
                useExtrinsicGuess=False,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return False, None, None, None
            
            # Convert rotation vector to rotation matrix, then to Euler angles
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            
            # Extract pitch, yaw, roll from rotation matrix
            pitch, yaw, roll = self._rotation_matrix_to_euler(rotation_mat)
            
            return True, rotation_vec, translation_vec, (pitch, yaw, roll)
        
        except Exception as e:
            # Gracefully handle any errors (e.g., with stub data)
            return False, None, None, None
    
    @staticmethod
    def _rotation_matrix_to_euler(rotation_mat: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert rotation matrix to Euler angles (pitch, yaw, roll).
        
        Args:
            rotation_mat: 3x3 rotation matrix
        
        Returns:
            Tuple of (pitch, yaw, roll) in degrees
        """
        # Extract Euler angles from rotation matrix
        # Assuming ZYX convention (roll-pitch-yaw)
        
        # Clamp to avoid numerical issues with arcsin
        sy = np.sqrt(rotation_mat[0, 0] ** 2 + rotation_mat[1, 0] ** 2)
        
        singular = sy < 1e-6
        
        if not singular:
            x = np.arctan2(rotation_mat[2, 1], rotation_mat[2, 2])
            y = np.arctan2(-rotation_mat[2, 0], sy)
            z = np.arctan2(rotation_mat[1, 0], rotation_mat[0, 0])
        else:
            x = np.arctan2(-rotation_mat[1, 2], rotation_mat[1, 1])
            y = np.arctan2(-rotation_mat[2, 0], sy)
            z = 0
        
        # Convert to degrees
        pitch = np.degrees(x)
        yaw = np.degrees(y)
        roll = np.degrees(z)
        
        return float(pitch), float(yaw), float(roll)
    
    def compute_head_pose_risk(
        self,
        pitch: float,
        yaw: float,
        roll: float,
        pitch_threshold: float = 25.0,
        yaw_threshold: float = 40.0,
        roll_threshold: float = 30.0
    ) -> float:
        """
        Compute drowsiness risk based on head pose.
        
        High risk if:
        - Pitch > threshold (forward nod/falling asleep)
        - Abs(yaw) > threshold (extreme rotation)
        - Abs(roll) > threshold (extreme tilt)
        
        Args:
            pitch: Head pitch angle in degrees
            yaw: Head yaw angle in degrees
            roll: Head roll angle in degrees
            pitch_threshold: Threshold for forward nod (degrees)
            yaw_threshold: Threshold for side rotation (degrees)
            roll_threshold: Threshold for tilt (degrees)
        
        Returns:
            Risk score (0.0 - 1.0)
        """
        risk = 0.0
        
        # Forward nod (pitch > threshold)
        if pitch > pitch_threshold:
            risk = max(risk, (pitch - pitch_threshold) / (90.0 - pitch_threshold))
        
        # Extreme yaw (looking too far left or right)
        if abs(yaw) > yaw_threshold:
            risk = max(risk, (abs(yaw) - yaw_threshold) / (90.0 - yaw_threshold))
        
        # Extreme roll (head tilt)
        if abs(roll) > roll_threshold:
            risk = max(risk, (abs(roll) - roll_threshold) / (90.0 - roll_threshold))
        
        return float(np.clip(risk, 0.0, 1.0))
    
    def draw_pose_on_frame(
        self,
        frame: np.ndarray,
        rotation_vec: np.ndarray,
        translation_vec: np.ndarray,
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> np.ndarray:
        """
        Draw 3D head pose axes on frame.
        
        Args:
            frame: Input frame
            rotation_vec: Rotation vector from PnP
            translation_vec: Translation vector from PnP
            color: Color of axes (BGR)
        
        Returns:
            Frame with drawn axes
        """
        # Camera matrix (reuse from __init__)
        focal_length = self.frame_width
        center = (self.frame_width / 2, self.frame_height / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        
        # Define 3D axis points
        axis_points = np.float32([
            [0, 0, 0],     # Origin
            [100, 0, 0],   # X-axis (red)
            [0, 100, 0],   # Y-axis (green)
            [0, 0, -100]   # Z-axis (blue)
        ])
        
        # Project 3D axis points onto 2D image
        img_points, _ = cv2.projectPoints(
            axis_points,
            rotation_vec,
            translation_vec,
            camera_matrix,
            np.zeros((4, 1))
        )
        
        img_points = img_points.astype(int)
        
        # Draw axes
        origin = tuple(img_points[0].ravel())
        x_end = tuple(img_points[1].ravel())
        y_end = tuple(img_points[2].ravel())
        z_end = tuple(img_points[3].ravel())
        
        # X-axis: Red
        frame = cv2.line(frame, origin, x_end, (0, 0, 255), 3)
        # Y-axis: Green
        frame = cv2.line(frame, origin, y_end, (0, 255, 0), 3)
        # Z-axis: Blue
        frame = cv2.line(frame, origin, z_end, (255, 0, 0), 3)
        
        return frame
