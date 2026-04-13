import '@/index.css';
import { useState, useEffect } from 'react';
import { Header, Footer, FleetMap, AlertsList, KPIDashboard, TrendChart, CalibrationModal } from './components';
import { alertsAPI, analyticsAPI, calibrationAPI } from './api/client';
import type { DrowsinessAlert, FleetKPI, VehicleTrend, CalibrationSettings } from './types/index';
import { RefreshCw, Settings } from 'lucide-react';

export function App() {
  const [alerts, setAlerts] = useState<DrowsinessAlert[]>([]);
  const [previousAlerts, setPreviousAlerts] = useState<DrowsinessAlert[]>([]);
  const [kpis, setKpis] = useState<FleetKPI | null>(null);
  const [trends, setTrends] = useState<VehicleTrend[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [calibration, setCalibration] = useState<Partial<CalibrationSettings> | null>(null);
  const [showCalibrationModal, setShowCalibrationModal] = useState(false);
  const [calibrationLoading, setCalibrationLoading] = useState(false);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);

  // Play alert sound using system notification instead of Web Audio API
  const playAlertSound = (state: string) => {
    try {
      // Request notification permission if needed
      if (Notification.permission === 'granted' || Notification.permission === 'default') {
        const title = state === 'asleep' ? '🚨 ALERT: Driver Asleep!' : '⚠️ WARNING: Driver Drowsy';
        const options: NotificationOptions = {
          icon: state === 'asleep' ? '🔴' : '🟡',
          tag: 'drowsiness-alert',
          requireInteraction: false,
          badge: `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="${state === 'asleep' ? '%23FF0000' : '%23FFA500'}"/></svg>`
        };
        
        // Request permission first if needed
        if (Notification.permission === 'default') {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              new Notification(title, options);
            }
          });
        } else if (Notification.permission === 'granted') {
          new Notification(title, options);
        }
      }
    } catch (error) {
      console.warn('Could not show notification:', error);
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const data = await alertsAPI.getAlerts({ limit: 50 });
      const newAlerts = data || [];
      
      // Detect new critical alerts
      const newCriticalAlerts = newAlerts.filter(alert => {
        const wasInPrevious = previousAlerts.some(pa => pa.alert_id === alert.alert_id);
        return !wasInPrevious && (alert.state === 'drowsy' || alert.state === 'asleep');
      });
      
      // Play sound for each new critical alert
      newCriticalAlerts.forEach(alert => {
        playAlertSound(alert.state);
      });
      
      setPreviousAlerts(newAlerts);
      setAlerts(newAlerts);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  // Fetch KPIs
  const fetchKPIs = async () => {
    try {
      const data = await analyticsAPI.getFleetKPIs();
      setKpis(data);
    } catch (error) {
      console.error('Failed to fetch KPIs:', error);
    }
  };

  // Fetch trends for selected vehicle
  const fetchTrends = async (vehicleId: string) => {
    try {
      const data = await analyticsAPI.getVehicleTrends(vehicleId);
      // Handle empty or null response
      setTrends(Array.isArray(data) && data.length > 0 ? data : []);
    } catch (error) {
      console.error('Failed to fetch trends:', error);
      // Use empty array - trends are optional
      setTrends([]);
    }
  };

  // Fetch calibration for selected driver
  const fetchCalibration = async (driverId: string) => {
    try {
      const data = await calibrationAPI.getCalibration(driverId);
      // Use provided data or defaults if null
      setCalibration(
        data || {
          ear_awake_threshold: 0.3,
          ear_drowsy_threshold: 0.2,
          head_pitch_threshold: 25.0,
          head_roll_threshold: 15.0,
          alert_hysteresis_frames: 5,
        }
      );
    } catch (error) {
      console.error('Failed to fetch calibration:', error);
      // Use defaults if API not ready
      setCalibration({
        ear_awake_threshold: 0.3,
        ear_drowsy_threshold: 0.2,
        head_pitch_threshold: 25.0,
        head_roll_threshold: 15.0,
        alert_hysteresis_frames: 5,
      });
    }
  };

  // Geolocation with rate limiting (every 5 seconds)
  const fetchUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
          console.log(`📍 User location: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
        },
        (error) => {
          console.warn('Could not fetch user location:', error.message);
          // Fallback to NYC if location unavailable
          setUserLocation([40.7128, -74.0060]);
        },
        { timeout: 10000, enableHighAccuracy: false }
      );
    } else {
      console.warn('Geolocation not supported');
      setUserLocation([40.7128, -74.0060]);
    }
  };

  // Initial load
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      // Fetch user location immediately
      fetchUserLocation();
      await Promise.all([fetchAlerts(), fetchKPIs()]);
      setLoading(false);
    };
    load();
  }, []);

  // Poll for updates every 5 seconds (alerts, KPIs) and location every 5 seconds (rate limited)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAlerts();
      fetchKPIs();
      fetchUserLocation(); // Rate limited: every 5 seconds
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Load trends when vehicle is selected
  useEffect(() => {
    if (selectedVehicleId) {
      fetchTrends(selectedVehicleId);
      const driverId = selectedVehicleId.replace('vehicle_', 'driver_');
      fetchCalibration(driverId);
    }
  }, [selectedVehicleId]);

  const handleCalibrationSave = async (settings: Partial<CalibrationSettings>) => {
    if (!selectedVehicleId) return;
    
    setCalibrationLoading(true);
    try {
      const driverId = selectedVehicleId.replace('vehicle_', 'driver_');
      await calibrationAPI.updateCalibration(driverId, settings);
      setCalibration(settings);
      setShowCalibrationModal(false);
      alert('✅ Calibration saved successfully');
    } catch (error) {
      console.error('Failed to save calibration:', error);
      alert('❌ Failed to save calibration');
    } finally {
      setCalibrationLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header />
      
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8 space-y-6">
        {/* Control Bar */}
        <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div>
            <h2 className="text-xl font-bold">Fleet Dashboard</h2>
            <p className="text-sm text-gray-600">Real-time drowsiness monitoring</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => {
                fetchAlerts();
                fetchKPIs();
              }}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            {selectedVehicleId && (
              <button
                onClick={() => setShowCalibrationModal(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span>Calibrate</span>
              </button>
            )}
          </div>
        </div>

        {/* KPIs */}
        <KPIDashboard kpis={kpis} loading={loading} />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden" style={{ height: '500px' }}>
              <FleetMap
                alerts={alerts}
                selectedVehicleId={selectedVehicleId}
                onSelectVehicle={setSelectedVehicleId}
                userLocation={userLocation}
              />
            </div>
          </div>

          {/* Alerts List */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
            <AlertsList alerts={alerts} onSelectVehicle={setSelectedVehicleId} />
          </div>
        </div>

        {/* Trends */}
        {selectedVehicleId && (
          <div>
            <h3 className="text-lg font-semibold mb-4">Vehicle Details</h3>
            <TrendChart data={trends} vehicleId={selectedVehicleId} />
          </div>
        )}

        {/* Calibration Info */}
        {selectedVehicleId && calibration && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Calibration Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-gray-600">EAR Awake</p>
                <p className="text-2xl font-bold">{calibration.ear_awake_threshold?.toFixed(2)}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-gray-600">EAR Drowsy</p>
                <p className="text-2xl font-bold">{calibration.ear_drowsy_threshold?.toFixed(2)}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-gray-600">Pitch Threshold</p>
                <p className="text-2xl font-bold">{calibration.head_pitch_threshold?.toFixed(1)}°</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Calibration Modal */}
      <CalibrationModal
        isOpen={showCalibrationModal}
        driverId={selectedVehicleId?.replace('vehicle_', 'driver_') || 'unknown'}
        settings={calibration}
        onSave={handleCalibrationSave}
        onClose={() => setShowCalibrationModal(false)}
        loading={calibrationLoading}
      />

      <Footer />
    </div>
  );
}

export default App;
