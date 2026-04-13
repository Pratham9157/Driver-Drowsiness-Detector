import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <h3 className="font-semibold mb-2">About</h3>
            <p>Real-time drowsiness detection for fleet management</p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Technology</h3>
            <p>MediaPipe • FastAPI • MongoDB • React</p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Status</h3>
            <p>API: http://localhost:8000</p>
          </div>
        </div>
        <div className="mt-6 pt-6 border-t border-gray-700 text-xs">
          <p>&copy; 2026 Driver Drowsiness Detector. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
