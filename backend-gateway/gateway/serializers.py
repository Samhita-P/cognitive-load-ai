from rest_framework import serializers

class HumanFeedbackCreateSerializer(serializers.Serializer):
    focus_score = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    fatigue_score = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    workload_score = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    confidence_score = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    
    label_source = serializers.CharField(max_length=50, default='self-report', allow_blank=False)
    prompt_trigger_type = serializers.CharField(max_length=50, default='random', allow_blank=False)
    
    tab_switch_count = serializers.IntegerField(default=0, min_value=0, max_value=1000)
    prompt_response_delay_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=3600000) # Max 1 hour
    visibility_state = serializers.CharField(max_length=50, default='visible', allow_blank=False)
    
    features_snapshot = serializers.JSONField()
    feature_schema_version = serializers.CharField(max_length=50, default='v1.0')

    def validate_features_snapshot(self, value):
        if not isinstance(value, dict) or len(value) < 1:
            raise serializers.ValidationError("features_snapshot must be a non-empty object.")
        if len(str(value)) > 100000: # ~100KB hard limit to prevent DB bloat
            raise serializers.ValidationError("features_snapshot payload is too large.")
        return value
