import React, { useState, useEffect } from "react";
import { useCognitiveStore } from "../store/useCognitiveStore";
import { useAuthStore } from "../store/useAuthStore";
import { X } from "lucide-react";
import { apiUrl } from "../config/env";

export const FeedbackPopup: React.FC = () => {
  const { latestPrediction } = useCognitiveStore();
  const token = useAuthStore((s) => s.token);
  const [isVisible, setIsVisible] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  useEffect(() => {
    if (!latestPrediction || hasSubmitted) return;

    const isFatigued = latestPrediction.state === "Fatigued";
    const isLowConfidence = latestPrediction.confidence < 60;

    if ((isFatigued || isLowConfidence) && Math.random() > 0.8) {
      setIsVisible(true);
    }
  }, [latestPrediction, hasSubmitted]);

  const handleSubmit = async (label: string) => {
    if (!latestPrediction || !token) return;

    const features_snapshot =
      latestPrediction.engine_features && Object.keys(latestPrediction.engine_features).length > 0
        ? latestPrediction.engine_features
        : {
            focus_score: latestPrediction.focus_score,
            fatigue_score: latestPrediction.fatigue_score,
            state: latestPrediction.state,
          };

    const body: Record<string, unknown> = {
      human_label: label,
      features_snapshot,
      prediction_state: latestPrediction.state,
      confidence: latestPrediction.confidence,
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
        const err = await res.json().catch(() => ({}));
        console.error("Feedback error", res.status, err);
      }
    } catch (err) {
      console.error("Feedback error", err);
    }

    setIsVisible(false);
    setHasSubmitted(true);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 left-4 bg-white shadow-xl border border-gray-100 rounded-xl p-5 max-w-sm z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-gray-800">How focused do you feel right now?</h3>
        <button
          type="button"
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => handleSubmit("Focused")}
          className="bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-sm font-medium py-2 rounded transition-colors"
        >
          Focused
        </button>
        <button
          type="button"
          onClick={() => handleSubmit("Normal")}
          className="bg-slate-50 hover:bg-slate-100 text-slate-700 text-sm font-medium py-2 rounded transition-colors"
        >
          Normal
        </button>
        <button
          type="button"
          onClick={() => handleSubmit("Distracted")}
          className="bg-amber-50 hover:bg-amber-100 text-amber-700 text-sm font-medium py-2 rounded transition-colors"
        >
          Distracted
        </button>
        <button
          type="button"
          onClick={() => handleSubmit("Fatigued")}
          className="bg-rose-50 hover:bg-rose-100 text-rose-700 text-sm font-medium py-2 rounded transition-colors"
        >
          Fatigued
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-3 text-center">
        Saved to your account for supervised training (gateway API).
      </p>
    </div>
  );
};
