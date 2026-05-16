from django.utils import timezone
from django.db.models import Avg, Max, Count
from .models import CognitiveSession, CognitivePrediction, CompressedTelemetry
import logging

logger = logging.getLogger(__name__)

def finalize_session(session_id, reason="timeout"):
    try:
        session = CognitiveSession.objects.get(id=session_id)
        if session.status in ['completed', 'abandoned', 'expired']:
            return
            
        session.status = 'expired' if reason == 'timeout' else 'completed'
        session.ended_reason = reason
        session.ended_at = timezone.now() if reason != 'timeout' else session.last_activity_at

        # 1. Aggregate Predictions
        preds = session.predictions.all()
        prediction_count = preds.count()
        
        dominant_state = "Normal"
        if prediction_count > 0:
            agg = preds.aggregate(Avg('focus_score'), Max('fatigue_score'))
            session.average_focus = agg['focus_score__avg']
            session.peak_fatigue = agg['fatigue_score__max']
            
            # Dominant state
            state_counts = preds.values('predicted_state').annotate(count=Count('predicted_state')).order_by('-count')
            if state_counts:
                dominant_state = state_counts[0]['predicted_state']
                
        # 2. Aggregate Telemetry
        telemetries = session.telemetry.all()
        total_keystrokes = 0
        total_clicks = 0
        total_mouse_distance = 0.0
        total_idle_ms = 0
        duration_ms = 0
        
        if telemetries.exists():
            first_t = telemetries.first().timestamp
            last_t = telemetries.last().timestamp
            duration_ms = (last_t - first_t).total_seconds() * 1000
            
            for t in telemetries:
                total_keystrokes += t.keyboard_data.get('keystrokes', 0)
                total_clicks += t.mouse_data.get('clicks', 0)
                total_mouse_distance += t.mouse_data.get('distance_px', 0)
                total_idle_ms += t.activity_data.get('idle_time_ms', 0)

        if duration_ms <= 0:
            duration_ms = 5000

        idle_ratio = total_idle_ms / duration_ms
        total_events = total_keystrokes + total_clicks + (total_mouse_distance / 100)
        activity_density = total_events / (duration_ms / 1000)

        # 3. Create cleanly structured session_summary
        session.session_summary = {
            "average_focus": round(session.average_focus or 0, 1),
            "peak_fatigue": round(session.peak_fatigue or 0, 1),
            "average_idle_ratio": round(min(idle_ratio, 1.0), 2),
            "average_activity_density": round(activity_density, 2),
            "intervention_count": session.total_interventions,
            "prediction_count": prediction_count,
            "duration_minutes": round((duration_ms / 1000) / 60, 1),
            "dominant_state": dominant_state
        }
        
        session.save()
        logger.info(f"Finalized session {session.id} with reason {reason}")
    except Exception as e:
        logger.error(f"Error finalizing session {session_id}: {e}")
