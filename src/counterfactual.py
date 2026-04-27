"""Generate vernacular counterfactual explanations for denied applicants.

Pipeline:
  1. Search the candidate space of single-feature changes that flip the
     prediction from denied to approved.
  2. Validate each change against the actual classifier (no hallucinated
     fixes — Gemini only sees changes that we have proven flip the model).
  3. Pass the validated change + applicant context to Gemini to render an
     empathetic 2-3 sentence explanation in the requested language.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import data_loader as dl

LANG_MAP = {
    "english": "English",
    "hindi": "Hindi (Devanagari script)",
    "tamil": "Tamil (Tamil script)",
    "bengali": "Bengali (Bengali script)",
}

NUMERIC_FLIP_DELTAS = {
    "education_num": [1, 2, 3, 4],
    "hours_per_week": [5, 10, 15],
    "capital_gain": [1000, 5000, 10000],
    "age": [3, 5, 10],
}


@dataclass
class Counterfactual:
    feature: str
    original_value: object
    proposed_value: object
    proposed_proba: float
    explanation_human: str  # short English description of the change


def encode_for_model(applicant_row: pd.Series, encoders: dict, feature_cols: list[str]) -> pd.DataFrame:
    """Encode a single applicant row into the model's feature space."""
    vals = {}
    for col in feature_cols:
        v = applicant_row[col]
        if col in dl.CATEGORICAL_COLS:
            le = encoders[col]
            v = le.transform([str(v)])[0] if str(v) in set(le.classes_) else -1
        vals[col] = v
    return pd.DataFrame([vals])


def find_counterfactuals(
    applicant: pd.Series,
    model,
    encoders: dict,
    feature_cols: list[str],
    max_results: int = 3,
) -> list[Counterfactual]:
    """Try single-feature changes; keep ones that flip the prediction."""
    base_enc = encode_for_model(applicant, encoders, feature_cols)
    base_proba = float(model.predict_proba(base_enc)[0, 1])
    candidates: list[Counterfactual] = []

    # numeric features: try increasing
    for col, deltas in NUMERIC_FLIP_DELTAS.items():
        if col not in feature_cols:
            continue
        original = applicant[col]
        for d in deltas:
            new_val = original + d
            trial = applicant.copy()
            trial[col] = new_val
            enc = encode_for_model(trial, encoders, feature_cols)
            p = float(model.predict_proba(enc)[0, 1])
            if p >= 0.5:
                desc = _describe_numeric_change(col, original, new_val)
                candidates.append(
                    Counterfactual(col, original, new_val, p, desc)
                )
                break  # smallest delta that works

    # categorical: education, occupation, marital_status — try each level
    cat_to_try = ["education", "occupation", "marital_status"]
    for col in cat_to_try:
        if col not in encoders:
            continue
        le = encoders[col]
        original = applicant[col]
        best = None
        for level in le.classes_:
            if level == original:
                continue
            trial = applicant.copy()
            trial[col] = level
            enc = encode_for_model(trial, encoders, feature_cols)
            p = float(model.predict_proba(enc)[0, 1])
            if p >= 0.5 and (best is None or p > best.proposed_proba):
                desc = _describe_categorical_change(col, original, level)
                best = Counterfactual(col, original, level, p, desc)
        if best is not None:
            candidates.append(best)

    candidates.sort(key=lambda c: c.proposed_proba, reverse=True)
    return candidates[:max_results]


def _describe_numeric_change(col: str, old, new) -> str:
    if col == "education_num":
        return f"{int(new - old)} more year(s) of formal education"
    if col == "hours_per_week":
        return f"working {int(new - old)} more hour(s) per week"
    if col == "capital_gain":
        return f"₹{int((new - old) * 83):,} more in declared annual capital gains"
    if col == "age":
        return f"applying {int(new - old)} years later"
    return f"{col}: {old} → {new}"


def _describe_categorical_change(col: str, old, new) -> str:
    if col == "education":
        return f"upgrading education from '{old}' to '{new}'"
    if col == "occupation":
        return f"shifting occupation from '{old}' to '{new}'"
    if col == "marital_status":
        return f"a different marital status ('{new}')"
    return f"{col}: {old} → {new}"


SYSTEM_PROMPT = """You are FairLoan India, a public-interest assistant that explains
algorithmic loan denials to Indian applicants in their own language. You speak
warmly, plainly, and with respect. Never blame the applicant. Always frame the
counterfactual as 'the model would have approved you if X' — never 'you should
have done X.' Keep responses to 2-4 short sentences. Use the rupee symbol ₹
for any monetary value. Do not invent any feature change beyond the ones
provided. Output ONLY the explanation in the requested language; no preamble,
no English translation, no markdown."""


def render_explanation(
    applicant: pd.Series,
    counterfactuals: list[Counterfactual],
    language: str = "hindi",
) -> str:
    """Use Gemini 2.5 Flash to render a vernacular counterfactual."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback_explanation(applicant, counterfactuals, language)
    if not counterfactuals:
        return _no_counterfactual_message(language)

    try:
        from google import genai
        from google.genai import types
    except Exception:
        return _fallback_explanation(applicant, counterfactuals, language)

    lang_label = LANG_MAP.get(language.lower(), "English")
    bullets = "\n".join(
        f"- {c.explanation_human} (model approval probability would rise to "
        f"{c.proposed_proba:.0%})"
        for c in counterfactuals
    )
    user_prompt = (
        f"Applicant: {applicant.get('display_name', 'Citizen')} from "
        f"{applicant.get('state', 'India')} ({applicant.get('city_tier', '')}). "
        f"Currently working as a {applicant.get('occupation', 'worker')}, "
        f"age {int(applicant.get('age', 0))}, "
        f"{int(applicant.get('education_num', 0))} years of education. "
        f"The instant-loan model denied the application. The following changes "
        f"would have resulted in approval, ranked by approval probability:\n"
        f"{bullets}\n\n"
        f"Write the explanation in {lang_label}. Address the applicant by their "
        f"first name. Lead with the strongest counterfactual. Two to four short "
        f"sentences."
    )
    try:
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        resp = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=400,
            ),
        )
        return (resp.text or "").strip() or _fallback_explanation(
            applicant, counterfactuals, language
        )
    except Exception as exc:
        return _fallback_explanation(applicant, counterfactuals, language, error=str(exc))


def _fallback_explanation(
    applicant: pd.Series,
    counterfactuals: list[Counterfactual],
    language: str,
    error: str | None = None,
) -> str:
    """Plain-English fallback when Gemini is unavailable."""
    name = applicant.get("display_name", "Applicant")
    if not counterfactuals:
        return _no_counterfactual_message(language)
    top = counterfactuals[0]
    note = f" (Gemini unreachable: {error})" if error else ""
    return (
        f"{name}, the model denied your application based on the patterns it "
        f"learned. According to the audit, you would have been approved with "
        f"{top.explanation_human}.{note}"
    )


def _no_counterfactual_message(language: str) -> str:
    return (
        "We could not find a single-feature change that would have flipped this "
        "decision. The denial reflects a combination of factors the model weighs "
        "together — and is exactly the kind of opaque outcome FairLoan India "
        "exists to surface."
    )
