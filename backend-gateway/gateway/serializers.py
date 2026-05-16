from rest_framework import serializers

ALLOWED_LABELS = {"Focused", "Distracted", "Fatigued", "Normal"}


class HumanFeedbackCreateSerializer(serializers.Serializer):
    human_label = serializers.ChoiceField(choices=[(c, c) for c in sorted(ALLOWED_LABELS)])
    features_snapshot = serializers.JSONField()
    prediction_id = serializers.IntegerField(required=False, allow_null=True)
    prediction_state = serializers.CharField(max_length=50, required=False, allow_blank=True)
    confidence = serializers.FloatField(required=False, default=0.0)

    def validate_features_snapshot(self, value):
        if not isinstance(value, dict) or len(value) < 1:
            raise serializers.ValidationError("features_snapshot must be a non-empty object.")
        return value
