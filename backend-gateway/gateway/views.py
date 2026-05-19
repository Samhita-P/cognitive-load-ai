from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView

from .models import CognitivePrediction, CognitiveSession, HumanFeedback
from .serializers import HumanFeedbackCreateSerializer
import secrets
import json
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle
from .ticket_store import WSTicketStore

class WSTicketThrottle(UserRateThrottle):
    scope = 'ws_ticket'
    rate = '10/min'


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

class WSTicketView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = [WSTicketThrottle]

    def post(self, request):
        ticket = secrets.token_urlsafe(32)
        payload = {
            "user_id": request.user.id,
            "purpose": "ws_auth"
        }
        WSTicketStore.issue(ticket, payload, ttl=60)
        return Response({"ticket": ticket}, status=status.HTTP_201_CREATED)

class HumanFeedbackSubmitView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ser = HumanFeedbackCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        session = (
            CognitiveSession.objects.filter(user=request.user, ended_at__isnull=True)
            .order_by("-started_at")
            .first()
        )
        if session is None:
            return Response(
                {"detail": "No active cognitive session. Open the dashboard and send telemetry first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not hasattr(request.user, 'privacy_profile') or not request.user.privacy_profile.telemetry_consent:
            return Response(
                {"detail": "Telemetry consent is required to submit feedback."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = ser.validated_data
        prediction = None
        pid = data.get("prediction_id")
        if pid is not None:
            prediction = CognitivePrediction.objects.filter(
                id=pid, session=session
            ).first()
            if prediction is None:
                return Response(
                    {"detail": "prediction_id does not match your active session."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        fb = HumanFeedback.objects.create(
            session=session,
            prediction=prediction,
            focus_score=data.get("focus_score"),
            fatigue_score=data.get("fatigue_score"),
            workload_score=data.get("workload_score"),
            confidence_score=data.get("confidence_score"),
            label_source=data.get("label_source", "self-report"),
            prompt_trigger_type=data.get("prompt_trigger_type", "random"),
            tab_switch_count=data.get("tab_switch_count", 0),
            prompt_response_delay_ms=data.get("prompt_response_delay_ms"),
            visibility_state=data.get("visibility_state", "visible"),
            features_snapshot=data["features_snapshot"],
            feature_schema_version=data.get("feature_schema_version", "v1.0")
        )
        return Response(
            {"status": "ok", "id": fb.id, "prediction_linked": prediction is not None},
            status=status.HTTP_201_CREATED,
        )
