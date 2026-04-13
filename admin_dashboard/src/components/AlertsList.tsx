import React from 'react';
import { AlertCircle, AlertTriangle, AlertOctagon, Zap } from 'lucide-react';
import type { DrowsinessAlert } from '../types/index';
import { formatDistanceToNow } from 'date-fns';

interface AlertsListProps {
  alerts: DrowsinessAlert[];
  onSelectVehicle?: (vehicleId: string) => void;
}

/**
 * Parse a timestamp string as UTC.
 * Python's datetime.isoformat() omits the 'Z' suffix, so JavaScript's
 * Date constructor interprets the string as LOCAL time instead of UTC.
 * Appending 'Z' forces correct UTC interpretation.
 */
const parseUTC = (ts: string): Date => {
  if (!ts) return new Date();
  const normalized = ts.endsWith('Z') || ts.includes('+') ? ts : ts + 'Z';
  return new Date(normalized);
};

export const AlertsList: React.FC<AlertsListProps> = ({ alerts, onSelectVehicle }) => {
  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'asleep':
        return <AlertOctagon className="w-5 h-5 text-red-600" />;
      case 'drowsy':
        return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-blue-600" />;
    }
  };

  const getStatusBgColor = (state: string) => {
    switch (state) {
      case 'asleep':
        return 'bg-red-50 border-l-4 border-red-600';
      case 'drowsy':
        return 'bg-orange-50 border-l-4 border-orange-600';
      default:
        return 'bg-blue-50 border-l-4 border-blue-600';
    }
  };

  const getStatusTextColor = (state: string) => {
    switch (state) {
      case 'asleep':
        return 'text-red-900';
      case 'drowsy':
        return 'text-orange-900';
      default:
        return 'text-blue-900';
    }
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center text-gray-500">
          <Zap className="w-5 h-5 mr-2" />
          No alerts
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="max-h-96 overflow-y-auto">
        {alerts.map((alert, index) => (
          <div
            key={`${alert.alert_id}-${index}`}
            className={`p-4 border-b border-gray-200 last:border-b-0 cursor-pointer hover:bg-gray-50 transition-colors ${getStatusBgColor(alert.state)}`}
            onClick={() => onSelectVehicle?.(alert.vehicle_id)}
          >
            <div className="flex items-start space-x-3">
              <div className="mt-1">{getStatusIcon(alert.state)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h4 className={`font-semibold ${getStatusTextColor(alert.state)}`}>
                    {alert.vehicle_id}
                  </h4>
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    alert.state === 'asleep' ? 'bg-red-200 text-red-800' :
                    alert.state === 'drowsy' ? 'bg-orange-200 text-orange-800' :
                    'bg-blue-200 text-blue-800'
                  }`}>
                    {alert.state.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Driver: {alert.driver_id}
                </p>
                <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                  <div className="bg-white bg-opacity-50 p-2 rounded">
                    <div className="font-semibold">Score</div>
                    <div className="text-sm">{(alert.drowsiness_score * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-white bg-opacity-50 p-2 rounded">
                    <div className="font-semibold">EAR</div>
                    <div className="text-sm">{alert.ear_value.toFixed(3)}</div>
                  </div>
                  <div className="bg-white bg-opacity-50 p-2 rounded">
                    <div className="font-semibold">Fatigue</div>
                    <div className="text-sm">{(alert.fatigue_score * 100).toFixed(1)}%</div>
                  </div>
                </div>
                {alert.address && (
                  <p className="text-xs text-gray-500 mt-2 truncate">
                    📍 {alert.address}
                  </p>
                )}
                <p className="text-xs text-gray-400 mt-1">
                  {formatDistanceToNow(parseUTC(alert.detected_at || alert.timestamp || ''), { addSuffix: true })}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
