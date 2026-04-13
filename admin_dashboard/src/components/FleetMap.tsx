import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import type { DrowsinessAlert } from '../types/index';

interface FleetMapProps {
  alerts: DrowsinessAlert[];
  selectedVehicleId?: string;
  onSelectVehicle?: (vehicleId: string) => void;
  userLocation?: [number, number] | null;
}

/**
 * Inner component — must live inside <MapContainer> to access the map instance.
 * react-leaflet's `center` prop on MapContainer is mount-only and never updates.
 * This component calls map.flyTo() whenever the target center changes.
 */
const MapViewController: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, map.getZoom(), { animate: true, duration: 1.0 });
  }, [center[0], center[1]]);
  return null;
};

export const FleetMap: React.FC<FleetMapProps> = ({ alerts, selectedVehicleId, onSelectVehicle, userLocation }) => {
  // Use user location as default, fallback to NYC
  const defaultCenter: [number, number] = userLocation || [40.7128, -74.0060];
  const [mapCenter, setMapCenter] = useState<[number, number]>(defaultCenter);

  // Group alerts by vehicle to get latest position
  const vehiclePositions = new Map<string, DrowsinessAlert>();
  alerts.forEach(alert => {
    if (alert.latitude && alert.longitude) {
      // Keep only the latest alert per vehicle
      const existing = vehiclePositions.get(alert.vehicle_id);
      if (!existing || new Date(alert.detected_at) > new Date(existing.detected_at)) {
        vehiclePositions.set(alert.vehicle_id, alert);
      }
    }
  });

  // Update map center based on nearest vehicle or selected vehicle
  useEffect(() => {
    if (selectedVehicleId && vehiclePositions.has(selectedVehicleId)) {
      // Center on selected vehicle
      const selected = vehiclePositions.get(selectedVehicleId);
      if (selected?.latitude && selected?.longitude) {
        setMapCenter([selected.latitude, selected.longitude]);
      }
    } else if (vehiclePositions.size > 0) {
      // Center on nearest/first vehicle
      const firstVehicle = Array.from(vehiclePositions.values())[0];
      if (firstVehicle?.latitude && firstVehicle?.longitude) {
        setMapCenter([firstVehicle.latitude, firstVehicle.longitude]);
      }
    } else if (userLocation) {
      // No vehicles, use user's actual GPS location
      setMapCenter(userLocation);
    }
  }, [alerts, selectedVehicleId, userLocation]);

  // Create custom icons based on status
  const getMarkerIcon = (state: string, isSelected: boolean) => {
    const colors: Record<string, string> = {
      active: isSelected ? '#3b82f6' : '#10b981',
      drowsy: isSelected ? '#f59e0b' : '#f97316',
      asleep: isSelected ? '#ef4444' : '#dc2626',
    };
    
    return new Icon({
      iconUrl: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23${colors[state]?.slice(1) || '10b981'}'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z'/%3E%3C/svg%3E`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });
  };

  return (
    <div className="w-full h-full rounded-lg overflow-hidden border border-gray-200">
      <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
        {/* MapViewController must live inside MapContainer to access useMap() */}
        <MapViewController center={mapCenter} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {Array.from(vehiclePositions.entries()).map(([vehicleId, alert]) => (
          <React.Fragment key={vehicleId}>
            <Marker
              position={[alert.latitude || 40.7128, alert.longitude || -74.0060]}
              icon={getMarkerIcon(alert.state, vehicleId === selectedVehicleId)}
              eventHandlers={{
                click: () => onSelectVehicle?.(vehicleId),
              }}
            >
              <Popup>
                <div className="p-2 text-sm">
                  <div className="font-bold">{vehicleId}</div>
                  <div className="text-gray-600">{alert.address || 'Unknown location'}</div>
                  <div className={`mt-1 font-semibold ${
                    alert.state === 'active' ? 'text-green-600' :
                    alert.state === 'drowsy' ? 'text-orange-600' :
                    'text-red-600'
                  }`}>
                    {alert.state.toUpperCase()}
                  </div>
                  <div className="text-gray-600 text-xs mt-1">
                    Score: {(alert.drowsiness_score * 100).toFixed(1)}%
                  </div>
                </div>
              </Popup>
            </Marker>

            {/* Alert radius for drowsy/asleep vehicles */}
            {alert.state !== 'active' && (
              <Circle
                center={[alert.latitude || 40.7128, alert.longitude || -74.0060]}
                radius={500}
                color={alert.state === 'asleep' ? '#dc2626' : '#f97316'}
                fillOpacity={0.1}
              />
            )}
          </React.Fragment>
        ))}
      </MapContainer>
    </div>
  );
};
