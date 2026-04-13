export interface Vehicle {
  vehicle_id: string;
  driver_id: string;
  driver_name: string;
  latitude: number;
  longitude: number;
  status: 'active' | 'drowsy' | 'asleep' | 'offline';
  last_alert?: string;
  last_heartbeat?: string;
}

export interface DrowsinessAlert {
  alert_id: string;
  vehicle_id: string;
  driver_id: string;
  state: 'active' | 'drowsy' | 'asleep';
  ear_value: number;
  head_pitch?: number;
  head_yaw?: number;
  fatigue_score: number;
  drowsiness_score: number;
  latitude?: number;
  longitude?: number;
  address?: string;
  detected_at: string;
  severity?: string;
  timestamp?: string;
}

export interface FleetKPI {
  alerts_today: number;
  drowsy_alerts: number;
  asleep_alerts: number;
  active_detectors: number;
  timestamp: string;
}

export interface VehicleTrend {
  timestamp: string;
  drowsiness_score: number;
  state: 'active' | 'drowsy' | 'asleep';
  ear_value: number;
}

export interface CalibrationSettings {
  driver_id: string;
  ear_awake_threshold: number;
  ear_drowsy_threshold: number;
  head_pitch_threshold: number;
  head_roll_threshold: number;
  alert_hysteresis_frames: number;
}
