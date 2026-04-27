"""Load UCI Adult Income (the universal fairness benchmark) and recast it
into an Indian credit-eligibility framing.

The Adult dataset is the most-cited benchmark in algorithmic fairness research.
We use it because:
  - It's the standard fairness benchmark every reviewer recognizes.
  - It has demographic features (sex, race, age, education) with documented disparities.
  - It's directly downloadable from the UCI archive (no Kaggle auth, no rate limit).
  - The income > 50K target maps cleanly onto a binary "loan-eligible" decision.

We add an Indian-context layer on top: applicants get Indian names, an Indian state,
a tier-1/2/3 city classification, and incomes shown in INR (₹). The audit
methodology is identical; the Indian framing is what the demo and counterfactuals
present to the user.
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ADULT_TRAIN_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
)
ADULT_TEST_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.test"
)

COLUMN_NAMES = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education_num",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "native_country",
    "income",
]

NUMERIC_COLS = [
    "age",
    "fnlwgt",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
]
CATEGORICAL_COLS = [
    "workclass",
    "education",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "native_country",
]
SENSITIVE_COLS = ["sex", "race", "age_band"]
TARGET_COL = "loan_eligible"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    with urllib.request.urlopen(url, timeout=30) as resp:
        dest.write_bytes(resp.read())


def _read_adult(path: Path, skip_first: bool = False) -> pd.DataFrame:
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    if skip_first:
        raw = "\n".join(raw.splitlines()[1:])
    df = pd.read_csv(
        io.StringIO(raw),
        header=None,
        names=COLUMN_NAMES,
        skipinitialspace=True,
        na_values=["?"],
    )
    df = df.dropna().reset_index(drop=True)
    df["income"] = df["income"].str.rstrip(".").str.strip()
    df[TARGET_COL] = (df["income"] == ">50K").astype(int)
    df = df.drop(columns=["income"])
    df["age_band"] = pd.cut(
        df["age"],
        bins=[0, 25, 35, 50, 65, 200],
        labels=["18-25", "26-35", "36-50", "51-65", "65+"],
    ).astype(str)
    df["education_band"] = pd.cut(
        df["education_num"],
        bins=[0, 9, 12, 14, 25],
        labels=["Below-HS", "HS", "Some-College", "College+"],
    ).astype(str)
    return df


def load_adult(force_download: bool = False) -> pd.DataFrame:
    """Download and combine the UCI Adult train + test sets, return a clean DataFrame.

    The combined set is ~45K rows after removing missing values. Target is
    ``loan_eligible`` (1 if original income > 50K, 0 otherwise).
    """
    train_path = DATA_DIR / "adult.data"
    test_path = DATA_DIR / "adult.test"
    if force_download:
        train_path.unlink(missing_ok=True)
        test_path.unlink(missing_ok=True)
    _download(ADULT_TRAIN_URL, train_path)
    _download(ADULT_TEST_URL, test_path)
    train = _read_adult(train_path, skip_first=False)
    test = _read_adult(test_path, skip_first=True)
    df = pd.concat([train, test], ignore_index=True)
    df = _add_indian_context(df)
    return df


# Indian-context overlay
INDIAN_FEMALE_FIRST = [
    "Sarita", "Aisha", "Priya", "Lakshmi", "Meena", "Kavita", "Rekha",
    "Sunita", "Anjali", "Neha", "Divya", "Pooja", "Shruti", "Geeta",
    "Aarti", "Smita", "Asha", "Vimla", "Renu", "Suman",
]
INDIAN_MALE_FIRST = [
    "Rohan", "Arjun", "Vikram", "Ravi", "Suresh", "Manoj", "Dinesh",
    "Karan", "Ajay", "Sanjay", "Rahul", "Amit", "Deepak", "Mohan",
    "Naveen", "Prakash", "Rajesh", "Sandeep", "Vivek", "Yash",
]
INDIAN_LAST = [
    "Sharma", "Verma", "Patel", "Reddy", "Iyer", "Kumar", "Singh",
    "Khan", "Banerjee", "Das", "Nair", "Pillai", "Rao", "Mehta",
    "Joshi", "Gupta", "Yadav", "Choudhary", "Naik", "Bhat",
]
INDIAN_STATES_TIER = {
    "Maharashtra": "tier-1", "Delhi": "tier-1", "Karnataka": "tier-1",
    "Tamil Nadu": "tier-1", "Telangana": "tier-1", "Gujarat": "tier-1",
    "West Bengal": "tier-2", "Uttar Pradesh": "tier-2", "Punjab": "tier-2",
    "Kerala": "tier-2", "Rajasthan": "tier-2", "Andhra Pradesh": "tier-2",
    "Bihar": "tier-3", "Odisha": "tier-3", "Madhya Pradesh": "tier-3",
    "Jharkhand": "tier-3", "Assam": "tier-3", "Chhattisgarh": "tier-3",
}
USD_TO_INR = 83.0


def _add_indian_context(df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """Add Indian names, state, tier-classification, and INR income bands.

    The mapping is a transparent overlay for the dashboard's Indian framing.
    The audit and modeling still run on the original UCI features.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    states = list(INDIAN_STATES_TIER.keys())
    state_arr = rng.choice(states, size=n)
    df = df.copy()
    df["state"] = state_arr
    df["city_tier"] = df["state"].map(INDIAN_STATES_TIER)
    first_names = np.where(
        df["sex"].str.strip() == "Female",
        rng.choice(INDIAN_FEMALE_FIRST, size=n),
        rng.choice(INDIAN_MALE_FIRST, size=n),
    )
    last_names = rng.choice(INDIAN_LAST, size=n)
    df["display_name"] = [f"{f} {l}" for f, l in zip(first_names, last_names)]
    df["estimated_monthly_income_inr"] = (
        np.where(df[TARGET_COL] == 1, 65000, 22000)
        + rng.integers(-5000, 8000, size=n)
    )
    df["display_id"] = [f"FL-{i:06d}" for i in range(n)]
    return df


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) where X holds modeling features and y is the target."""
    feature_cols = NUMERIC_COLS + CATEGORICAL_COLS
    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()
    return X, y
