import React, { useEffect, useState } from "react";
import type { ValidatedTelemetryBatch } from "../schemas/telemetry";

export const DevTelemetryOverlay: React.FC = () => {
  const [lastBatch, setLastBatch] = useState<ValidatedTelemetryBatch | null>(null);
  const [batchCount, setBatchCount] = useState(0);

  useEffect(() => {
    const handleBatchSent = (e: Event) => {
      const customEvent = e as CustomEvent<ValidatedTelemetryBatch>;
      setLastBatch(customEvent.detail);
      setBatchCount(prev => prev + 1);
    };

    window.addEventListener("telemetry_batch_sent", handleBatchSent);
    return () => window.removeEventListener("telemetry_batch_sent", handleBatchSent);
  }, []);

  if (!lastBatch) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 text-green-400 p-4 rounded shadow-lg text-xs font-mono z-50 max-w-xs opacity-90">
      <h3 className="text-white font-bold mb-2 border-b border-gray-700 pb-1">Dev Telemetry</h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span className="text-gray-400">Batch ID:</span>
        <span className="truncate" title={lastBatch.batch_id}>{lastBatch.batch_id.split("-")[0]}...</span>
        
        <span className="text-gray-400">Total Sent:</span>
        <span>{batchCount}</span>

        <span className="text-gray-400">Keystrokes:</span>
        <span>{lastBatch.keyboard.keystrokes}</span>

        <span className="text-gray-400">Mouse Dist:</span>
        <span>{lastBatch.mouse.distance_px}px</span>

        <span className="text-gray-400">Idle Time:</span>
        <span>{lastBatch.session.idle_time_ms}ms</span>
      </div>
    </div>
  );
};
