import json

from django.core.management.base import BaseCommand

from gateway.models import HumanFeedback


class Command(BaseCommand):
    help = "Export HumanFeedback rows as JSONL for ml-service/scripts/train_rf.py"

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-keys",
            type=int,
            default=3,
            help="Minimum keys in features_snapshot to include a row.",
        )

    def handle(self, *args, **options):
        min_keys = options["min_keys"]
        qs = HumanFeedback.objects.select_related("prediction").all().order_by("id")
        count = 0
        for fb in qs.iterator(chunk_size=500):
            snap = fb.features_snapshot
            if not isinstance(snap, dict) or len(snap) < min_keys:
                continue
            row = {
                "label": fb.user_label,
                "features": snap,
                "prediction_id": fb.prediction_id,
                "model_state": fb.prediction.predicted_state
                if fb.prediction_id
                else None,
            }
            self.stdout.write(json.dumps(row, separators=(",", ":")))
            count += 1
        self.stderr.write(self.style.NOTICE(f"Exported {count} rows to stdout (JSONL).\n"))
