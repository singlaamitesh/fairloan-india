"""FairLoan India — Streamlit dashboard.

Two tabs:
  1. Audit: slice-level disparities visualised as a heatmap + per-slice bars
  2. Citizen Lookup: pick a denied applicant, see Gemini's vernacular
     counterfactual explanation in Hindi / Tamil / Bengali / English
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make this file work both as a package module (python -m src.app) and as a
# top-level script (streamlit run src/app.py). The latter is what Cloud Run
# executes, and Python won't recognise `src` as a package without sys.path help.
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src import audit as audit_mod
from src import counterfactual as cf_mod
from src import personas
from src import train as train_mod

load_dotenv()

st.set_page_config(
    page_title="FairLoan India — Bias Audit + Vernacular Counterfactuals",
    page_icon="⚖️",
    layout="wide",
)

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


@st.cache_resource
def load_or_train():
    if not (ARTIFACT_DIR / "model.pkl").exists():
        with st.spinner("First-run training (about 30 seconds)…"):
            train_mod.train_model()
    return train_mod.load_artifacts()


@st.cache_data
def get_audit_reports(_holdout: pd.DataFrame):
    return audit_mod.audit_all(_holdout)


def _format_pct(x):
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return str(x)


def header(metadata):
    cols = st.columns([3, 1, 1, 1])
    cols[0].markdown(
        "## ⚖️ FairLoan India\n"
        "**Bias audit + vernacular counterfactual explanations for "
        "Indian digital-lending decisions.**"
    )
    cols[1].metric("Model accuracy", f"{metadata['accuracy']*100:.1f}%")
    cols[2].metric("ROC-AUC", f"{metadata['auc']:.3f}")
    cols[3].metric("Holdout size", f"{metadata['n_test']:,}")


def render_audit(holdout: pd.DataFrame, reports):
    st.markdown(
        "### Slice-level disparities  \n"
        "Each row is a sensitive feature. Demographic Parity Difference "
        "(DPD) measures the gap in approval rate between the highest- and "
        "lowest-treated groups. Equalized Odds Difference (EOD) measures "
        "the gap in error rates. Higher = more disparity."
    )
    summary = audit_mod.disparity_summary(reports).reset_index(drop=True)
    summary_disp = summary.copy()
    for col in [
        "demographic_parity_difference",
        "equalized_odds_difference",
        "max_selection_rate",
        "min_selection_rate",
    ]:
        summary_disp[col] = summary_disp[col].apply(_format_pct)
    st.dataframe(
        summary_disp,
        use_container_width=True,
        hide_index=True,
    )

    cols = st.columns(len(reports))
    for i, (name, rep) in enumerate(reports.items()):
        with cols[i]:
            st.markdown(f"#### {name.replace('_', ' ').title()}")
            df_chart = rep.by_group.reset_index().rename(
                columns={rep.by_group.index.name or "index": "group"}
            )
            df_chart["selection_rate_pct"] = df_chart["selection_rate"] * 100
            fig = px.bar(
                df_chart,
                x="group",
                y="selection_rate_pct",
                hover_data=["count", "accuracy", "false_negative_rate"],
                labels={"selection_rate_pct": "Approval rate (%)"},
                color="selection_rate_pct",
                color_continuous_scale="RdYlGn",
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Approval rate (%)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
                showlegend=False,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                f"DPD = {rep.dpd:.1%}  ·  EOD = {rep.eod:.1%}"
            )


def _applicant_card(applicant: pd.Series):
    cols = st.columns([1, 1, 1, 1])
    cols[0].markdown(f"**Name**  \n{applicant['display_name']}")
    cols[1].markdown(
        f"**State / tier**  \n{applicant['state']} · {applicant['city_tier']}"
    )
    cols[2].markdown(
        f"**Estimated income**  \n"
        f"₹{int(applicant['estimated_monthly_income_inr']):,} / month"
    )
    cols[3].markdown(
        f"**Application ID**  \n`{applicant['display_id']}`"
    )
    st.divider()
    cols = st.columns([1, 1, 1, 1, 1])
    cols[0].markdown(f"**Age**  \n{int(applicant['age'])}")
    cols[1].markdown(f"**Sex**  \n{applicant['sex']}")
    cols[2].markdown(f"**Occupation**  \n{applicant['occupation']}")
    cols[3].markdown(f"**Education**  \n{applicant['education']}")
    cols[4].markdown(
        f"**Hours / week**  \n{int(applicant['hours_per_week'])}"
    )


def render_citizen_lookup(holdout, model, encoders, feature_cols):
    st.markdown(
        "### Citizen Lookup — Why was I denied?  \n"
        "Pick a denied applicant. FairLoan finds single-feature changes that "
        "would have flipped the model's decision, then renders a "
        "vernacular explanation via Gemini."
    )
    demo = personas.pick_demo_applicants(holdout, n_per_archetype=1)
    if demo.empty:
        st.warning("No denied applicants in holdout — odd, please retrain.")
        return

    cols = st.columns([2, 2, 1])
    with cols[0]:
        labels = [
            f"{r['display_name']}  ·  {r['archetype']}"
            for _, r in demo.iterrows()
        ]
        idx = st.selectbox(
            "Choose a denied applicant",
            options=list(range(len(demo))),
            format_func=lambda i: labels[i],
        )
    with cols[1]:
        language = st.selectbox(
            "Explanation language",
            options=["hindi", "tamil", "bengali", "english"],
            index=0,
        )
    with cols[2]:
        st.write("")
        st.write("")
        run = st.button("Why was I denied?", type="primary")

    applicant = demo.iloc[idx]

    st.markdown("#### Applicant profile")
    _applicant_card(applicant)

    st.markdown("#### Model decision")
    proba = float(applicant["pred_proba"])
    badge = "🛑 DENIED"
    st.markdown(
        f"**{badge}**  ·  approval probability **{proba:.0%}** "
        f"(threshold 50%)"
    )

    if not run:
        return

    with st.spinner("Searching counterfactuals…"):
        cfs = cf_mod.find_counterfactuals(
            applicant, model, encoders, feature_cols, max_results=3
        )
    if not cfs:
        st.info(
            "No single-feature change flips this decision. The denial reflects "
            "a combination of factors the model weighs together — exactly the "
            "kind of opaque outcome FairLoan exists to surface."
        )
        return
    st.markdown("#### Validated counterfactuals (each one flips the model)")
    cf_df = pd.DataFrame(
        [
            {
                "Change": c.explanation_human,
                "Approval probability after change": f"{c.proposed_proba:.0%}",
            }
            for c in cfs
        ]
    )
    st.dataframe(cf_df, use_container_width=True, hide_index=True)

    st.markdown(f"#### Gemini explanation — _{language.title()}_")
    with st.spinner("Asking Gemini for a respectful, vernacular explanation…"):
        explanation = cf_mod.render_explanation(applicant, cfs, language)
    st.success(explanation)
    st.caption(
        "Generated by Gemini 2.5 Flash. The model only sees counterfactuals "
        "that have been verified to flip the classifier — no hallucinated fixes."
    )


def render_about(metadata):
    st.markdown(
        f"""
### About this prototype
**FairLoan India** is a public-interest dashboard built for the
**Google Solution Challenge 2026 India** (Theme 4 — Unbiased AI Decision).

**Why this matters.** Indian digital-lending apps approve or deny instant loans
in seconds using ML classifiers. RBI's 2021 Working Group on Digital Lending
and multiple journalistic investigations have documented systematic disparities
in approval rates by gender, region, and socioeconomic class — with no
explanation given to denied applicants. FairLoan India is a thin layer that any
journalist, regulator, NGO, or ombudsman can use to (a) quantify those
disparities and (b) generate vernacular counterfactual explanations for
affected citizens.

**What's in the demo.** The audit runs on the **UCI Adult Income** dataset —
the universal fairness benchmark in algorithmic-fairness research — recast
into an Indian-context framing (names, states, tier classification, INR
income bands). The methodology is identical for a real Indian credit dataset;
only the data source changes. The bias patterns the dashboard surfaces are
real (gender × region × age disparities are the textbook fairness signal in
this dataset).

**Stack.**  LightGBM · Fairlearn · Streamlit · Gemini 2.5 Flash · Cloud Run.

**SDG mapping.** SDG 5 (Gender Equality) · SDG 10 (Reduced Inequalities)
· SDG 16 (Peace, Justice & Strong Institutions).

**Holdout accuracy:** {metadata['accuracy']*100:.1f}% · **AUC:** {metadata['auc']:.3f}
· **Holdout size:** {metadata['n_test']:,} applicants.

GitHub repo and demo video: see submission deck.
"""
    )


def main():
    model, encoders, feature_cols, holdout, metadata = load_or_train()
    header(metadata)
    reports = get_audit_reports(holdout)

    tab_audit, tab_citizen, tab_about = st.tabs(
        ["🧪 Audit", "👤 Citizen Lookup", "ℹ️ About"]
    )
    with tab_audit:
        render_audit(holdout, reports)
    with tab_citizen:
        render_citizen_lookup(holdout, model, encoders, feature_cols)
    with tab_about:
        render_about(metadata)


if __name__ == "__main__":
    main()
