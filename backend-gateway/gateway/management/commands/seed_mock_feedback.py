from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gateway.models import CognitiveSession, HumanFeedback
import random

class Command(BaseCommand):
    help = "Seed database with synthetic HumanFeedback to bootstrap the ML model."

    def handle(self, *args, **options):
        # Create or get a dummy user
        user, _ = User.objects.get_or_create(username='ml_bootstrap_user', email='ml@example.com')
        user.set_password('password123')
        user.save()

        # Create a dummy session
        session = CognitiveSession.objects.create(user=user)

        labels = ['Focused', 'Distracted', 'Fatigued', 'Normal']
        
        # We need to generate realistic feature snapshots for each state
        # Features: idle_ratio, activity_density, error_rate, max_pause_ms, avg_mouse_variance, total_keystrokes

        mock_data = []

        for _ in range(50):
            # Focused
            mock_data.append({
                'label': 'Focused',
                'features': {
                    'idle_ratio': random.uniform(0.0, 0.2),
                    'activity_density': random.uniform(4.0, 8.0),
                    'error_rate': random.uniform(0.0, 0.05),
                    'max_pause_ms': random.uniform(200, 1500),
                    'avg_mouse_variance': random.uniform(10.0, 50.0),
                    'total_keystrokes': random.randint(30, 80)
                }
            })
            
            # Fatigued
            mock_data.append({
                'label': 'Fatigued',
                'features': {
                    'idle_ratio': random.uniform(0.5, 0.9),
                    'activity_density': random.uniform(0.5, 2.0),
                    'error_rate': random.uniform(0.1, 0.3),
                    'max_pause_ms': random.uniform(3000, 10000),
                    'avg_mouse_variance': random.uniform(200.0, 500.0), # Erratic mouse movements
                    'total_keystrokes': random.randint(5, 20)
                }
            })
            
            # Distracted
            mock_data.append({
                'label': 'Distracted',
                'features': {
                    'idle_ratio': random.uniform(0.3, 0.6),
                    'activity_density': random.uniform(1.0, 5.0),
                    'error_rate': random.uniform(0.05, 0.15),
                    'max_pause_ms': random.uniform(1500, 5000),
                    'avg_mouse_variance': random.uniform(100.0, 300.0),
                    'total_keystrokes': random.randint(15, 40)
                }
            })

            # Normal
            mock_data.append({
                'label': 'Normal',
                'features': {
                    'idle_ratio': random.uniform(0.2, 0.4),
                    'activity_density': random.uniform(2.0, 4.0),
                    'error_rate': random.uniform(0.02, 0.08),
                    'max_pause_ms': random.uniform(1000, 3000),
                    'avg_mouse_variance': random.uniform(50.0, 150.0),
                    'total_keystrokes': random.randint(20, 50)
                }
            })

        for data in mock_data:
            HumanFeedback.objects.create(
                session=session,
                user_label=data['label'],
                features_snapshot=data['features']
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(mock_data)} synthetic feedback records!"))
