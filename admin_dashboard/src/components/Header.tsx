import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center space-x-3">
          <div className="bg-white rounded-lg p-2">
            <div className="w-6 h-6 bg-gradient-to-br from-blue-600 to-blue-800 rounded-md"></div>
          </div>
          <div>
            <h1 className="text-2xl font-bold">Driver Drowsiness Detector</h1>
            <p className="text-blue-100 text-sm">Fleet Management Dashboard</p>
          </div>
        </div>
      </div>
    </header>
  );
};
