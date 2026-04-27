"""Curated denied applicants for the demo's Citizen Lookup tab.

We surface a handful of denied applicants from the holdout set who illustrate
the bias patterns most clearly — a tier-3-city woman, a younger applicant from
a low-resource state, a worker with limited formal education, etc. Judges
clicking through the demo see real model decisions on real data; the names and
locations are the Indian-context overlay.
"""
from __future__ import annotations

import pandas as pd


def pick_demo_applicants(holdout: pd.DataFrame, n_per_archetype: int = 1) -> pd.DataFrame:
    """Return a small DataFrame of denied applicants suitable for the demo."""
    denied = holdout[holdout["pred_label"] == 0].copy()

    archetypes = []

    # Archetype 1: Female, tier-3, denied
    f_t3 = denied[
        (denied["sex"].str.strip() == "Female")
        & (denied["city_tier"] == "tier-3")
    ].sort_values("pred_proba", ascending=False)
    archetypes.append(("Tier-3 woman, denied", f_t3, n_per_archetype))

    # Archetype 2: Female, tier-2, with reasonable hours, denied
    f_t2 = denied[
        (denied["sex"].str.strip() == "Female")
        & (denied["city_tier"] == "tier-2")
        & (denied["hours_per_week"] >= 35)
    ].sort_values("pred_proba", ascending=False)
    archetypes.append(("Tier-2 woman, full-time, denied", f_t2, n_per_archetype))

    # Archetype 3: Younger applicant (18-25), denied
    young = denied[denied["age_band"] == "18-25"].sort_values(
        "pred_proba", ascending=False
    )
    archetypes.append(("Young applicant (18-25), denied", young, n_per_archetype))

    # Archetype 4: Low formal education
    low_ed = denied[denied["education_band"] == "Below-HS"].sort_values(
        "pred_proba", ascending=False
    )
    archetypes.append(("Limited formal education, denied", low_ed, n_per_archetype))

    # Archetype 5: Self-employed-ish (no formal employer)
    self_emp = denied[
        denied["occupation"].astype(str).isin(["Other-service", "Handlers-cleaners",
                                               "Farming-fishing", "Priv-house-serv"])
    ].sort_values("pred_proba", ascending=False)
    archetypes.append(("Service-sector worker, denied", self_emp, n_per_archetype))

    rows = []
    for label, frame, k in archetypes:
        if frame.empty:
            continue
        sub = frame.head(k).copy()
        sub["archetype"] = label
        rows.append(sub)

    if not rows:
        return denied.head(5).assign(archetype="Denied applicant")

    out = pd.concat(rows, ignore_index=False)
    out = out.drop_duplicates(subset=["display_id"]).reset_index(drop=True)
    return out
