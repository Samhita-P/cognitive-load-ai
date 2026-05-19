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
    
    # Target Variables (Ordinal Likert 1-5)
    focus_score = models.IntegerField(null=True, blank=True)
    fatigue_score = models.IntegerField(null=True, blank=True)
    workload_score = models.IntegerField(null=True, blank=True)
    
    # Label Quality
    confidence_score = models.IntegerField(null=True, blank=True) # 1-5
    
    # Metadata for Label Context
    label_source = models.CharField(max_length=50, default='self-report') # e.g. self-report, nasa-tlx
    prompt_trigger_type = models.CharField(max_length=50, default='random') # e.g. random, anomaly, manual
    
    # Contamination Control
    tab_switch_count = models.IntegerField(default=0)
    prompt_response_delay_ms = models.IntegerField(null=True, blank=True)
    visibility_state = models.CharField(max_length=50, default='visible')
    
    # Feature Linkage
    features_snapshot = models.JSONField(default=dict)
    feature_schema_version = models.CharField(max_length=50, default='v1.0')
    
    timestamp = models.DateTimeField(auto_now_add=True)

class UserPrivacyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_profile')
    telemetry_consent = models.BooleanField(default=False)
    privacy_mode = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(auto_now_add=True)
    consent_version = models.CharField(max_length=50, default='1.0')
    deletion_requested_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Privacy Profile for {self.user.username} (Consent: {self.telemetry_consent})"

class PrivacyAuditLog(models.Model):
    EVENT_CHOICES = [
        ('CONSENT_GRANTED', 'Consent Granted'),
        ('CONSENT_REVOKED', 'Consent Revoked'),
        ('PRIVACY_MODE_ENABLED', 'Privacy Mode Enabled'),
        ('PRIVACY_MODE_DISABLED', 'Privacy Mode Disabled'),
        ('DELETION_REQUESTED', 'Deletion Requested'),
        ('DELETION_COMPLETED', 'Deletion Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='privacy_audit_logs')
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.event} at {self.timestamp}"
