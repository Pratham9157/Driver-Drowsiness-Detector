"""
Integrated drowsiness scoring combining EAR, head pose, and fatigue signals.
"""
import numpy as np
from typing import Tuple, Dict, Optional
from collections import deque


class DrowsinessScorer:
    """
    Compute integrated drowsiness score from multiple signals.
    Score = 0.6 * EAR + 0.2 * head_pose_risk + 0.2 * fatigue_score
    """
    
    # Default weights for combining signals
    DEFAULT_WEIGHTS = {
        "ear": 0.6,           # Eye Aspect Ratio (60%)
        "head_pose": 0.2,     # Head pose risk (20%)
        "fatigue": 0.2        # Fatigue score (20%)
    }
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        smoothing_window: int = 5
    ):
        """
        Initialize drowsiness scorer.
        
        Args:
            weights: Custom weights for different signals
            smoothing_window: Moving average window size
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.smoothing_window = smoothing_window
        self.score_history = deque(maxlen=smoothing_window)
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0; got {total_weight}")
    
    def compute_score(
        self,
        ear: float,
        head_pitch: float = 0.0,
        head_yaw: float = 0.0,
        head_roll: float = 0.0,
        fatigue_score: float = 0.0,
        pitch_threshold: float = 25.0,
        yaw_threshold: float = 40.0,
        roll_threshold: float = 30.0
    ) -> float:
        """
        Compute integrated drowsiness score.
        
        Args:
            ear: Eye Aspect Ratio (0.0 - 1.0, where lower = more drowsy)
            head_pitch: Head pitch angle (degrees)
            head_yaw: Head yaw angle (degrees)
            head_roll: Head roll angle (degrees)
            fatigue_score: Fatigue signal (0.0 - 1.0, where higher = more fatigue)
            pitch_threshold: Pitch threshold for drowsiness (degrees)
            yaw_threshold: Yaw threshold for drowsiness (degrees)
            roll_threshold: Roll threshold for drowsiness (degrees)
        
        Returns:
            Integrated drowsiness score (0.0 - 1.0)
        """
        # Normalize EAR to drowsiness scale (inverse — lower EAR = more drowsy).
        # Map EAR from [EAR_OPEN=0.32 → 0.0 drowsy] to [EAR_CLOSED=0.12 → 1.0 drowsy].
        # Using a closed floor of 0.12 prevents fully-closed eyes from being
        # treated identically to slightly-closed eyes.
        EAR_OPEN   = 0.32   # typical wide-awake EAR
        EAR_CLOSED = 0.12   # typical eye-closed EAR
        ear_range  = EAR_OPEN - EAR_CLOSED          # 0.20
        ear_drowsiness = 1.0 - np.clip((ear - EAR_CLOSED) / ear_range, 0.0, 1.0)
        
        # Head pose risk (0.0 = normal posture, 1.0 = extreme pose)
        head_pose_risk = self._compute_head_pose_risk(
            head_pitch, head_yaw, head_roll,
            pitch_threshold, yaw_threshold, roll_threshold
        )
        
        # Fatigue score (already normalized 0-1)
        fatigue_normalized = np.clip(fatigue_score, 0.0, 1.0)
        
        # Weighted combination
        drowsiness_score = (
            self.weights["ear"] * ear_drowsiness +
            self.weights["head_pose"] * head_pose_risk +
            self.weights["fatigue"] * fatigue_normalized
        )
        
        drowsiness_score = float(np.clip(drowsiness_score, 0.0, 1.0))
        
        return drowsiness_score
    
    def compute_smoothed_score(
        self,
        ear: float,
        head_pitch: float = 0.0,
        head_yaw: float = 0.0,
        head_roll: float = 0.0,
        fatigue_score: float = 0.0,
        pitch_threshold: float = 25.0,
        yaw_threshold: float = 40.0,
        roll_threshold: float = 30.0
    ) -> Tuple[float, float]:
        """
        Compute drowsiness score with moving average smoothing.
        
        Args:
            Same as compute_score()
        
        Returns:
            Tuple of (instantaneous_score, smoothed_score)
        """
        # Compute instantaneous score
        instant_score = self.compute_score(
            ear, head_pitch, head_yaw, head_roll, fatigue_score,
            pitch_threshold, yaw_threshold, roll_threshold
        )
        
        # Add to history
        self.score_history.append(instant_score)
        
        # Compute smoothed score (moving average)
        smoothed_score = float(np.mean(list(self.score_history)))
        
        return float(instant_score), float(smoothed_score)
    
    @staticmethod
    def _compute_head_pose_risk(
        head_pitch: float,
        head_yaw: float,
        head_roll: float,
        pitch_threshold: float,
        yaw_threshold: float,
        roll_threshold: float
    ) -> float:
        """
        Compute drowsiness risk from head pose.
        
        High risk if:
        - Pitch > threshold (forward nod, eyes closing)
        - Abs(yaw) > threshold (extreme side turn, disengagement)
        - Abs(roll) > threshold (head tilt, fatigue posture)
        
        Args:
            head_pitch, head_yaw, head_roll: Rotation angles (degrees)
            *_threshold: Thresholds in degrees
        
        Returns:
            Risk score (0.0 - 1.0)
        """
        risk = 0.0
        
        # Forward nod (pitch > threshold) - most important indicator
        if head_pitch > pitch_threshold:
            risk = max(risk, (head_pitch - pitch_threshold) / (90.0 - pitch_threshold))
        
        # Extreme yaw (looking too far left or right)
        if abs(head_yaw) > yaw_threshold:
            risk = max(risk, (abs(head_yaw) - yaw_threshold) / (90.0 - yaw_threshold))
        
        # Extreme roll (head tilt)
        if abs(head_roll) > roll_threshold:
            risk = max(risk, (abs(head_roll) - roll_threshold) / (90.0 - roll_threshold))
        
        return float(np.clip(risk, 0.0, 1.0))
    
    def classify_state(
        self,
        drowsiness_score: float,
        awake_threshold: float = 0.35,
        drowsy_threshold: float = 0.62
    ) -> str:
        """
        Classify drowsiness state based on combined score.
        
        Args:
            drowsiness_score: Score from compute_score()
            awake_threshold:  Score below this            → "active"  (default 0.35)
            drowsy_threshold: Score at or above this      → "asleep"  (default 0.62)
                              Score between the two       → "drowsy"
        
        Returns:
            State string: "active", "drowsy", or "asleep"
        """
        if drowsiness_score < awake_threshold:
            return "active"
        elif drowsiness_score >= drowsy_threshold:
            return "asleep"
        else:
            return "drowsy"
    
    def get_diagnosis(
        self,
        ear: float,
        head_pitch: float,
        head_yaw: float,
        head_roll: float,
        fatigue_score: float,
        drowsiness_score: float
    ) -> Dict[str, any]:
        """
        Get detailed diagnosis of drowsiness with signal breakdown.
        
        Args:
            All signal values
        
        Returns:
            Dictionary with signal contributions and recommendations
        """
        # Compute EAR contribution (must match compute_score's normalization)
        EAR_OPEN, EAR_CLOSED = 0.32, 0.12
        ear_drowsiness = 1.0 - np.clip((ear - EAR_CLOSED) / (EAR_OPEN - EAR_CLOSED), 0.0, 1.0)
        ear_contribution = self.weights["ear"] * ear_drowsiness
        
        # Compute head pose contribution
        head_pose_risk = self._compute_head_pose_risk(
            head_pitch, head_yaw, head_roll, 25.0, 40.0, 30.0
        )
        head_pose_contribution = self.weights["head_pose"] * head_pose_risk
        
        # Compute fatigue contribution
        fatigue_normalized = np.clip(fatigue_score, 0.0, 1.0)
        fatigue_contribution = self.weights["fatigue"] * fatigue_normalized
        
        # Determine dominant signal
        contributions = {
            "ear": ear_contribution,
            "head_pose": head_pose_contribution,
            "fatigue": fatigue_contribution
        }
        dominant_signal = max(contributions, key=contributions.get)
        
        # Generate recommendation
        recommendation = self._get_recommendation(
            dominant_signal, drowsiness_score,
            ear_drowsiness, head_pose_risk, fatigue_normalized
        )
        
        return {
            "overall_score": drowsiness_score,
            "contributions": {
                "ear": float(ear_contribution),
                "head_pose": float(head_pose_contribution),
                "fatigue": float(fatigue_contribution)
            },
            "dominant_signal": dominant_signal,
            "signal_values": {
                "ear": float(ear),
                "head_pitch": float(head_pitch),
                "head_yaw": float(head_yaw),
                "head_roll": float(head_roll),
                "fatigue": float(fatigue_score)
            },
            "recommendation": recommendation
        }
    
    @staticmethod
    def _get_recommendation(
        dominant_signal: str,
        drowsiness_score: float,
        ear_drowsiness: float,
        head_pose_risk: float,
        fatigue: float
    ) -> str:
        """
        Get driving recommendation based on signals.
        
        Args:
            dominant_signal: Which signal is driving drowsiness
            drowsiness_score: Overall score
            Other signal values for context
        
        Returns:
            Human-readable recommendation string
        """
        if drowsiness_score < 0.3:
            return "✅ Alert and ready to drive"
        elif drowsiness_score < 0.7:
            if dominant_signal == "ear":
                return "⚠️ Eyes getting heavy. Try opening eyes wide, look around."
            elif dominant_signal == "head_pose":
                return "⚠️ Head nodding forward. Adjust posture, keep eyes forward."
            else:
                return "⚠️ Feeling fatigue. Consider a 15-minute break ahead."
        else:
            if dominant_signal == "ear":
                return "🛑 CRITICAL: Eyes closing! Pull over safely IMMEDIATELY."
            elif dominant_signal == "head_pose":
                return "🛑 CRITICAL: Head has dropped significantly! Pull over safely IMMEDIATELY."
            else:
                return "🛑 CRITICAL: Severe fatigue detected! Pull over safely IMMEDIATELY."
