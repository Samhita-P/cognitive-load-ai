#!/usr/bin/env python3
"""
Train RandomForest from JSONL (one JSON object per line).
Produce ml-service/models/rf_cognitive.joblib + rf_cognitive.meta.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.features.metric_keys import TRAINING_FEATURE_KEYS  # noqa: E402

LABELS = frozenset({"Focused", "Distracted", "Fatigued", "Normal", "Overloaded"})

def main() -> None:
    ap = argparse.ArgumentParser(description="Train RF cognitive classifier from JSONL export.")
    ap.add_argument("input", type=Path, help="JSONL file from export_feedback_dataset")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "models",
        help="Directory for rf_cognitive.joblib and rf_cognitive.meta.json",
    )
    args = ap.parse_args()

    try:
        text = args.input.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = args.input.read_text(encoding="utf-16")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))

    feat_rows: list[dict] = []
    y: list[str] = []
    for r in rows:
        lab = r.get("label")
        if lab not in LABELS:
            continue
        f = r.get("features")
        if not isinstance(f, dict):
            continue
        feat_rows.append({k: float(f.get(k) or 0.0) for k in TRAINING_FEATURE_KEYS})
        y.append(str(lab))

    if len(y) < 8:
        print("Need at least 8 labeled rows with valid features.", file=sys.stderr)
        sys.exit(1)
    if len(set(y)) < 2:
        print("Need at least two distinct labels in the export.", file=sys.stderr)
        sys.exit(1)

    X = pd.DataFrame(feat_rows)[TRAINING_FEATURE_KEYS]
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)
    print(f"Model trained. Accuracy on test set: {accuracy:.4f}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    model_p = args.out_dir / "rf_cognitive.joblib"
    meta_p = args.out_dir / "rf_cognitive.meta.json"
    joblib.dump(clf, model_p)
    
    meta_data = {
      "model_name": "rf_cognitive",
      "model_version": "v2_random_forest",
      "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
      "dataset_rows": len(y),
      "accuracy": round(accuracy, 4),
      "features": TRAINING_FEATURE_KEYS,
      "classes": [str(c) for c in clf.classes_]
    }
    
    meta_p.write_text(
        json.dumps(meta_data, indent=2),
        encoding="utf-8",
    )
    print("Wrote", model_p, "and", meta_p, file=sys.stderr)

if __name__ == "__main__":
    main()
