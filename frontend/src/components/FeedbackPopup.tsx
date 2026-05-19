import React, { useState, useEffect, useRef } from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";
import { useAuthStore } from "../store/useAuthStore";
import { X, Check } from "lucide-react";
import { apiUrl } from "../config/env";

const MIN_GAP_MS = 45 * 60 * 1000; // 45 minutes
const MAX_PROMPTS_PER_DAY = 3;

export const FeedbackPopup: React.FC = () => {
  const { latestPrediction } = useCognitiveStore();
  const token = useAuthStore((s) => s.token);
  const [isVisible, setIsVisible] = useState(false);
  
  // Form State
  const [focus, setFocus] = useState<number | null>(null);
  const [fatigue, setFatigue] = useState<number | null>(null);
  const [workload, setWorkload] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);

  // Metadata State
  const promptShownAt = useRef<number>(0);
  const tabSwitchCount = useRef<number>(0);
  const triggerType = useRef<string>("random");

  useEffect(() => {
    if (!latestPrediction || isVisible) return;

    const now = Date.now();
    const lastPromptTime = parseInt(localStorage.getItem("lastPromptTime") || "0");
    const promptsToday = parseInt(localStorage.getItem("promptsToday") || "0");
    const lastPromptDate = localStorage.getItem("lastPromptDate");
    const todayDate = new Date().toDateString();

    // Reset daily count
    let currentPromptsToday = promptsToday;
    if (lastPromptDate !== todayDate) {
      currentPromptsToday = 0;
      localStorage.setItem("lastPromptDate", todayDate);
    }

    if (currentPromptsToday >= MAX_PROMPTS_PER_DAY) return;
    if (now - lastPromptTime < MIN_GAP_MS) return;

    const isLowConfidence = latestPrediction.confidence < 60;
    const isFatigued = latestPrediction.state === "Fatigued";
    
    // Hybrid Strategy: 80% Random, 20% Anomaly
    // Anomaly = Low confidence or extreme state
    let triggered = false;
    
    if ((isLowConfidence || isFatigued) && Math.random() < 0.2) {
      triggerType.current = "anomaly";
      triggered = true;
    } else if (Math.random() < 0.05) { // Random chance (simulated roughly for 80% of actual occurrences)
      triggerType.current = "random";
      triggered = true;
    }

    if (triggered) {
      setIsVisible(true);
      promptShownAt.current = Date.now();
      tabSwitchCount.current = 0;
      setFocus(null);
      setFatigue(null);
      setWorkload(null);
      setConfidence(null);
      
      localStorage.setItem("lastPromptTime", now.toString());
      localStorage.setItem("promptsToday", (currentPromptsToday + 1).toString());
    }
  }, [latestPrediction, isVisible]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isVisible) {
        tabSwitchCount.current += 1;
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isVisible]);

  const handleSubmit = async () => {
    if (!latestPrediction || !token) return;
    if (!focus || !fatigue || !workload || !confidence) return;

    const features_snapshot =
      latestPrediction.engine_features && Object.keys(latestPrediction.engine_features).length > 0
        ? latestPrediction.engine_features
        : {
            focus_score: latestPrediction.focus_score,
            fatigue_score: latestPrediction.fatigue_score,
            state: latestPrediction.state,
          };

    const delayMs = Date.now() - promptShownAt.current;

    const body: Record<string, unknown> = {
      focus_score: focus,
      fatigue_score: fatigue,
      workload_score: workload,
      confidence_score: confidence,
      label_source: "self-report",
      prompt_trigger_type: triggerType.current,
      tab_switch_count: tabSwitchCount.current,
      prompt_response_delay_ms: delayMs,
      visibility_state: document.visibilityState,
      features_snapshot,
      feature_schema_version: "v1.1",
    };

    if (latestPrediction.gateway_prediction_id != null) {
      body.prediction_id = latestPrediction.gateway_prediction_id;
    }

    try {
      const res = await fetch(apiUrl("/api/feedback/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        console.error("Feedback error", res.status);
      }
    } catch (err) {
      console.error("Feedback error", err);
    }

    setIsVisible(false);
  };

  if (!isVisible) return null;

  const renderScale = (
    label: string, 
    value: number | null, 
    setValue: (v: number) => void,
    lowLabel: string,
    highLabel: string
  ) => (
    <div className="mb-4">
      <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
        <span>{label}</span>
      </div>
      <div className="flex justify-between gap-1">
        {[1, 2, 3, 4, 5].map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setValue(v)}
            className={`flex-1 py-1 text-sm rounded border transition-colors ${
              value === v 
                ? 'bg-blue-600 text-white border-blue-600' 
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
            }`}
          >
            {v}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );

  const canSubmit = focus && fatigue && workload && confidence;

  return (
    <div className="fixed bottom-4 right-4 bg-white shadow-2xl border border-gray-200 rounded-xl p-5 w-80 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold text-gray-800">Quick Check-in</h3>
        <button
          type="button"
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-1">
        {renderScale("Focus", focus, setFocus, "Distracted", "Hyper-focused")}
        {renderScale("Fatigue", fatigue, setFatigue, "Energetic", "Exhausted")}
        {renderScale("Workload", workload, setWorkload, "Light", "Overwhelming")}
        {renderScale("Confidence in answers", confidence, setConfidence, "Guessing", "Certain")}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg mt-4 font-medium transition-colors ${
          canSubmit 
            ? 'bg-gray-900 text-white hover:bg-gray-800' 
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
      >
        <Check className="w-4 h-4" />
        Submit
      </button>
      
      <p className="text-[10px] text-gray-400 mt-3 text-center">
        Data helps calibrate your personalized baseline.
      </p>
    </div>
  );
};
