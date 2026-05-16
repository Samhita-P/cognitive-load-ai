import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { apiUrl } from '../config/env';
import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts';
import { AlertCircle, TrendingUp, Clock, Activity } from 'lucide-react';

export const HistoricalAnalytics: React.FC = () => {
  const { token } = useAuthStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [burnout, setBurnout] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [histRes, baseRes] = await Promise.all([
          fetch(apiUrl('/api/analytics/history/'), { headers: { Authorization: `Bearer ${token}` } }),
          fetch(apiUrl('/api/analytics/baseline/'), { headers: { Authorization: `Bearer ${token}` } })
        ]);
        
        if (histRes.ok && baseRes.ok) {
          setData(await histRes.json());
          setBurnout(await baseRes.json());
        }
      } catch (err) {
        console.error("Failed to fetch analytics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [token]);

  if (loading) return <div className="text-gray-400 p-8 text-center animate-pulse text-sm uppercase tracking-widest">Loading Analytics...</div>;
  if (!data) return <div className="text-gray-400 p-8 text-center">No historical data available.</div>;

  return (
    <div className="flex flex-col gap-6 w-full animate-in fade-in duration-500">
      
      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-gray-400">
            <AlertCircle className="w-4 h-4" />
            <h3 className="text-xs uppercase tracking-wider font-semibold">Burnout Risk</h3>
          </div>
          <div className="flex items-end gap-3">
            <span className={`text-3xl font-bold ${burnout?.burnout_risk === 'High' ? 'text-red-500' : burnout?.burnout_risk === 'Moderate' ? 'text-orange-500' : 'text-emerald-500'}`}>
              {burnout?.burnout_risk || 'Low'}
            </span>
            {burnout?.burnout_increase_pct > 0 && (
              <span className="text-sm text-red-400 font-medium mb-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> {burnout.burnout_increase_pct}%
              </span>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-gray-400">
            <Clock className="w-4 h-4" />
            <h3 className="text-xs uppercase tracking-wider font-semibold">Peak Focus Window</h3>
          </div>
          <div className="text-2xl font-bold text-gray-800">
            {data.peak_hour}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-2 mb-2 text-gray-400">
            <Activity className="w-4 h-4" />
            <h3 className="text-xs uppercase tracking-wider font-semibold">Total Sessions</h3>
          </div>
          <div className="text-2xl font-bold text-gray-800">
            {data.total_sessions}
          </div>
        </div>

      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Focus Trend */}
        <div className="xl:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100 min-h-[350px] flex flex-col">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-gray-400 mb-6">Weekly Focus Trend</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.weekly_trend}>
                <defs>
                  <linearGradient id="colorFocus" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tickFormatter={(t) => t.split(' ')[0]} stroke="#cbd5e1" fontSize={10} tickMargin={10} minTickGap={30} />
                <YAxis stroke="#cbd5e1" fontSize={10} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Area type="monotone" dataKey="focus" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorFocus)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fatigue Heatmap */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 min-h-[350px] flex flex-col">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-gray-400 mb-6">Fatigue Heatmap</h3>
          <div className="flex-1 flex flex-col gap-3 justify-center">
            {data.heatmap.map((d: any) => (
              <div key={d.day} className="flex items-center gap-4">
                <span className="text-xs font-medium text-gray-500 w-8">{d.day}</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div 
                      key={i} 
                      className={`w-8 h-8 rounded-md transition-colors ${
                        i <= d.fatigue_blocks 
                          ? i >= 4 ? 'bg-red-400' : i === 3 ? 'bg-orange-400' : 'bg-emerald-400'
                          : 'bg-gray-100'
                      }`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
