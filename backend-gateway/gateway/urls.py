from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, HumanFeedbackSubmitView
from .views_analytics import HistoricalAnalyticsView, UserBaselineView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('feedback/', HumanFeedbackSubmitView.as_view(), name='feedback_submit'),
    path('analytics/history/', HistoricalAnalyticsView.as_view(), name='analytics_history'),
    path('analytics/baseline/', UserBaselineView.as_view(), name='analytics_baseline'),
]
