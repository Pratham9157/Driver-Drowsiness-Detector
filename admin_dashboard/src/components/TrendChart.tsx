import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar } from 'recharts';
import type { VehicleTrend } from '../types/index';

interface TrendChartProps {
  data: VehicleTrend[];
  vehicleId: string;
}

export const TrendChart: React.FC<TrendChartProps> = ({ data, vehicleId }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-80 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No data available for {vehicleId}</p>
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map(item => ({
    time: new Date(item.timestamp).toLocaleTimeString(),
    drowsiness_score: Math.round(item.drowsiness_score * 100),
    ear_value: Math.round(item.ear_value * 100),
    state: item.state,
  }));

  return (
    <div className="w-full bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold mb-4">Drowsiness Trends - {vehicleId}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip 
            contentStyle={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb' }}
            formatter={(value) => `${value}%`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="drowsiness_score"
            stroke="#ef4444"
            name="Drowsiness Score (%)"
            isAnimationActive={false}
          />
          <Bar
            dataKey="ear_value"
            fill="#3b82f6"
            name="Eye Aspect Ratio (%)"
            opacity={0.7}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
