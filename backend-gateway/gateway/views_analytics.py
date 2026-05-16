from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CognitiveSession
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Max

class HistoricalAnalyticsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        sessions = CognitiveSession.objects.filter(
            user=user, 
            started_at__gte=seven_days_ago,
            ended_at__isnull=False
        ).order_by('started_at')

        # Weekly Focus Trend (Line chart data)
        weekly_trend = []
        
        # Fatigue Heatmap Data
        heatmap_data = {}

        # Productivity Hours
        hour_focus = {}

        for session in sessions:
            day_str = session.started_at.strftime('%a')
            hour = session.started_at.hour
            
            # Aggregate Weekly Trend
            weekly_trend.append({
                'date': session.started_at.strftime('%Y-%m-%d %H:%M'),
                'focus': session.average_focus or 0,
                'fatigue': session.peak_fatigue or 0
            })

            # Aggregate Heatmap
            if day_str not in heatmap_data:
                heatmap_data[day_str] = []
            heatmap_data[day_str].append(session.peak_fatigue or 0)

            # Aggregate Hour Focus
            if hour not in hour_focus:
                hour_focus[hour] = []
            hour_focus[hour].append(session.average_focus or 0)

        # Process Heatmap
        final_heatmap = []
        days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days_order:
            if day in heatmap_data and len(heatmap_data[day]) > 0:
                avg_fatigue = sum(heatmap_data[day]) / len(heatmap_data[day])
                blocks = int((avg_fatigue / 100.0) * 5) # 0 to 5 blocks
                blocks = max(1, min(5, blocks))
                final_heatmap.append({'day': day, 'fatigue_blocks': blocks, 'value': avg_fatigue})
            else:
                final_heatmap.append({'day': day, 'fatigue_blocks': 0, 'value': 0})

        # Process Peak Hour
        peak_hour = None
        max_focus_avg = 0
        for h, focus_list in hour_focus.items():
            avg_f = sum(focus_list) / len(focus_list)
            if avg_f > max_focus_avg:
                max_focus_avg = avg_f
                peak_hour = h
                
        peak_hour_str = f"{peak_hour}:00 - {peak_hour+1}:00" if peak_hour is not None else "N/A"

        return Response({
            'weekly_trend': weekly_trend,
            'heatmap': final_heatmap,
            'peak_hour': peak_hour_str,
            'total_sessions': sessions.count()
        })

class UserBaselineView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        sessions = CognitiveSession.objects.filter(
            user=user, 
            started_at__gte=seven_days_ago
        )

        # Baseline Calculation
        total_activity = 0
        total_idle = 0
        count = 0
        
        recent_fatigues = []

        for session in sessions:
            summary = session.session_summary or {}
            
            # Assuming summary has average_activity_density and average_idle_ratio
            act = summary.get('average_activity_density')
            idle = summary.get('average_idle_ratio')
            if act is not None and idle is not None:
                total_activity += float(act)
                total_idle += float(idle)
                count += 1
                
            if session.peak_fatigue is not None:
                recent_fatigues.append(session.peak_fatigue)

        baseline = {
            'activity_density': total_activity / count if count > 0 else 3.0, # Default fallback
            'idle_ratio': total_idle / count if count > 0 else 0.2
        }

        # Burnout Risk Logic (Consecutive high fatigue)
        burnout_risk = "Low"
        burnout_increase = 0
        
        if len(recent_fatigues) >= 3:
            recent_avg = sum(recent_fatigues[-3:]) / 3
            older_avg = sum(recent_fatigues[:-3]) / len(recent_fatigues[:-3]) if len(recent_fatigues) > 3 else recent_avg
            
            if recent_avg > 75:
                burnout_risk = "High"
            elif recent_avg > 60:
                burnout_risk = "Moderate"
                
            if older_avg > 0:
                burnout_increase = int(((recent_avg - older_avg) / older_avg) * 100)

        return Response({
            'baseline': baseline,
            'burnout_risk': burnout_risk,
            'burnout_increase_pct': burnout_increase
        })
