from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView

from .models import CognitivePrediction, CognitiveSession, HumanFeedback
from .serializers import HumanFeedbackCreateSerializer


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
            user_label=data["human_label"],
            features_snapshot=data["features_snapshot"],
        )
        return Response(
            {"status": "ok", "id": fb.id, "prediction_linked": prediction is not None},
            status=status.HTTP_201_CREATED,
        )
