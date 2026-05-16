import { create } from "zustand";
import type { CognitiveStatePrediction, AdaptiveAction } from "@shared/types";

interface CognitiveStore {
  latestPrediction: CognitiveStatePrediction | null;
  timeline: CognitiveStatePrediction[];
  activeIntervention: AdaptiveAction | null;
  socketStatus: "connected" | "reconnecting" | "disconnected";
  isDeepWorkMode: boolean;
  baseline: Record<string, number> | null;
  addPrediction: (prediction: CognitiveStatePrediction) => void;
  setIntervention: (action: AdaptiveAction | null) => void;
  setSocketStatus: (status: "connected" | "reconnecting" | "disconnected") => void;
  clearHistory: () => void;
  setBaseline: (baseline: Record<string, number> | null) => void;
}

export const useCognitiveStore = create<CognitiveStore>((set) => ({
  latestPrediction: null,
  timeline: [],
  activeIntervention: null,
  socketStatus: "disconnected",
  isDeepWorkMode: false,
  baseline: null,

  addPrediction: (prediction) =>
    set((state) => {
      // Keep only the last 50 predictions in memory for the timeline
      const newTimeline = [...state.timeline, prediction].slice(-50);
      
      // Calculate Deep Work Mode: 3 consecutive windows > 80 focus
      const recent = newTimeline.slice(-3);
      const isDeepWorkMode = recent.length === 3 && recent.every(p => p.focus_score > 80);
      
      return {
        latestPrediction: prediction,
        timeline: newTimeline,
        isDeepWorkMode
      };
    }),

  setIntervention: (action) => set({ activeIntervention: action }),

  setSocketStatus: (status) => set({ socketStatus: status }),

  clearHistory: () => set({ timeline: [], latestPrediction: null, activeIntervention: null, isDeepWorkMode: false }),
  
  setBaseline: (baseline) => set({ baseline }),
}));
