import React from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";

export const GatewayHealth: React.FC = () => {
  const { socketStatus, latestPrediction } = useCognitiveStore();

  const isConnected = socketStatus === "connected";
  // Consider ML active if we have a prediction in the last 10 seconds, or just if connected for the demo
  const isMlActive = isConnected && latestPrediction !== null;

  return (
    <div className="flex items-center gap-4 bg-white/80 backdrop-blur-sm border border-gray-100 rounded-full px-4 py-2 shadow-sm text-xs font-medium text-gray-600">
      <div className="flex items-center gap-1.5">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-rose-500 animate-pulse'}`}></div>
        <span>Gateway Connected</span>
      </div>
      <div className="w-px h-3 bg-gray-200"></div>
      <div className="flex items-center gap-1.5">
        <div className={`w-2 h-2 rounded-full ${isMlActive ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-400'}`}></div>
        <span>ML Service Active</span>
      </div>
      <div className="w-px h-3 bg-gray-200"></div>
      <div className="flex items-center gap-1.5">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-gray-300'}`}></div>
        <span>WebSocket Stable</span>
      </div>
    </div>
  );
};
