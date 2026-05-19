import React, { useState } from "react";
import { PlayCircle, Loader2 } from "lucide-react";
import { apiUrl } from "../config/env";

export const DemoControlPanel: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [activeScenario, setActiveScenario] = useState("");

  const runScenario = async (scenario: string) => {
    setIsRunning(true);
    setActiveScenario(scenario);

    try {
      const res = await fetch(
        `${apiUrl("/api/demo/trigger")}?scenario=${encodeURIComponent(scenario)}`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!res.ok) {
        throw new Error(`Request failed: ${res.status}`);
      }

      const data = await res.json();
      console.log("Demo started:", data);

      // Scenario runs for 60 seconds
      setTimeout(() => {
        setIsRunning(false);
        setActiveScenario("");
      }, 60000);

    } catch (error) {
      console.error("Scenario trigger failed:", error);
      setIsRunning(false);
      setActiveScenario("");
    }
  };

  return (
    <div className="w-full bg-white border border-gray-100 rounded-xl p-5 shadow-sm flex flex-col gap-4">
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
          Scenario Orchestration
        </h3>
        <p className="text-xs text-gray-500">
          Trigger deterministic sequences.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        {/* Deep Focus */}
        <button
          disabled={isRunning}
          onClick={() => runScenario("Deep Focus")}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all w-full
            ${activeScenario === "Deep Focus"
              ? "bg-emerald-50 border border-emerald-100 text-emerald-800"
              : "bg-gray-50 border border-transparent text-gray-600 hover:bg-emerald-50 hover:text-emerald-700 disabled:opacity-50"
            }`}
        >
          {activeScenario === "Deep Focus" ? (
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
          ) : (
            <PlayCircle className="w-4 h-4 text-emerald-600 opacity-70" />
          )}
          Deep Focus
        </button>

        {/* Severe Fatigue */}
        <button
          disabled={isRunning}
          onClick={() => runScenario("Severe Fatigue")}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all w-full
            ${activeScenario === "Severe Fatigue"
              ? "bg-rose-50 border border-rose-100 text-rose-800"
              : "bg-gray-50 border border-transparent text-gray-600 hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50"
            }`}
        >
          {activeScenario === "Severe Fatigue" ? (
            <Loader2 className="w-4 h-4 animate-spin text-rose-600" />
          ) : (
            <PlayCircle className="w-4 h-4 text-rose-600 opacity-70" />
          )}
          Fatigue Spike
        </button>

        {/* Task Switching */}
        <button
          disabled={isRunning}
          onClick={() => runScenario("Chaotic Task Switching")}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all w-full
            ${activeScenario === "Chaotic Task Switching"
              ? "bg-amber-50 border border-amber-100 text-amber-800"
              : "bg-gray-50 border border-transparent text-gray-600 hover:bg-amber-50 hover:text-amber-700 disabled:opacity-50"
            }`}
        >
          {activeScenario === "Chaotic Task Switching" ? (
            <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
          ) : (
            <PlayCircle className="w-4 h-4 text-amber-600 opacity-70" />
          )}
          Task Switching
        </button>
      </div>
    </div>
  );
};