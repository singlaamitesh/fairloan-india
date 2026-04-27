"""Train a LightGBM credit-eligibility classifier on the UCI Adult benchmark.

Run: ``python -m src.train``
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from . import data_loader as dl

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def encode_categoricals(
    X: pd.DataFrame, encoders: dict[str, LabelEncoder] | None = None
) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    """Label-encode categorical columns in place; return the encoders."""
    X = X.copy()
    encoders = encoders or {}
    for col in dl.CATEGORICAL_COLS:
        le = encoders.get(col)
        if le is None:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le
        else:
            seen = set(le.classes_)
            X[col] = X[col].astype(str).map(
                lambda v, _seen=seen, _le=le: _le.transform([v])[0] if v in _seen else -1
            )
    return X, encoders


def train_model(seed: int = 42) -> dict:
    """Train, evaluate, and persist the classifier.

    Saves: model, encoders, holdout predictions, training metadata.
    """
    t0 = time.time()
    df = dl.load_adult()
    X, y = dl.split_xy(df)
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.25, random_state=seed, stratify=y
    )
    X_train_enc, encoders = encode_categoricals(X_train)
    X_test_enc, _ = encode_categoricals(X_test, encoders)
    model = lgb.LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=63,
        random_state=seed,
        verbosity=-1,
    )
    model.fit(X_train_enc, y_train)
    y_pred = model.predict(X_test_enc)
    y_proba = model.predict_proba(X_test_enc)[:, 1]
    accuracy = float(accuracy_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_proba))
    feature_importance = dict(
        zip(X_train_enc.columns, model.feature_importances_.tolist())
    )
    holdout = df.loc[idx_test].copy()
    holdout["pred_label"] = y_pred
    holdout["pred_proba"] = y_proba
    holdout["true_label"] = y_test.values
    joblib.dump(
        {"model": model, "encoders": encoders, "feature_cols": X_train_enc.columns.tolist()},
        ARTIFACT_DIR / "model.pkl",
    )
    holdout.to_parquet(ARTIFACT_DIR / "holdout.parquet", index=False)
    metadata = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": accuracy,
        "auc": auc,
        "feature_importance": feature_importance,
        "elapsed_s": round(time.time() - t0, 2),
        "seed": seed,
    }
    (ARTIFACT_DIR / "training_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )
    return metadata


def load_artifacts() -> tuple[object, dict, list[str], pd.DataFrame, dict]:
    """Load trained model + encoders + holdout dataframe + metadata."""
    bundle = joblib.load(ARTIFACT_DIR / "model.pkl")
    holdout = pd.read_parquet(ARTIFACT_DIR / "holdout.parquet")
    metadata = json.loads((ARTIFACT_DIR / "training_metadata.json").read_text())
    return bundle["model"], bundle["encoders"], bundle["feature_cols"], holdout, metadata


if __name__ == "__main__":
    info = train_model()
    print(json.dumps(info, indent=2))
