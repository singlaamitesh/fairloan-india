"""FairLoan India — Streamlit dashboard.

Editorial / public-interest dossier styling (see src/style.py).
Two tabs:
  1. Audit — slice-level disparities, with the worst-disparity slice
     highlighted in alarm-red on every chart.
  2. Citizen Lookup — pick a denied applicant; render a vernacular
     counterfactual explanation via Gemini as a pull-quote.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from html import escape
from pathlib import Path

# Make this file work both as a package module (python -m src.app) and as a
# top-level script (streamlit run src/app.py). The latter is what Cloud Run
# executes, and Python won't recognise `src` as a package without sys.path help.
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src import audit as audit_mod
from src import counterfactual as cf_mod
from src import personas
from src import style
from src import train as train_mod

load_dotenv()

st.set_page_config(
    page_title="FairLoan India — Bias Audit + Vernacular Counterfactuals",
    page_icon="⚖",
    layout="wide",
)

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"


@st.cache_resource
def load_or_train():
    if not (ARTIFACT_DIR / "model.pkl").exists():
        with st.spinner("First-run training — about 30 seconds…"):
            train_mod.train_model()
    return train_mod.load_artifacts()


@st.cache_data
def get_audit_reports(_holdout: pd.DataFrame):
    return audit_mod.audit_all(_holdout)


# ---------------------------------------------------------------------------
# Masthead + KPI strip
# ---------------------------------------------------------------------------
def render_masthead(metadata: dict) -> None:
    today = dt.date.today().strftime("%B %d, %Y").upper()
    st.html(
        f"""
<div class="fl-masthead">
  <p class="fl-eyebrow">Vol. 01 · Public-interest audit · {today}</p>
  <h1 class="fl-title">FairLoan India</h1>
  <p class="fl-kicker">
    A public-interest audit of algorithmic credit decisions in India,
    with vernacular explanations rendered for the citizens those decisions
    silently affect.
  </p>
  <p class="fl-byline">
    Filed by FairLoan India · Theme 4, Unbiased AI Decision · SDG 5 · 10 · 16
  </p>
</div>
"""
    )

    st.html(
        f"""
<div class="fl-kpis">
  <div class="fl-kpi">
    <div class="fl-kpi-label">Holdout accuracy</div>
    <div class="fl-kpi-value">{metadata['accuracy']*100:.1f}%</div>
  </div>
  <div class="fl-kpi">
    <div class="fl-kpi-label">ROC AUC</div>
    <div class="fl-kpi-value">{metadata['auc']:.3f}</div>
  </div>
  <div class="fl-kpi">
    <div class="fl-kpi-label">Holdout applicants</div>
    <div class="fl-kpi-value">{metadata['n_test']:,}</div>
  </div>
  <div class="fl-kpi">
    <div class="fl-kpi-label">Languages</div>
    <div class="fl-kpi-value">हि · த · বং · EN</div>
  </div>
</div>
"""
    )


def section_head(eyebrow: str, title: str, deck: str) -> None:
    st.html(
        f"""
<div class="fl-section-head">
  <div class="fl-section-eyebrow">{escape(eyebrow)}</div>
  <h2 class="fl-section-title">{escape(title)}</h2>
  <p class="fl-section-deck">{deck}</p>
</div>
"""
    )


# ---------------------------------------------------------------------------
# Audit tab
# ---------------------------------------------------------------------------
def render_audit(holdout: pd.DataFrame, reports) -> None:
    section_head(
        "Finding I",
        "Slice-level disparities",
        "Each row is a sensitive feature. <em>Demographic Parity Difference</em>"
        " is the gap in approval rate between the most-treated and "
        "least-treated group. <em>Equalized Odds Difference</em> is the gap "
        "in error rates. The largest gaps are highlighted.",
    )

    summary = audit_mod.disparity_summary(reports).reset_index(drop=True)

    rows_html = []
    for _, r in summary.iterrows():
        dpd = r["demographic_parity_difference"]
        eod = r["equalized_odds_difference"]
        max_sr = r["max_selection_rate"]
        min_sr = r["min_selection_rate"]
        bar_pct = max(2.0, min(100.0, dpd * 100))
        bar_class = "" if dpd > 0.10 else "muted"
        dpd_class = "high" if dpd > 0.10 else ("low" if dpd < 0.05 else "")
        rows_html.append(
            f"""
<tr>
  <td class="feature">{escape(r['sensitive_feature'])}</td>
  <td class="num {dpd_class}">{dpd*100:.1f}%</td>
  <td class="bar-cell fl-bar-cell">
    <div class="fl-bar-track"><div class="fl-bar-fill {bar_class}" style="width:{bar_pct:.1f}%"></div></div>
  </td>
  <td class="num">{eod*100:.1f}%</td>
  <td class="num">{max_sr*100:.1f}%</td>
  <td class="num">{min_sr*100:.1f}%</td>
  <td class="num">{int(r['n_groups'])}</td>
</tr>"""
        )

    st.html(
        f"""
<table class="fl-table-disparity">
  <thead>
    <tr>
      <th>Sensitive feature</th>
      <th class="num">DPD</th>
      <th>&nbsp;</th>
      <th class="num">EOD</th>
      <th class="num">Max approval</th>
      <th class="num">Min approval</th>
      <th class="num">Groups</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows_html)}
  </tbody>
</table>
<p class="fl-chart-meta">DPD &gt; 10% rendered in <span class="fl-dpd-high">alarm</span>. The horizontal rule is proportional to DPD.</p>
"""
    )

    st.markdown("&nbsp;")
    cols = st.columns(len(reports))
    for i, (name, rep) in enumerate(reports.items()):
        with cols[i]:
            df_chart = rep.by_group.reset_index().rename(
                columns={rep.by_group.index.name or "index": "group"}
            )
            df_chart["selection_rate_pct"] = df_chart["selection_rate"] * 100
            colors = style.bar_colors(df_chart["selection_rate_pct"].tolist())

            chart_label = name.replace("_", " ").upper()
            st.html(
                f'<div class="fl-chart-grid-head">{escape(chart_label)}</div>'
            )
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=df_chart["group"],
                        y=df_chart["selection_rate_pct"],
                        marker=dict(color=colors, line=dict(color=style.INK, width=1)),
                        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
                    )
                ]
            )
            fig.update_layout(**style.chart_layout(height=240))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            dpd_class = "fl-dpd-high" if rep.dpd > 0.10 else ""
            st.html(
                f'<div class="fl-chart-meta">DPD <span class="{dpd_class}">{rep.dpd*100:.1f}%</span> · EOD {rep.eod*100:.1f}%</div>'
            )


# ---------------------------------------------------------------------------
# Citizen Lookup tab
# ---------------------------------------------------------------------------
def render_dossier(applicant: pd.Series) -> None:
    fields_top = [
        ("Name", str(applicant["display_name"])),
        ("State · tier", f"{applicant['state']} · {applicant['city_tier']}"),
        ("Estimated income", f"₹{int(applicant['estimated_monthly_income_inr']):,} / month"),
        ("Application ID", str(applicant["display_id"])),
    ]
    fields_bottom = [
        ("Age", str(int(applicant["age"]))),
        ("Sex", str(applicant["sex"])),
        ("Occupation", str(applicant["occupation"])),
        ("Education", str(applicant["education"])),
        ("Hours / week", str(int(applicant["hours_per_week"]))),
    ]

    def cells(items):
        return "".join(
            f'<div><div class="fl-field-label">{escape(label)}</div>'
            f'<div class="fl-field-value">{escape(value)}</div></div>'
            for label, value in items
        )

    st.html(
        f"""
<div class="fl-applicant">
  <div class="fl-applicant-grid">{cells(fields_top)}</div>
  <div class="fl-applicant-rule"></div>
  <div class="fl-applicant-grid cols-5">{cells(fields_bottom)}</div>
</div>
"""
    )


def render_decision(applicant: pd.Series) -> None:
    proba = float(applicant["pred_proba"])
    st.html(
        f"""
<div class="fl-decision">
  <span class="fl-dot"></span>
  <span>Denied</span>
  <span class="fl-decision-meta">approval probability {proba*100:.0f}% · threshold 50%</span>
</div>
"""
    )


def render_counterfactual_table(cfs) -> None:
    rows = "".join(
        f'<tr><td class="feature">{escape(c.explanation_human)}</td>'
        f'<td class="num high">{c.proposed_proba*100:.0f}%</td></tr>'
        for c in cfs
    )
    st.html(
        f"""
<table class="fl-table-disparity" style="margin-top: 0.4rem;">
  <thead>
    <tr>
      <th>Validated counterfactual change</th>
      <th class="num">Approval after change</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
"""
    )


def render_quote(text: str, applicant: pd.Series, language: str) -> None:
    today = dt.date.today().strftime("%B %d, %Y")
    safe_text = escape(text).replace("\n", "<br>")
    st.html(
        f"""
<blockquote class="fl-quote">
  {safe_text}
  <span class="fl-quote-attr">
    Rendered in {language.upper()} by Gemini 2.5 Flash · for
    {escape(str(applicant['display_name']))}, {escape(str(applicant['state']))} · {today}
  </span>
</blockquote>
"""
    )


def render_citizen_lookup(holdout, model, encoders, feature_cols) -> None:
    section_head(
        "Finding II",
        "Citizen Lookup — Why was I denied?",
        "Pick a denied applicant. FairLoan finds single-feature changes that "
        "would flip the model's decision (each verified against the actual "
        "classifier). Gemini renders a respectful explanation in the citizen's "
        "own language.",
    )

    demo = personas.pick_demo_applicants(holdout, n_per_archetype=1)
    if demo.empty:
        st.warning("No denied applicants in holdout — please retrain.")
        return

    cols = st.columns([3, 2, 1.4])
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
        run = st.button("Why was I denied?", type="primary", use_container_width=True)

    applicant = demo.iloc[idx]

    render_dossier(applicant)
    render_decision(applicant)

    if not run:
        st.html(
            '<p class="fl-chart-meta" style="margin-top: 1.6rem;">'
            'Press "Why was I denied?" to surface validated counterfactuals '
            'and a vernacular explanation.</p>'
        )
        return

    with st.spinner("Searching counterfactuals…"):
        cfs = cf_mod.find_counterfactuals(
            applicant, model, encoders, feature_cols, max_results=3
        )
    if not cfs:
        st.html(
            '<p class="fl-chart-meta" style="margin-top: 1.6rem;">'
            'No single-feature change flips this decision. The denial reflects '
            'a combination of factors the model weighs together — exactly the '
            'kind of opaque outcome FairLoan exists to surface.</p>'
        )
        return

    st.html(
        '<p class="fl-section-eyebrow" style="margin-top: 1.6rem;">'
        'Validated counterfactuals · each one flips the model</p>'
    )
    render_counterfactual_table(cfs)

    with st.spinner("Asking Gemini for a respectful, vernacular explanation…"):
        explanation = cf_mod.render_explanation(applicant, cfs, language)
    render_quote(explanation, applicant, language)
    st.caption(
        "Gemini only sees counterfactuals that have been verified to flip the "
        "classifier. No invented fixes."
    )


# ---------------------------------------------------------------------------
# About tab
# ---------------------------------------------------------------------------
def render_about(metadata: dict) -> None:
    section_head(
        "Editorial",
        "About this audit",
        "Method, dataset, and the uncomfortable patterns this dashboard makes "
        "visible.",
    )
    st.html(
        f"""
<div class="fl-essay">
<p>
Indian digital-lending apps approve or deny instant loans in seconds using ML
classifiers. RBI's <strong>2021 Working Group on Digital Lending</strong> and
multiple journalistic investigations have documented systematic disparities in
approval rates by gender, region, and class — and denied applicants get one
line of explanation: <em>your application could not be processed</em>.
</p>

<h3>What FairLoan does</h3>
<p>
FairLoan India is a thin layer that any journalist, regulator, NGO, or
ombudsman can use to (a) <strong>quantify</strong> those disparities at the
slice level and (b) generate <strong>vernacular counterfactual explanations</strong>
for affected citizens. The audit is dataset-agnostic; the Indian framing is
the user-facing layer.
</p>

<h3>Method</h3>
<p>
The classifier in this demo trains on the <strong>UCI Adult Income</strong>
benchmark — the most-cited dataset in algorithmic-fairness research — recast
into an Indian framing (names, states, tier classification, INR income bands).
Holdout accuracy <strong>{metadata['accuracy']*100:.1f}%</strong>,
ROC AUC <strong>{metadata['auc']:.3f}</strong>,
holdout size <strong>{metadata['n_test']:,}</strong> applicants.
The bias patterns the dashboard surfaces — gender × region × age — are the
textbook fairness signal in this dataset.
</p>

<h3>Counterfactual integrity</h3>
<p>
The Citizen Lookup tab does <strong>not</strong> let Gemini invent feature
changes. The counterfactual finder tries deterministic single-feature deltas,
scores each against the actual LightGBM model, keeps only those that cross
the 0.5 approval threshold, and passes the validated set to Gemini with a
system prompt that forbids invention. Every explanation is model-verified.
</p>

<h3>Stack</h3>
<p>
LightGBM · Fairlearn · Streamlit · Gemini 2.5 Flash · Google Cloud Run
(asia-south1).
</p>

<h3>SDG mapping</h3>
<p>
SDG 5 (Gender Equality) · SDG 10 (Reduced Inequalities) · SDG 16 (Strong
Institutions, Algorithmic Accountability).
</p>

<h3>Roadmap</h3>
<p>
v2 partners with Sa-Dhan or Bharat Inclusion Initiative to audit a real
production microfinance classifier under MoU; integrates the Home Credit
Default Risk India subset; adds caste-axis slicing under consented data.
</p>
</div>
"""
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    style.inject_css()
    model, encoders, feature_cols, holdout, metadata = load_or_train()
    render_masthead(metadata)
    reports = get_audit_reports(holdout)

    tab_audit, tab_citizen, tab_about = st.tabs(
        ["Audit", "Citizen Lookup", "About"]
    )
    with tab_audit:
        render_audit(holdout, reports)
    with tab_citizen:
        render_citizen_lookup(holdout, model, encoders, feature_cols)
    with tab_about:
        render_about(metadata)


if __name__ == "__main__":
    main()
