import React, { useMemo } from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";

export const SessionSummaryCard: React.FC = () => {
  const { timeline } = useCognitiveStore();

  const stats = useMemo(() => {
    if (timeline.length === 0) {
      return {
        avgFocus: 0,
        peakFatigue: 0,
        longestWindow: 0,
        interventions: 0,
      };
    }

    let totalFocus = 0;
    let peakFatigue = 0;
    let currentFocusStreak = 0;
    let maxFocusStreak = 0;
    let interventions = 0;

    for (let i = 0; i < timeline.length; i++) {
      const p = timeline[i];
      totalFocus += p.focus_score;
      if (p.fatigue_score > peakFatigue) peakFatigue = p.fatigue_score;

      if (p.state === "Focused") {
        currentFocusStreak++;
        if (currentFocusStreak > maxFocusStreak) maxFocusStreak = currentFocusStreak;
      } else {
        currentFocusStreak = 0;
      }

      // Count transitions into Fatigued as an intervention
      if (p.state === "Fatigued" && (i === 0 || timeline[i - 1].state !== "Fatigued")) {
        interventions++;
      }
    }

    return {
      avgFocus: Math.round(totalFocus / timeline.length),
      peakFatigue: Math.round(peakFatigue),
      // Assume each batch is roughly 5 seconds, window in minutes
      longestWindow: Math.round((maxFocusStreak * 5) / 60) || (maxFocusStreak > 0 ? "< 1" : 0),
      interventions,
    };
  }, [timeline]);

  return (
    <div className="w-full bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Session Summary</h3>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Average Focus</span>
          <span className="text-sm font-medium text-gray-800">{stats.avgFocus}%</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Peak Fatigue</span>
          <span className="text-sm font-medium text-gray-800">{stats.peakFatigue}%</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Longest Focus Window</span>
          <span className="text-sm font-medium text-gray-800">{stats.longestWindow}m</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Interventions</span>
          <span className="text-sm font-medium text-gray-800">{stats.interventions}</span>
        </div>
      </div>
    </div>
  );
};
