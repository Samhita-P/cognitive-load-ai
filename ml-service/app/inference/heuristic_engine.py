from typing import Dict, Tuple, List
import time

# Store previous scores for temporal smoothing
# session_id -> (prev_focus, prev_fatigue, consecutive_state_count, prev_state, transition_count, state_start_time)
session_state_memory: Dict[str, Tuple[float, float, int, str, int, float]] = {}

class HeuristicEngine:
    @staticmethod
    def infer_state(session_id: str, features: dict) -> Tuple[str, float, float, float, List[str]]:
        """
        Calculates Focus and Fatigue scores based on heuristics.
        Applies temporal smoothing and persistence logic.
        """
        if not features:
            return "Unknown", 0.0, 0.0, 0.0, []

        idle_ratio = features.get("idle_ratio", 0)
        activity_density = features.get("activity_density", 0)
        error_rate = features.get("error_rate", 0)
        max_pause_ms = features.get("max_pause_ms", 0)
        
        top_factors = []

        # 1. Raw Score Calculation
        raw_focus = 50.0 + (activity_density * 2.0) - (idle_ratio * 40.0)
        raw_focus = max(0.0, min(100.0, raw_focus))
        
        raw_fatigue = 0.0 + (error_rate * 80.0) + (max_pause_ms / 100.0)
        raw_fatigue = max(0.0, min(100.0, raw_fatigue))

        # 2. Temporal Smoothing
        # old_state: (focus, fatigue, count, state, transitions, start_time)
        memory = session_state_memory.get(session_id, (50.0, 0.0, 0, "Unknown", 0, time.time()))
        prev_focus, prev_fatigue, consecutive_count, prev_state, transition_count, state_start_time = memory
        
        # current = (old * 0.7) + (new * 0.3)
        focus_score = (prev_focus * 0.7) + (raw_focus * 0.3)
        fatigue_score = (prev_fatigue * 0.7) + (raw_fatigue * 0.3)

        # 3. Categorical State Logic
        raw_state = "Focused"
        if fatigue_score > 60:
            raw_state = "Fatigued"
            top_factors.append(f"High error rate ({error_rate:.2f})") if error_rate > 0.1 else None
            top_factors.append("Extended typing pauses") if max_pause_ms > 3000 else None
        elif idle_ratio > 0.4 and focus_score < 40:
            raw_state = "Distracted"
            top_factors.append(f"High idle ratio ({idle_ratio:.2f})")
        elif focus_score > 70:
            raw_state = "Focused"
            top_factors.append("High continuous activity")
        else:
            raw_state = "Normal"

        if not top_factors:
            top_factors.append("Baseline interaction patterns")

        # 4. State Transition Persistence
        # A state must persist for 3 consecutive windows, otherwise we keep the old state
        final_state = prev_state
        if raw_state == prev_state:
            consecutive_count += 1
        else:
            consecutive_count = 1
            
        if consecutive_count >= 3 or prev_state == "Unknown":
            if final_state != raw_state and prev_state != "Unknown":
                transition_count += 1
                state_start_time = time.time()
            final_state = raw_state
            
        state_duration_sec = time.time() - state_start_time
            
        # Update memory
        session_state_memory[session_id] = (focus_score, fatigue_score, consecutive_count, final_state, transition_count, state_start_time)

        # 5. Meaningful Confidence Calibration
        # Base confidence from stability
        confidence = 50.0 + min(consecutive_count * 5.0, 20.0) 
        
        # Feature agreement boost
        if final_state == "Focused" and activity_density > 1.5 and error_rate < 0.05:
            confidence += 20.0
        elif final_state == "Fatigued" and error_rate > 0.15 and max_pause_ms > 2000:
            confidence += 20.0
        elif final_state == "Distracted" and idle_ratio > 0.5:
            confidence += 20.0
            
        # Time-in-state boost
        if state_duration_sec > 60:
            confidence += 5.0
            
        confidence = min(98.0, confidence)

        import logging
        logging.getLogger(__name__).info(
            f"[Inference] session={session_id} state={final_state} duration={int(state_duration_sec)}s "
            f"transitions={transition_count} confidence={confidence:.1f}%"
        )

        return final_state, focus_score, fatigue_score, confidence, top_factors
