from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

class DatasetAuditor:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def check_nulls(self) -> Dict[str, int]:
        nulls = self.df.isnull().sum()
        return nulls[nulls > 0].to_dict()
        
    def analyze_contamination(self) -> Dict[str, Any]:
        """Returns contamination statistics and rejection rate if applied."""
        total = len(self.df)
        if total == 0:
            return {"total_rows": 0, "rejection_rate": 0.0}
            
        valid = self.df[
            (self.df["confidence_score"] >= 3) &
            (self.df["tab_switch_count"] <= 2) &
            (self.df["visibility_state"] == "visible") &
            (self.df["prompt_response_delay_ms"] <= 10000)
        ]
        
        dropped = total - len(valid)
        rejection_rate = dropped / total
        
        return {
            "total_rows": total,
            "usable_rows": len(valid),
            "rejection_rate": rejection_rate
        }
        
    def analyze_user_skew(self) -> Dict[str, Any]:
        """Checks for massive user skew (e.g. one user dominating labels)."""
        if "user_id" not in self.df.columns or self.df.empty:
            return {}
            
        counts = self.df["user_id"].value_counts(normalize=True)
        max_share = counts.iloc[0] if not counts.empty else 0.0
        
        return {
            "unique_users": len(counts),
            "max_single_user_share": max_share,
            "top_users_share": counts.head(5).to_dict()
        }
        
    def check_label_balance(self) -> Dict[str, float]:
        """Returns max class ratio for each target to detect severe imbalance."""
        imbalance = {}
        targets = ["focus_score", "fatigue_score", "workload_score"]
        for target in targets:
            if target in self.df.columns and not self.df.empty:
                val_counts = self.df[target].value_counts(normalize=True)
                imbalance[target] = val_counts.iloc[0] if not val_counts.empty else 0.0
        return imbalance

    def run_full_audit(self) -> Dict[str, Any]:
        return {
            "nulls": self.check_nulls(),
            "contamination": self.analyze_contamination(),
            "user_skew": self.analyze_user_skew(),
            "label_imbalance": self.check_label_balance()
        }
