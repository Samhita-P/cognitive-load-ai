from django.core.management.base import BaseCommand
from django.utils import timezone
from gateway.models import CompressedTelemetry
from datetime import timedelta

class Command(BaseCommand):
    help = 'Cull raw telemetry data older than 30 days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of data to retain (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Deleting CompressedTelemetry older than {days} days ({cutoff_date})...")
        
        # Only delete raw telemetry, keep CognitiveSession, HumanFeedback, etc.
        # Actually, deleting CompressedTelemetry doesn't cascade to session.
        # Wait, the model is: CompressedTelemetry has ForeignKey to CognitiveSession
        # So deleting CompressedTelemetry just deletes those rows.
        queryset = CompressedTelemetry.objects.filter(timestamp__lt=cutoff_date)
        count, _ = queryset.delete()
        
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} telemetry records."))
