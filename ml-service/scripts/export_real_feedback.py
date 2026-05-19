#!/usr/bin/env python3
"""
export_real_feedback.py

Connects to the Neon PostgreSQL database via Django ORM to extract
the real HumanFeedback records, joined with their precise features_snapshot.

Produces raw_feedback.parquet, raw_feedback.csv, and export_metadata.json.
"""
import os
import sys
import argparse
import datetime
import json
from pathlib import Path
from packaging.version import Version

import pandas as pd

# Setup Django environment
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend-gateway"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from gateway.models import HumanFeedback

def export_data(min_date: str, output_path: Path, fmt: str):
    print(f"Connecting to database to extract feedback since {min_date}...")
    
    dt_filter = datetime.datetime.fromisoformat(min_date)
    # Filter for NOT NULL focus_score (Phase 1+ only)
    qs = HumanFeedback.objects.filter(
        timestamp__gte=dt_filter,
        focus_score__isnull=False
    ).select_related('session', 'session__user')
    
    rows = []
    for fb in qs:
        # Schema version guard
        schema_ver = fb.feature_schema_version or "1.0"
        schema_ver = schema_ver.lstrip('v')
        try:
            if Version(schema_ver) < Version("1.1"):
                continue
        except Exception:
            continue
            
        # The snapshot is already aligned perfectly to the label time
        feats = fb.features_snapshot or {}
        
        row = {
            "feedback_id": fb.id,
            "session_id": fb.session.id,
            "user_id": fb.session.user.id,
            "timestamp": fb.timestamp.isoformat(),
            
            # Target Variables
            "focus_score": fb.focus_score,
            "fatigue_score": fb.fatigue_score,
            "workload_score": fb.workload_score,
            "confidence_score": fb.confidence_score,
            
            # Contamination Metadata
            "tab_switch_count": fb.tab_switch_count,
            "prompt_response_delay_ms": fb.prompt_response_delay_ms,
            "visibility_state": fb.visibility_state,
            "label_source": fb.label_source,
            "prompt_trigger_type": fb.prompt_trigger_type,
            "feature_schema_version": fb.feature_schema_version,
        }
        
        # Flatten features directly into the row
        for k, v in feats.items():
            row[k] = v
            
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    print(f"Extracted {len(df)} rows.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save datasets
    base_name = output_path.stem
    out_dir = output_path.parent
    
    parquet_path = out_dir / f"{base_name}.parquet"
    csv_path = out_dir / f"{base_name}.csv"
    meta_path = out_dir / "export_metadata.json"
    
    if len(df) > 0:
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
    else:
        print("Warning: Exported 0 rows. Output files will be empty.")
        # Create empty files so subsequent steps don't crash
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        
    # Calculate Staleness
    oldest_ts = df["timestamp"].min() if not df.empty else None
    latest_ts = df["timestamp"].max() if not df.empty else None
    coverage_days = 0
    if oldest_ts and latest_ts:
        t1 = datetime.datetime.fromisoformat(oldest_ts)
        t2 = datetime.datetime.fromisoformat(latest_ts)
        coverage_days = (t2 - t1).days

    # Write metadata
    metadata = {
        "record_count": len(df),
        "export_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "feature_schema_version": "1.1",
        "source_db": "django_default",
        "staleness": {
            "oldest_timestamp": oldest_ts,
            "latest_timestamp": latest_ts,
            "coverage_days": coverage_days
        },
        "filters_applied": {
            "min_date": min_date,
            "require_focus_score_not_null": True,
            "min_schema_version": "1.1"
        }
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved to {parquet_path}")
    print(f"Saved to {csv_path}")
    print(f"Saved metadata to {meta_path}")

def main():
    parser = argparse.ArgumentParser(description="Export raw HumanFeedback dataset.")
    parser.add_argument("--min-date", type=str, default="2024-01-01", help="YYYY-MM-DD")
    parser.add_argument("--format", type=str, default="parquet", help="parquet or csv")
    parser.add_argument("--output", type=str, default=str(ROOT_DIR / "ml-service" / "data" / "raw_feedback.parquet"))
    
    args = parser.parse_args()
    
    export_data(
        min_date=args.min_date,
        output_path=Path(args.output),
        fmt=args.format
    )

if __name__ == "__main__":
    main()
