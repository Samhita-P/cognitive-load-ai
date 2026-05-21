import { useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { throttle } from "lodash";
import { TelemetryAggregator } from "../services/telemetryAggregator";
import { telemetrySocket } from "../services/websocket";
import { useAuthStore } from "../store/useAuthStore";
import { useCognitiveStore } from "../store/useCognitiveStore";
import { usePrivacyStore } from "../store/usePrivacyStore";
import { apiUrl } from "../config/env";

export const useTelemetry = () => {
  const token = useAuthStore((s) => s.token);
  const aggregatorRef = useRef<TelemetryAggregator | null>(null);

  const { setBaseline, baseline } = useCognitiveStore();

  const telemetryConsent = usePrivacyStore((s) => s.telemetryConsent);
  const privacyMode = usePrivacyStore((s) => s.privacyMode);

  useEffect(() => {
    if (privacyMode || !telemetryConsent) {
      telemetrySocket.disconnect();
      aggregatorRef.current = null;
      return;
    }

    const fetchBaseline = async () => {
      try {
        if (token) {
          const res = await fetch(apiUrl("/api/analytics/baseline/"), {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (res.ok) {
            const data = await res.json();
            if (data.baseline) {
              setBaseline(data.baseline);
            }
          }
        }
      } catch (err) {
        console.error("Baseline fetch failed:", err);
      }
    };

    fetchBaseline();

    const sessionId = uuidv4();
    const aggregator = new TelemetryAggregator(sessionId, baseline);
    aggregatorRef.current = aggregator;

    console.log("[Telemetry] Starting websocket...");
    telemetrySocket.connect();

    const handleKeyDown = (e: KeyboardEvent) => {
      aggregator.trackKeydown(e.key);
    };

    const handleMouseMove = throttle((e: MouseEvent) => {
      aggregator.trackMouseMove(e.clientX, e.clientY);
    }, 100);

    const handleClick = () => {
      aggregator.trackClick();
    };

    const handleVisibilityChange = () => {
      aggregator.trackVisibility(document.hidden);
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("click", handleClick);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    const batchInterval = setInterval(() => {
      const batch = aggregator.flushBatch();

      if (batch) {
        telemetrySocket.sendBatch(batch);

        window.dispatchEvent(
          new CustomEvent("telemetry_batch_sent", {
            detail: batch,
          })
        );
      }
    }, 5000);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("mousemove", handleMouseMove);
      handleMouseMove.cancel();
      window.removeEventListener("click", handleClick);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      clearInterval(batchInterval);

      telemetrySocket.disconnect();
      aggregatorRef.current = null;
    };
  }, [token, telemetryConsent, privacyMode]);
};