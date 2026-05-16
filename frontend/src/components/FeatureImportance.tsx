import React, { useMemo } from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";

const LABELS: Record<string, string> = {
  idle_ratio: "Idle ratio",
  activity_density: "Activity density",
  error_rate: "Error rate",
  max_pause_ms: "Max pause (ms)",
  avg_mouse_variance: "Mouse variance",
  total_keystrokes: "Keystrokes",
};

export const FeatureImportance: React.FC = () => {
  const { latestPrediction } = useCognitiveStore();

  const rows = useMemo(() => {
    const imp = latestPrediction?.feature_importances;
    if (imp && Object.keys(imp).length > 0) {
      return (Object.entries(imp) as [string, number][])
        .map(([key, value]) => ({
          name: LABELS[key] ?? key,
          value: Math.round(Math.min(100, Math.max(0, value * 100))),
        }))
        .sort((a, b) => b.value - a.value);
    }
    return null;
  }, [latestPrediction]);

  if (!latestPrediction) {
    return (
      <div className="w-full bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Model feature importances
        </h3>
        <p className="text-xs text-gray-500">Awaiting predictions…</p>
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="w-full bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          Model feature importances
        </h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          Shown when a trained Random Forest (<code className="text-[10px] bg-gray-100 px-1 rounded">v2_random_forest</code>) is
          present under <code className="text-[10px] bg-gray-100 px-1 rounded">ml-service/models/</code>. Heuristic mode does not
          emit importances.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
        Random Forest importances
      </h3>

      <div className="space-y-3">
        {rows.map((feature, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500 font-mono">{feature.name}</span>
            </div>
            <div className="w-full bg-gray-50 rounded-sm h-1.5 overflow-hidden flex">
              <div
                className="bg-indigo-400 h-1.5 transition-all duration-700 ease-out"
                style={{ width: `${feature.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
