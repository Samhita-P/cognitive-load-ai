from django.db import models
from django.contrib.auth.models import User

class CognitiveSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cognitive_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    ended_reason = models.CharField(max_length=50, null=True, blank=True)
    average_focus = models.FloatField(null=True, blank=True)
    peak_fatigue = models.FloatField(null=True, blank=True)
    total_interventions = models.IntegerField(default=0)
    session_summary = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} ({self.status}) for {self.user.username}"

class CompressedTelemetry(models.Model):
    session = models.ForeignKey(CognitiveSession, on_delete=models.CASCADE, related_name='telemetry')
    timestamp = models.DateTimeField(auto_now_add=True)
    keyboard_data = models.JSONField(default=dict)
    mouse_data = models.JSONField(default=dict)
    activity_data = models.JSONField(default=dict)

class CognitivePrediction(models.Model):
    session = models.ForeignKey(CognitiveSession, on_delete=models.CASCADE, related_name='predictions')
    timestamp = models.DateTimeField(auto_now_add=True)
    batch_id = models.CharField(max_length=64, blank=True, default='')
    focus_score = models.FloatField()
    fatigue_score = models.FloatField()
    predicted_state = models.CharField(max_length=50)
    confidence = models.FloatField()
    model_version = models.CharField(max_length=50, default='v1_heuristic')
    model_source = models.CharField(max_length=50, default='heuristic')
    top_factors = models.JSONField(default=list)

class HumanFeedback(models.Model):
    session = models.ForeignKey(CognitiveSession, on_delete=models.CASCADE, related_name='feedbacks')
    prediction = models.ForeignKey(CognitivePrediction, on_delete=models.CASCADE, null=True, blank=True)
    user_label = models.CharField(max_length=50)
    features_snapshot = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
