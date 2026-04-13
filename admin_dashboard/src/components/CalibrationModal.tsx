import React, { useState } from 'react';
import { Save, X } from 'lucide-react';
import type { CalibrationSettings } from '../types/index';

interface CalibrationModalProps {
  isOpen: boolean;
  driverId: string;
  settings: Partial<CalibrationSettings> | null;
  onSave: (settings: Partial<CalibrationSettings>) => Promise<void>;
  onClose: () => void;
  loading: boolean;
}

export const CalibrationModal: React.FC<CalibrationModalProps> = ({
  isOpen,
  driverId,
  settings,
  onSave,
  onClose,
  loading,
}) => {
  const [formData, setFormData] = useState<Partial<CalibrationSettings>>(
    settings || {
      ear_awake_threshold: 0.3,
      ear_drowsy_threshold: 0.2,
      head_pitch_threshold: 25.0,
      head_roll_threshold: 15.0,
      alert_hysteresis_frames: 5,
    }
  );

  React.useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md flex flex-col max-h-[90vh]">
        {/* Sticky header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b shrink-0">
          <h2 className="text-2xl font-bold">Calibrate Driver</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Driver ID:</strong> {driverId}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Awake EAR Threshold
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.ear_awake_threshold || 0.3}
              onChange={(e) =>
                setFormData({ ...formData, ear_awake_threshold: parseFloat(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Eye Aspect Ratio when awake (default: 0.3)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Drowsy EAR Threshold
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.ear_drowsy_threshold || 0.2}
              onChange={(e) =>
                setFormData({ ...formData, ear_drowsy_threshold: parseFloat(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Eye Aspect Ratio when drowsy (default: 0.2)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Head Pitch Threshold (degrees)
            </label>
            <input
              type="number"
              step="0.5"
              value={formData.head_pitch_threshold || 25.0}
              onChange={(e) =>
                setFormData({ ...formData, head_pitch_threshold: parseFloat(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Maximum head pitch angle (default: 25°)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Head Roll Threshold (degrees)
            </label>
            <input
              type="number"
              step="0.5"
              value={formData.head_roll_threshold || 15.0}
              onChange={(e) =>
                setFormData({ ...formData, head_roll_threshold: parseFloat(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Maximum head roll angle (default: 15°)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alert Hysteresis (frames)
            </label>
            <input
              type="number"
              min="1"
              value={formData.alert_hysteresis_frames || 5}
              onChange={(e) =>
                setFormData({ ...formData, alert_hysteresis_frames: parseInt(e.target.value) })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">Consecutive frames before alert fires (default: 5)</p>
          </div>
        </div>

        {/* Sticky footer */}
        <div className="flex space-x-3 px-6 py-4 border-t shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 disabled:opacity-50"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center space-x-2 disabled:opacity-50"
            disabled={loading}
          >
            <Save className="w-4 h-4" />
            <span>{loading ? 'Saving...' : 'Save'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
