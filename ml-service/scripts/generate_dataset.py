import json
import random
from pathlib import Path

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def clamp_int(val, min_val, max_val):
    return int(round(clamp(val, min_val, max_val)))

def generate_row():
    # Base archetypes to build coherent features
    archetypes = ["Focused", "Normal", "Distracted", "Fatigued", "Overloaded"]
    archetype = random.choice(archetypes)
    
    # Adding more overlap between classes to make the dataset realistic
    if archetype == "Focused":
        activity_density = random.gauss(4.0, 1.5)
        idle_ratio = random.gauss(0.15, 0.1)
        error_rate = random.gauss(0.03, 0.02)
        max_pause_ms = random.gauss(800, 400)
        avg_mouse_variance = random.gauss(30.0, 15.0)
        total_keystrokes = random.gauss(50, 20)
        
        # Likert Scales (1-5)
        focus_score = clamp_int(random.gauss(4.5, 0.5), 1, 5)
        fatigue_score = clamp_int(random.gauss(1.5, 0.5), 1, 5)
        workload_score = clamp_int(random.gauss(3.0, 0.8), 1, 5)
        
    elif archetype == "Normal":
        activity_density = random.gauss(2.5, 1.2)
        idle_ratio = random.gauss(0.3, 0.15)
        error_rate = random.gauss(0.06, 0.03)
        max_pause_ms = random.gauss(2000, 800)
        avg_mouse_variance = random.gauss(50.0, 25.0)
        total_keystrokes = random.gauss(30, 15)
        
        focus_score = clamp_int(random.gauss(3.0, 0.8), 1, 5)
        fatigue_score = clamp_int(random.gauss(2.5, 0.8), 1, 5)
        workload_score = clamp_int(random.gauss(2.5, 0.8), 1, 5)
        
    elif archetype == "Distracted":
        activity_density = random.gauss(1.5, 1.0)
        idle_ratio = random.gauss(0.5, 0.2)
        error_rate = random.gauss(0.1, 0.06)
        max_pause_ms = random.gauss(4000, 2000)
        avg_mouse_variance = random.gauss(120.0, 60.0)
        total_keystrokes = random.gauss(20, 12)
        
        focus_score = clamp_int(random.gauss(1.5, 0.5), 1, 5)
        fatigue_score = clamp_int(random.gauss(3.0, 1.0), 1, 5)
        workload_score = clamp_int(random.gauss(2.0, 0.8), 1, 5)
        
    elif archetype == "Fatigued":
        activity_density = random.gauss(1.0, 0.8)
        idle_ratio = random.gauss(0.6, 0.25)
        error_rate = random.gauss(0.15, 0.1)
        max_pause_ms = random.gauss(7000, 3000)
        avg_mouse_variance = random.gauss(80.0, 40.0)
        total_keystrokes = random.gauss(10, 8)
        
        focus_score = clamp_int(random.gauss(2.0, 0.8), 1, 5)
        fatigue_score = clamp_int(random.gauss(4.5, 0.5), 1, 5)
        workload_score = clamp_int(random.gauss(4.0, 0.8), 1, 5)
        
    elif archetype == "Overloaded":
        activity_density = random.gauss(3.5, 1.8)
        idle_ratio = random.gauss(0.2, 0.1)
        error_rate = random.gauss(0.25, 0.15)
        max_pause_ms = random.gauss(1500, 800)
        avg_mouse_variance = random.gauss(250.0, 120.0)
        total_keystrokes = random.gauss(40, 25)
        
        focus_score = clamp_int(random.gauss(3.5, 1.0), 1, 5)
        fatigue_score = clamp_int(random.gauss(4.0, 0.8), 1, 5)
        workload_score = clamp_int(random.gauss(4.8, 0.4), 1, 5)
        
    features = {
        "idle_ratio": clamp(idle_ratio, 0.0, 1.0),
        "activity_density": clamp(activity_density, 0.0, 20.0),
        "error_rate": clamp(error_rate, 0.0, 1.0),
        "max_pause_ms": clamp(max_pause_ms, 0, 30000),
        "avg_mouse_variance": clamp(avg_mouse_variance, 0.0, 1000.0),
        "total_keystrokes": int(clamp(total_keystrokes, 0, 300)),
        # Relative features added for parity
        "relative_idle_ratio": clamp(idle_ratio / 0.2, 0.0, 3.0),
        "relative_activity_density": clamp(activity_density / 3.0, 0.0, 3.0)
    }
    
    return {
        "label": archetype, # keep for backward compatibility
        "focus_score": focus_score,
        "fatigue_score": fatigue_score,
        "workload_score": workload_score,
        "confidence_score": clamp_int(random.gauss(4.0, 1.0), 1, 5),
        "tab_switch_count": max(0, int(random.gauss(0.5, 1.0))),
        "prompt_response_delay_ms": max(500, int(random.gauss(2000, 1000))),
        "visibility_state": "visible" if random.random() > 0.05 else "hidden",
        "features": features
    }

def main():
    root = Path(__file__).resolve().parent.parent.parent
    out_file = root / "feedback.jsonl"
    
    rows = 10000
    
    with open(out_file, "w", encoding="utf-8") as f:
        for _ in range(rows):
            f.write(json.dumps(generate_row()) + "\n")
            
    print(f"Generated {rows} rows in {out_file}")

if __name__ == "__main__":
    main()
