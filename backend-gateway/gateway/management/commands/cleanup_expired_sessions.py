from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from gateway.models import CognitiveSession
from gateway.session_manager import finalize_session
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Finds active sessions with no activity for > 30 mins and finalizes them.'

    def handle(self, *args, **options):
        timeout_threshold = timezone.now() - timedelta(minutes=30)
        
        expired_sessions = CognitiveSession.objects.filter(
            status='active',
            last_activity_at__lt=timeout_threshold
        )
        
        count = 0
        for session in expired_sessions:
            try:
                finalize_session(session.id, reason="timeout")
                count += 1
            except Exception as e:
                logger.error(f"Error finalizing session {session.id}: {e}")
                self.stderr.write(self.style.ERROR(f"Error finalizing session {session.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Successfully finalized {count} expired sessions.'))
