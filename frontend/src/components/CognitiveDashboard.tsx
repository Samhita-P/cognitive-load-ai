import React from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";
import { BrainCircuit, Activity, Zap, Info } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { PrivacyControls } from "./PrivacyControls";

export const CognitiveDashboard: React.FC = () => {
  const { latestPrediction, timeline } = useCognitiveStore();

  if (!latestPrediction) {
    return (
      <div className="w-full bg-white/80 backdrop-blur-md border border-gray-100 rounded-2xl p-12 flex flex-col items-center justify-center min-h-[400px] shadow-sm">
        <BrainCircuit className="w-10 h-10 text-gray-300 animate-pulse mb-6" />
        <p className="text-gray-500 font-medium text-lg tracking-tight">Awaiting behavioral signals...</p>
        <p className="text-sm text-gray-400 mt-2 text-center max-w-md">
          The inference engine is standing by. Generate manual telemetry or trigger a scenario.
        </p>
      </div>
    );
  }

  const { state, focus_score, fatigue_score, confidence, top_factors } = latestPrediction;

  // Determine elegant color mapping
  const stateColorMap: Record<string, string> = {
    Focused: "text-emerald-500",
    Distracted: "text-amber-500",
    Fatigued: "text-rose-500",
    Normal: "text-gray-500",
    Unknown: "text-slate-400",
  };
  
  const stateBgMap: Record<string, string> = {
    Focused: "bg-emerald-50 border-emerald-100",
    Distracted: "bg-amber-50 border-amber-100",
    Fatigued: "bg-rose-50 border-rose-100",
    Normal: "bg-gray-50 border-gray-100",
    Unknown: "bg-slate-50 border-slate-100",
  };

  const currentColorClass = stateColorMap[state] || stateColorMap.Normal;
  const currentBgClass = stateBgMap[state] || stateBgMap.Normal;

  // Format timeline data for Recharts
  const chartData = timeline.map((p, index) => ({
    time: index, // Simplified time index for MVP
    focus: Math.round(p.focus_score),
    fatigue: Math.round(p.fatigue_score),
  }));

  return (
    <div className="w-full space-y-6">
      
      {/* Top Banner: Current State */}
      <div className={`w-full rounded-2xl border p-6 shadow-sm transition-all duration-700 ease-in-out flex items-center justify-between ${currentBgClass}`}>
        <div className="flex items-center gap-4">
          <BrainCircuit className={`w-8 h-8 ${currentColorClass}`} />
          <div>
            <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase">Current Cognitive State</h2>
            <div className="flex items-baseline gap-3 mt-1">
              <span className={`text-3xl font-bold tracking-tight ${currentColorClass}`}>{state}</span>
              <span className="text-sm text-gray-500 font-medium">{Math.round(confidence)}% confidence</span>
            </div>
          </div>
        </div>
        
        {/* Subtle Intervention Suggestion */}
        {state === "Fatigued" && (
          <div className="bg-white/60 px-4 py-3 rounded-lg border border-rose-100 shadow-sm max-w-xs text-sm text-rose-800">
            <span className="font-semibold block mb-1">Intervention Suggested</span>
            Your focus metrics indicate rising fatigue. Consider a 5-minute offline break.
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Realtime Scores */}
        <div className="md:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-gray-500 font-medium flex items-center gap-2"><Activity className="w-4 h-4"/> Focus Score</h3>
              <span className="text-2xl font-semibold text-gray-800">{Math.round(focus_score)}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div className="bg-emerald-400 h-2 transition-all duration-500 ease-out" style={{ width: `${focus_score}%` }}></div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-gray-500 font-medium flex items-center gap-2"><Zap className="w-4 h-4"/> Fatigue Score</h3>
              <span className="text-2xl font-semibold text-gray-800">{Math.round(fatigue_score)}</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div className="bg-rose-400 h-2 transition-all duration-500 ease-out" style={{ width: `${fatigue_score}%` }}></div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-gray-500 font-medium flex items-center gap-2 mb-4"><Info className="w-4 h-4"/> Explainability</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              {top_factors.map((factor: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-gray-300">•</span>
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Realtime Timeline Chart */}
        <div className="md:col-span-2 bg-white rounded-2xl border border-gray-100 p-6 shadow-sm flex flex-col">
          <h3 className="text-gray-500 font-medium mb-6">Cognitive Timeline (Last 50 Windows)</h3>
          <div className="flex-grow w-full min-h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, 100]} stroke="#e5e7eb" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  labelStyle={{ display: 'none' }}
                />
                <ReferenceLine y={60} stroke="#f43f5e" strokeDasharray="3 3" opacity={0.3} />
                <Line type="monotone" dataKey="focus" stroke="#10b981" strokeWidth={3} dot={false} animationDuration={500} />
                <Line type="monotone" dataKey="fatigue" stroke="#f43f5e" strokeWidth={3} dot={false} animationDuration={500} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Privacy Controls */}
      <div className="mt-8">
        <PrivacyControls />
      </div>
    </div>
  );
};
