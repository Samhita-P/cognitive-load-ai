from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)

from .views import (
    RegisterView,
    HumanFeedbackSubmitView,
    WSTicketView,
    demo_login,
    trigger_demo
)

from .views_analytics import (
    HistoricalAnalyticsView,
    UserBaselineView
)

from .views_privacy import (
    PrivacyConsentView,
    PrivacyTelemetryDeleteView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('auth/ws-ticket/', WSTicketView.as_view(), name='ws_ticket'),

    path('feedback/', HumanFeedbackSubmitView.as_view(), name='feedback_submit'),

    path('analytics/history/', HistoricalAnalyticsView.as_view(), name='analytics_history'),
    path('analytics/baseline/', UserBaselineView.as_view(), name='analytics_baseline'),

    path('privacy/consent/', PrivacyConsentView.as_view(), name='privacy_consent'),
    path('privacy/telemetry/', PrivacyTelemetryDeleteView.as_view(), name='privacy_telemetry'),

    path('demo/trigger/', trigger_demo, name='demo_trigger'),
    path("auth/demo-login/", demo_login),
]