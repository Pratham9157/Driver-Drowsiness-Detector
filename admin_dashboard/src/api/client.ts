import axios from 'axios';
import type { DrowsinessAlert, FleetKPI, VehicleTrend, CalibrationSettings } from '../types/index';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const alertsAPI = {
  getAlerts: async (filters?: {
    vehicle_id?: string;
    driver_id?: string;
    state?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => {
    const params = new URLSearchParams();
    if (filters?.vehicle_id) params.append('vehicle_id', filters.vehicle_id);
    if (filters?.driver_id) params.append('driver_id', filters.driver_id);
    if (filters?.state) params.append('state', filters.state);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await api.get(`/alerts?${params.toString()}`);
    return response.data.data as DrowsinessAlert[];
  },

  createAlert: async (alert: Omit<DrowsinessAlert, 'id'>) => {
    const response = await api.post('/alerts', alert);
    return response.data.data;
  },
};

export const analyticsAPI = {
  getFleetKPIs: async () => {
    try {
      const response = await api.get('/analytics/fleet-kpis');
      return response.data.data as FleetKPI;
    } catch (error) {
      console.error('Error fetching fleet KPIs:', error);
      // Return default KPIs
      return {
        alerts_today: 0,
        drowsy_alerts: 0,
        asleep_alerts: 0,
        active_detectors: 0,
        timestamp: new Date().toISOString(),
      } as FleetKPI;
    }
  },

  getVehicleTrends: async (vehicleId: string): Promise<VehicleTrend[]> => {
    try {
      const response = await api.get(`/analytics/vehicle/${vehicleId}/trends`);
      const data = response.data.data;
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error(`Error fetching trends for ${vehicleId}:`, error);
      return []; // Return empty array if API fails
    }
  },
};

export const calibrationAPI = {
  getCalibration: async (driverId: string) => {
    try {
      const response = await api.get(`/calibration/driver/${driverId}`);
      const data = response.data.data as CalibrationSettings;
      // Return data if valid, otherwise return defaults
      return (data && Object.keys(data).length > 0) ? data : null;
    } catch (error) {
      console.error(`Error fetching calibration for ${driverId}:`, error);
      return null; // Return null to trigger defaults in App.tsx
    }
  },

  updateCalibration: async (driverId: string, settings: Partial<CalibrationSettings>) => {
    try {
      const response = await api.put(`/calibration/driver/${driverId}`, settings);
      return response.data.data;
    } catch (error) {
      console.error(`Error updating calibration for ${driverId}:`, error);
      throw error;
    }
  },
};

export const detectorsAPI = {
  register: async (data: { detector_id: string; vehicle_id: string }) => {
    const response = await api.post('/detectors/register', data);
    return response.data.data;
  },

  heartbeat: async (detectorId: string, metrics: any) => {
    const response = await api.put(`/detectors/${detectorId}/heartbeat`, {
      detector_id: detectorId,
      status: 'running',
      metrics,
    });
    return response.data.data;
  },

  unregister: async (detectorId: string) => {
    const response = await api.delete(`/detectors/${detectorId}`);
    return response.data.data;
  },
};

export const sessionsAPI = {
  getSessions: async (filters?: { vehicle_id?: string; driver_id?: string; limit?: number }) => {
    const params = new URLSearchParams();
    if (filters?.vehicle_id) params.append('vehicle_id', filters.vehicle_id);
    if (filters?.driver_id) params.append('driver_id', filters.driver_id);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const response = await api.get(`/sessions?${params.toString()}`);
    return response.data.data;
  },
};

export default api;
