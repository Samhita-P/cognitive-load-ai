from collections import deque
from app.schemas.telemetry import TelemetryBatch
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    @staticmethod
    def extract_features(window: deque):
        """
        Aggregates a sliding window of TelemetryBatches (up to 30s)
        into a single feature vector for inference.
        """
        if not window:
            return {}

        total_keystrokes = 0
        total_backspaces = 0
        max_pause = 0
        
        total_mouse_distance = 0.0
        total_clicks = 0
        sum_variance_x = 0.0
        sum_variance_y = 0.0
        
        total_idle_ms = 0
        
        duration_ms = (window[-1].timestamp_end - window[0].timestamp_start)
        if duration_ms == 0:
            duration_ms = 5000  # fallback to 5s if only 1 batch
        
        for batch in window:
            total_keystrokes += batch.keyboard.keystrokes
            total_backspaces += batch.keyboard.backspaces
            if batch.keyboard.longest_pause_ms > max_pause:
                max_pause = batch.keyboard.longest_pause_ms
                
            total_mouse_distance += batch.mouse.distance_px
            total_clicks += batch.mouse.clicks
            sum_variance_x += batch.mouse.variance_x
            sum_variance_y += batch.mouse.variance_y
            
            total_idle_ms += batch.session.idle_time_ms
            
        # Engineered Features
        idle_ratio = total_idle_ms / duration_ms
        
        # Activity density (events per second)
        total_events = total_keystrokes + total_clicks + (total_mouse_distance / 100) # proxy for mouse activity
        activity_density = total_events / (duration_ms / 1000)
        
        error_rate = 0.0
        if total_keystrokes > 0:
            error_rate = total_backspaces / total_keystrokes
            
        avg_mouse_variance = (sum_variance_x + sum_variance_y) / len(window)

        features = {
            "idle_ratio": min(idle_ratio, 1.0),
            "activity_density": activity_density,
            "error_rate": error_rate,
            "max_pause_ms": max_pause,
            "avg_mouse_variance": avg_mouse_variance,
            "total_keystrokes": total_keystrokes
        }
        
        # Apply Personalization (Relative Features)
        baseline = window[-1].session.user_baseline
        if baseline:
            base_idle = baseline.get("idle_ratio", 0.2)
            base_activity = baseline.get("activity_density", 3.0)
            
            # Prevent div-by-zero
            base_idle = base_idle if base_idle > 0.01 else 0.01
            base_activity = base_activity if base_activity > 0.1 else 0.1
            
            features["relative_idle_ratio"] = min(features["idle_ratio"] / base_idle, 3.0)
            features["relative_activity_density"] = min(features["activity_density"] / base_activity, 3.0)
        else:
            # Fallback to absolute if no baseline
            features["relative_idle_ratio"] = features["idle_ratio"] / 0.2
            features["relative_activity_density"] = features["activity_density"] / 3.0
        
        
        # Feature Snapshot Logging
        logger.info(f"[Features] session={window[-1].session_id} "
                    f"activity={features['activity_density']:.2f} "
                    f"idle={features['idle_ratio']:.2f} "
                    f"err={features['error_rate']:.2f}")

        return features
