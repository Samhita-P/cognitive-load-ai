#!/usr/bin/env python3
"""
train_benchmark.py
Phase 2.6: Data Governance Hardened Training Pipeline

Implements strict sufficiency gates, dual-mode evaluation (Temporal + User Holdout),
and native MLflow abort/success lifecycle logging.
"""
from __future__ import annotations

import argparse
import json
import sys
import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import joblib

import mlflow
from sklearn.model_selection import TimeSeriesSplit, GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, cohen_kappa_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.features.metric_keys import TRAINING_FEATURE_KEYS

# --- STRICT GOVERNANCE THRESHOLDS ---
MIN_TOTAL_ROWS = 1000
MIN_UNIQUE_USERS = 30
MIN_SESSIONS = 100
MIN_ROWS_PER_TARGET_BUCKET = 30
MAX_SINGLE_USER_SHARE = 0.25
MAX_CLASS_RATIO = 0.70

def abort_training(reason: str):
    print(f"ABORTING TRAINING: {reason}", file=sys.stderr)
    mlflow.set_tag("status", "aborted")
    mlflow.set_tag("abort_reason", reason)
    mlflow.end_run()
    sys.exit(1)

def run_sufficiency_gate(df: pd.DataFrame):
    if len(df) < MIN_TOTAL_ROWS:
        abort_training(f"insufficient_rows (Got {len(df)}, need {MIN_TOTAL_ROWS})")
        
    if df["user_id"].nunique() < MIN_UNIQUE_USERS:
        abort_training(f"insufficient_users (Got {df['user_id'].nunique()}, need {MIN_UNIQUE_USERS})")
        
    if df["session_id"].nunique() < MIN_SESSIONS:
        abort_training(f"insufficient_sessions (Got {df['session_id'].nunique()}, need {MIN_SESSIONS})")
        
    user_counts = df["user_id"].value_counts(normalize=True)
    if user_counts.iloc[0] > MAX_SINGLE_USER_SHARE:
        abort_training(f"skew_failure (Top user has {user_counts.iloc[0]*100:.1f}% share, max is {MAX_SINGLE_USER_SHARE*100:.1f}%)")

def run_balance_gate(df: pd.DataFrame, targets: list[str]):
    for target in targets:
        # Check imbalance
        val_counts = df[target].value_counts(normalize=True)
        max_ratio = val_counts.iloc[0] if not val_counts.empty else 0
        if max_ratio > MAX_CLASS_RATIO:
            abort_training(f"label_imbalance (Target {target} max class ratio {max_ratio:.2f} > {MAX_CLASS_RATIO})")
            
        # Check buckets
        abs_counts = df[target].value_counts()
        if len(abs_counts) < 3 or abs_counts.min() < MIN_ROWS_PER_TARGET_BUCKET:
            abort_training(f"insufficient_buckets (Target {target} lacks diversity or bucket size < {MIN_ROWS_PER_TARGET_BUCKET})")

def evaluate_predictions(y_true, y_pred, targets):
    results = {}
    for i, target in enumerate(targets):
        yt = y_true[target]
        yp = y_pred[:, i]
        
        yp_rounded = np.clip(np.round(yp), 1, 5)
        mae = mean_absolute_error(yt, yp)
        qwk = cohen_kappa_score(yt, yp_rounded, weights="quadratic")
        rmse = np.sqrt(mean_squared_error(yt, yp))
        results[target] = {"mae": mae, "qwk": qwk, "rmse": rmse}
    return results

def train_and_eval_pipeline(X, y, groups, mode="A"):
    targets = y.columns.tolist()
    
    if mode == "A":
        # Mode A: Temporal Generalization (predict future)
        splitter = TimeSeriesSplit(n_splits=5)
    else:
        # Mode B: User Holdout (cross-user generalization)
        splitter = GroupKFold(n_splits=5)
        
    reg_maes, cls_maes = [], []
    
    for train_idx, test_idx in splitter.split(X, y, groups=groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train MultiOutput Regression
        reg = MultiOutputRegressor(RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42))
        reg.fit(X_train, y_train)
        y_pred_reg = reg.predict(X_test)
        reg_eval = evaluate_predictions(y_test, y_pred_reg, targets)
        reg_maes.append(np.mean([reg_eval[t]["mae"] for t in targets]))
        
        # Train Independent Classifiers
        y_pred_cls = np.zeros_like(y_pred_reg)
        for i, target in enumerate(targets):
            cls = RidgeClassifier(class_weight="balanced")
            cls.fit(X_train, y_train[target])
            y_pred_cls[:, i] = cls.predict(X_test)
        cls_eval = evaluate_predictions(y_test, y_pred_cls, targets)
        cls_maes.append(np.mean([cls_eval[t]["mae"] for t in targets]))
        
    return np.mean(reg_maes), np.mean(cls_maes)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=ROOT / "data" / "raw_feedback.parquet")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "models")
    args = ap.parse_args()

    mlflow.set_experiment("Phase_2.8_Benchmark")
    mlflow.start_run(run_name="Benchmark_Gate")

    if not args.input.exists():
        abort_training("missing_data_file")

    df = pd.read_parquet(args.input)
    mlflow.log_metric("initial_rows", len(df))
    
    # Missing targets check
    targets = ["focus_score", "fatigue_score", "workload_score"]
    if df[targets].isnull().all().all():
        abort_training("null_targets")
    
    # Clean data
    df = df.dropna(subset=targets).copy()
    for t in targets:
        df[t] = df[t].astype(int)

    # 1. Run Gates
    run_sufficiency_gate(df)
    run_balance_gate(df, targets)

    # 2. Extract
    X = df[TRAINING_FEATURE_KEYS]
    y = df[targets]
    groups = df["user_id"]
    
    # 3. Dual Evaluation
    print("Running Mode A: Temporal Generalization (TimeSeriesSplit)...")
    reg_mae_a, cls_mae_a = train_and_eval_pipeline(X, y, groups, mode="A")
    mlflow.log_metrics({"mode_A_reg_mae": reg_mae_a, "mode_A_cls_mae": cls_mae_a})
    
    print("Running Mode B: User Holdout Generalization (GroupKFold)...")
    reg_mae_b, cls_mae_b = train_and_eval_pipeline(X, y, groups, mode="B")
    mlflow.log_metrics({"mode_B_reg_mae": reg_mae_b, "mode_B_cls_mae": cls_mae_b})

    # Decide Champion on Mode B (User Generalization is harder/more robust)
    if reg_mae_b <= cls_mae_b:
        champion_name = "rf_multioutput_champion"
        mlflow.set_tag("champion", "Regression")
    else:
        champion_name = "ridge_independent_champion"
        mlflow.set_tag("champion", "Classification")

    mlflow.set_tag("status", "success")
    mlflow.end_run()
    print(f"\\nPipeline Succeeded! Champion: {champion_name}")

if __name__ == "__main__":
    main()
