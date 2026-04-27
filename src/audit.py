"""Slice-level fairness audit using Fairlearn.

Computes:
  - Selection rate (% of applicants approved) per slice
  - Accuracy per slice
  - Demographic Parity Difference (DPD)
  - Equalized Odds Difference (EOD)
  - False positive / negative rates per slice
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from fairlearn.metrics import (
    MetricFrame,
    demographic_parity_difference,
    equalized_odds_difference,
    false_negative_rate,
    false_positive_rate,
    selection_rate,
)
from sklearn.metrics import accuracy_score


@dataclass
class SliceReport:
    sensitive_feature: str
    by_group: pd.DataFrame  # rows = groups, cols = metrics
    overall: dict[str, float]
    dpd: float
    eod: float


def audit_slice(
    holdout: pd.DataFrame, sensitive_feature: str
) -> SliceReport:
    """Run the fairness audit on a single sensitive column."""
    if sensitive_feature not in holdout.columns:
        raise ValueError(f"unknown sensitive feature: {sensitive_feature}")
    y_true = holdout["true_label"].values
    y_pred = holdout["pred_label"].values
    sf = holdout[sensitive_feature].astype(str).values
    metrics = {
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
    }
    mf = MetricFrame(
        metrics=metrics,
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sf,
    )
    by_group = mf.by_group.copy()
    by_group["count"] = pd.Series(sf).value_counts().reindex(by_group.index).values
    dpd = float(
        demographic_parity_difference(
            y_true=y_true, y_pred=y_pred, sensitive_features=sf
        )
    )
    eod = float(
        equalized_odds_difference(
            y_true=y_true, y_pred=y_pred, sensitive_features=sf
        )
    )
    return SliceReport(
        sensitive_feature=sensitive_feature,
        by_group=by_group,
        overall={k: float(v) for k, v in mf.overall.items()},
        dpd=dpd,
        eod=eod,
    )


def audit_all(holdout: pd.DataFrame) -> dict[str, SliceReport]:
    """Run the audit across the standard sensitive columns."""
    sensitive = ["sex", "race", "age_band", "education_band", "city_tier"]
    reports = {}
    for col in sensitive:
        if col in holdout.columns:
            reports[col] = audit_slice(holdout, col)
    return reports


def disparity_summary(reports: dict[str, SliceReport]) -> pd.DataFrame:
    """One-row-per-slice summary suitable for the dashboard heatmap."""
    rows = []
    for name, rep in reports.items():
        rows.append(
            {
                "sensitive_feature": name,
                "demographic_parity_difference": rep.dpd,
                "equalized_odds_difference": rep.eod,
                "max_selection_rate": float(rep.by_group["selection_rate"].max()),
                "min_selection_rate": float(rep.by_group["selection_rate"].min()),
                "n_groups": int(len(rep.by_group)),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "demographic_parity_difference", ascending=False
    )
