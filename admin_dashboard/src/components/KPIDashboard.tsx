import React from 'react';
import { TrendingUp, AlertCircle, AlertTriangle, AlertOctagon } from 'lucide-react';
import type { FleetKPI } from '../types/index';

interface KPIDashboardProps {
  kpis: FleetKPI | null;
  loading: boolean;
}

export const KPIDashboard: React.FC<KPIDashboardProps> = ({ kpis, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-gray-100 rounded-lg p-4 animate-pulse h-32"></div>
        ))}
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="text-gray-500 text-center py-8">
        Unable to load KPIs
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Alerts Today',
      value: kpis.alerts_today,
      icon: AlertCircle,
      color: 'bg-blue-50 border-blue-200',
      iconColor: 'text-blue-600',
    },
    {
      label: 'Drowsy Alerts',
      value: kpis.drowsy_alerts,
      icon: AlertTriangle,
      color: 'bg-orange-50 border-orange-200',
      iconColor: 'text-orange-600',
    },
    {
      label: 'Asleep Alerts',
      value: kpis.asleep_alerts,
      icon: AlertOctagon,
      color: 'bg-red-50 border-red-200',
      iconColor: 'text-red-600',
    },
    {
      label: 'Active Detectors',
      value: kpis.active_detectors,
      icon: TrendingUp,
      color: 'bg-green-50 border-green-200',
      iconColor: 'text-green-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div
            key={index}
            className={`rounded-lg border-2 p-6 transition-all hover:shadow-lg ${card.color}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{card.label}</p>
                <p className="text-3xl font-bold mt-2">{card.value}</p>
              </div>
              <Icon className={`w-8 h-8 ${card.iconColor} opacity-80`} />
            </div>
          </div>
        );
      })}
    </div>
  );
};
