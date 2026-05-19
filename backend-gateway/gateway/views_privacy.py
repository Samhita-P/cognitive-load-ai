from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import UserPrivacyProfile, PrivacyAuditLog, CognitiveSession

class PrivacyConsentView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profile, created = UserPrivacyProfile.objects.get_or_create(user=request.user)
        return Response({
            "telemetry_consent": profile.telemetry_consent,
            "privacy_mode": profile.privacy_mode,
            "consent_version": profile.consent_version,
            "consent_timestamp": profile.consent_timestamp,
        })

    def post(self, request):
        profile, created = UserPrivacyProfile.objects.get_or_create(user=request.user)
        
        old_consent = profile.telemetry_consent
        old_privacy_mode = profile.privacy_mode
        
        telemetry_consent = request.data.get("telemetry_consent")
        privacy_mode = request.data.get("privacy_mode")
        
        updated = False
        
        if telemetry_consent is not None and telemetry_consent != old_consent:
            profile.telemetry_consent = telemetry_consent
            profile.consent_timestamp = timezone.now()
            event = 'CONSENT_GRANTED' if telemetry_consent else 'CONSENT_REVOKED'
            PrivacyAuditLog.objects.create(user=request.user, event=event)
            updated = True
            
            # If consent revoked, forcefully disconnect existing WebSockets
            if not telemetry_consent:
                # Set a revocation flag in cache for fast lookup in consumers
                from django.core.cache import cache
                cache.set(f"privacy_revoked_{request.user.id}", True, timeout=3600)
                
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{request.user.id}",
                        {"type": "force_disconnect"}
                    )
        
        if privacy_mode is not None and privacy_mode != old_privacy_mode:
            profile.privacy_mode = privacy_mode
            event = 'PRIVACY_MODE_ENABLED' if privacy_mode else 'PRIVACY_MODE_DISABLED'
            PrivacyAuditLog.objects.create(user=request.user, event=event)
            updated = True
            
        if updated:
            profile.save()
            
        return Response({
            "status": "ok",
            "telemetry_consent": profile.telemetry_consent,
            "privacy_mode": profile.privacy_mode
        })


class PrivacyTelemetryDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        profile, created = UserPrivacyProfile.objects.get_or_create(user=request.user)
        profile.deletion_requested_at = timezone.now()
        profile.save()
        
        PrivacyAuditLog.objects.create(user=request.user, event='DELETION_REQUESTED')
        
        # Hard Cascade Delete of all telemetry via CognitiveSession cascade
        sessions = CognitiveSession.objects.filter(user=request.user)
        deleted_count, _ = sessions.delete()
        
        PrivacyAuditLog.objects.create(user=request.user, event='DELETION_COMPLETED')
        
        return Response({
            "status": "ok",
            "message": "All identifying telemetry has been hard-deleted.",
            "sessions_deleted": deleted_count
        })
