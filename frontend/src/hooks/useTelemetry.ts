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
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);

  const aggregatorRef = useRef<TelemetryAggregator | null>(null);

  const { setBaseline, baseline } = useCognitiveStore();

  const telemetryConsent = usePrivacyStore((s) => s.telemetryConsent);
  const privacyMode = usePrivacyStore((s) => s.privacyMode);

  useEffect(() => {
    // Privacy enforcement
    if (privacyMode || !telemetryConsent) {
      aggregatorRef.current = null;
      telemetrySocket.disconnect();
      return;
    }

    // Demo mode support
    if (!isAuthenticated && !token) {
      console.log("[Telemetry] Starting in demo bootstrap mode");
    }

    // Fetch baseline only for authenticated users
    if (token) {
      fetch(apiUrl("/api/analytics/baseline/"), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Baseline fetch failed: ${res.status}`);
          }
          return res.json();
        })
        .then((data) => {
          if (data?.baseline) {
            setBaseline(data.baseline);
          }
        })
        .catch((err) => {
          console.error("[Telemetry] Failed to fetch baseline:", err);
        });
    }

    const sessionId = uuidv4();
    const aggregator = new TelemetryAggregator(sessionId, baseline);

    aggregatorRef.current = aggregator;

    // Start authenticated websocket flow
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
      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange
      );

      clearInterval(batchInterval);

      telemetrySocket.disconnect();

      aggregatorRef.current = null;
    };
  }, [
    token,
    isAuthenticated,
    telemetryConsent,
    privacyMode,
    baseline,
    setBaseline,
  ]);
};