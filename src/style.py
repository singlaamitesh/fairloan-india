"""Editorial / public-interest dossier theme for FairLoan India.

Visual reference: ProPublica, The Markup, Rest of World, FT data desk.
Single accent rule: alarm-red is reserved exclusively for disparity signals.
Everything else is ink, newsprint, and hairlines.
"""
from __future__ import annotations

import streamlit as st


# Color tokens — used by both the CSS injection below and the Plotly charts.
INK = "#0d0d0c"
INK_SOFT = "#3a3530"
MUTED = "#6c655d"
HAIRLINE = "#cfc8be"
NEWSPRINT = "#fbf9f4"
NEWSPRINT_TINT = "#f3eee5"

ALARM = "#c1272d"          # disparity / denial signal — used sparingly
ALARM_SOFT = "#e6b5b6"
SAFE = "#1b4d3e"           # used only for "approved" indicators
HIGHLIGHT = "#f0d367"

# Plotly palette helpers
MUTED_BAR = "#9a8f80"
ALARM_BAR = ALARM


def chart_layout(height: int = 320) -> dict:
    """Plotly layout shared by every chart in the app."""
    return dict(
        paper_bgcolor=NEWSPRINT,
        plot_bgcolor=NEWSPRINT,
        font=dict(
            family='"Newsreader", "JetBrains Mono", Georgia, serif',
            color=INK,
            size=13,
        ),
        margin=dict(l=18, r=14, t=18, b=20),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=INK,
            linewidth=1,
            tickfont=dict(size=12, color=INK_SOFT),
            ticklen=4,
        ),
        yaxis=dict(
            gridcolor=HAIRLINE,
            zeroline=False,
            tickfont=dict(size=11, color=MUTED),
        ),
        height=height,
        showlegend=False,
    )


def bar_colors(values, threshold_low_factor: float = 0.6) -> list[str]:
    """Color the LOWEST-approval bar in alarm red. Everything else muted.

    The audit's argument is "this one slice is denied at a far lower rate."
    Coloring the worst bar in alarm red turns each chart into a single-look
    proof of the disparity.
    """
    if not len(values):
        return []
    lo = min(values)
    hi = max(values)
    out = []
    for v in values:
        if v == lo and (hi - lo) > 1.5:  # >1.5 pp gap before flagging
            out.append(ALARM_BAR)
        else:
            out.append(MUTED_BAR)
    return out


def inject_css() -> None:
    """Inject the editorial theme. Call once at the top of main().

    Uses st.html() rather than st.markdown(unsafe_allow_html=True) because
    the latter runs the markdown parser, which mangles CSS attribute selectors
    like ``[class*="stApp"]`` (treats them as markdown link syntax).
    """
    st.html(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Newsreader:ital,opsz,wght@0,6..72,300..800;1,6..72,300..800&family=JetBrains+Mono:ital,wght@0,300..800;1,300..800&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #0d0d0c;
    --ink-soft: #3a3530;
    --muted: #6c655d;
    --hairline: #cfc8be;
    --newsprint: #fbf9f4;
    --newsprint-tint: #f3eee5;
    --alarm: #c1272d;
    --alarm-soft: #e6b5b6;
    --safe: #1b4d3e;
    --highlight: #f0d367;
    --serif-display: "Fraunces", "Newsreader", Georgia, serif;
    --serif-body: "Newsreader", Georgia, "Iowan Old Style", serif;
    --mono: "JetBrains Mono", "Fira Code", "Menlo", monospace;
  }

  /* ---- App shell ---- */
  html, body, [class*="stApp"], .stMain, .main {
    background: var(--newsprint) !important;
    color: var(--ink) !important;
    font-family: var(--serif-body) !important;
  }
  /* Hide the floating Deploy / hamburger chrome */
  header[data-testid="stHeader"] { background: transparent !important; }
  div[data-testid="stToolbar"] { display: none !important; }
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  .stDeployButton { display: none !important; }

  /* Wider, more disciplined column rhythm */
  .block-container {
    padding-top: 2.4rem !important;
    padding-bottom: 5rem !important;
    max-width: 1240px !important;
  }

  /* ---- Typography ---- */
  h1, h2, h3, h4, h5 {
    font-family: var(--serif-display) !important;
    color: var(--ink) !important;
    letter-spacing: -0.012em !important;
  }
  h1 { font-weight: 600 !important; }
  h2 { font-weight: 500 !important; font-style: italic; }
  p, li, label, .stMarkdown { font-family: var(--serif-body) !important; }
  code, pre, .stCodeBlock {
    font-family: var(--mono) !important;
    font-size: 0.86rem !important;
  }

  /* ---- Editorial header ---- */
  .fl-masthead {
    border-bottom: 4px solid var(--ink);
    padding-bottom: 1.2rem;
    margin-bottom: 2.2rem;
  }
  .fl-eyebrow {
    font-family: var(--mono);
    font-size: 0.74rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--alarm);
    margin: 0 0 0.6rem 0;
    font-weight: 500;
  }
  .fl-title {
    font-family: var(--serif-display);
    font-weight: 600;
    font-size: 3.6rem;
    line-height: 0.98;
    letter-spacing: -0.025em;
    color: var(--ink);
    margin: 0 0 0.35rem 0;
    font-variation-settings: "opsz" 144;
  }
  .fl-kicker {
    font-family: var(--serif-body);
    font-style: italic;
    font-size: 1.18rem;
    color: var(--ink-soft);
    line-height: 1.45;
    max-width: 60ch;
    margin: 0 0 1.6rem 0;
  }
  .fl-byline {
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.4rem;
  }

  /* ---- KPI strip ---- */
  .fl-kpis { display: flex; gap: 0; border-top: 1px solid var(--hairline);
             border-bottom: 1px solid var(--hairline); margin-bottom: 2rem; }
  .fl-kpi { flex: 1; padding: 1.1rem 1.2rem 1.1rem 0;
            border-right: 1px solid var(--hairline); }
  .fl-kpi:last-child { border-right: 0; }
  .fl-kpi-label { font-family: var(--mono); font-size: 0.7rem;
                  letter-spacing: 0.16em; text-transform: uppercase;
                  color: var(--muted); margin-bottom: 0.35rem; }
  .fl-kpi-value { font-family: var(--serif-display); font-size: 2.05rem;
                  font-weight: 500; color: var(--ink);
                  font-variation-settings: "opsz" 144;
                  font-feature-settings: "tnum" 1; }

  /* ---- Section heads ---- */
  .fl-section-head {
    margin-top: 1.2rem;
    margin-bottom: 1.4rem;
  }
  .fl-section-eyebrow {
    font-family: var(--mono); font-size: 0.68rem;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--alarm); margin-bottom: 0.4rem;
  }
  .fl-section-title {
    font-family: var(--serif-display); font-weight: 600;
    font-size: 1.85rem; line-height: 1.05;
    letter-spacing: -0.018em; margin: 0;
  }
  .fl-section-deck {
    font-family: var(--serif-body); font-style: italic;
    color: var(--ink-soft); max-width: 75ch;
    margin-top: 0.5rem; line-height: 1.5;
  }

  /* ---- Tabs ---- */
  div[data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--ink) !important;
    gap: 0 !important;
    margin-bottom: 1.6rem !important;
  }
  div[data-baseweb="tab"] {
    background: transparent !important;
    padding: 0.7rem 1.4rem !important;
    border: none !important;
    border-radius: 0 !important;
  }
  div[data-baseweb="tab"] p {
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    margin: 0 !important;
  }
  div[data-baseweb="tab"][aria-selected="true"] p {
    color: var(--ink) !important;
    font-weight: 600 !important;
  }
  div[data-baseweb="tab-highlight"] {
    background: var(--alarm) !important;
    height: 3px !important;
  }
  div[data-baseweb="tab-border"] { display: none !important; }

  /* ---- Buttons ---- */
  .stButton > button, .stDownloadButton > button {
    background: var(--ink) !important;
    color: var(--newsprint) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    padding: 0.7rem 1.3rem !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: background 0.16s ease;
  }
  .stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--alarm) !important;
    border-color: var(--alarm) !important;
    color: var(--newsprint) !important;
  }
  .stButton > button[kind="primary"] {
    background: var(--alarm) !important;
    border-color: var(--alarm) !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: var(--ink) !important;
    border-color: var(--ink) !important;
  }

  /* ---- Selects + inputs ---- */
  div[data-baseweb="select"] > div {
    background: var(--newsprint) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    font-family: var(--serif-body) !important;
  }
  label, .stSelectbox label, .stTextInput label {
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
  }

  /* ---- Tables ---- */
  div[data-testid="stDataFrame"] {
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
  }
  div[data-testid="stDataFrame"] [role="columnheader"] {
    background: var(--ink) !important;
    color: var(--newsprint) !important;
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
  }
  div[data-testid="stDataFrame"] [role="row"]:hover {
    background: var(--newsprint-tint) !important;
  }

  /* ---- Applicant card ---- */
  .fl-applicant {
    border: 1px solid var(--ink);
    background: var(--newsprint);
    padding: 1.4rem 1.6rem;
    margin: 1rem 0 1.5rem 0;
    position: relative;
  }
  .fl-applicant::before {
    content: "DOSSIER";
    position: absolute;
    top: -0.55rem; left: 1.2rem;
    background: var(--newsprint);
    padding: 0 0.5rem;
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.2em;
    color: var(--alarm);
    font-weight: 600;
  }
  .fl-applicant-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.1rem 2rem;
  }
  .fl-applicant-grid.cols-5 { grid-template-columns: repeat(5, 1fr); }
  .fl-field-label { font-family: var(--mono); font-size: 0.66rem;
                    letter-spacing: 0.14em; text-transform: uppercase;
                    color: var(--muted); margin-bottom: 0.18rem; }
  .fl-field-value { font-family: var(--serif-body); font-size: 1rem;
                    color: var(--ink); line-height: 1.3; }
  .fl-applicant-rule {
    border-top: 1px dashed var(--hairline);
    margin: 1.3rem 0 1.1rem 0;
  }

  /* ---- Decision badge with pulsing dot ---- */
  .fl-decision {
    display: inline-flex;
    align-items: baseline;
    gap: 0.7rem;
    margin-top: 0.4rem;
    padding: 0.55rem 1rem;
    border: 1.5px solid var(--alarm);
    background: var(--newsprint);
    font-family: var(--mono);
    font-size: 0.82rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--alarm);
    font-weight: 600;
  }
  .fl-decision .fl-dot {
    width: 0.6rem; height: 0.6rem;
    background: var(--alarm); border-radius: 50%;
    display: inline-block;
    animation: fl-pulse 1.6s ease-in-out infinite;
  }
  .fl-decision-meta {
    color: var(--muted);
    font-weight: 400;
    letter-spacing: 0.12em;
  }
  @keyframes fl-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%       { transform: scale(1.5); opacity: 0.55; }
  }

  /* ---- Pull-quote (the Gemini hero shot) ---- */
  .fl-quote {
    border-left: 3px solid var(--alarm);
    padding: 1.2rem 0 1.2rem 1.6rem;
    margin: 1.5rem 0 1rem 0;
    font-family: var(--serif-display);
    font-style: italic;
    font-weight: 400;
    font-size: 1.55rem;
    line-height: 1.45;
    color: var(--ink);
    font-variation-settings: "opsz" 96;
    background: linear-gradient(
      to right,
      rgba(193, 39, 45, 0.04) 0%,
      rgba(193, 39, 45, 0) 70%
    );
  }
  .fl-quote::before {
    content: "\\201C";
    color: var(--alarm);
    font-size: 2.4rem;
    line-height: 0;
    margin-right: 0.2rem;
    vertical-align: -0.4rem;
  }
  .fl-quote-attr {
    display: block;
    margin-top: 1.2rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    font-style: normal;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }

  /* ---- Disparity inline rules in the table ---- */
  .fl-table-disparity {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--serif-body);
    font-size: 0.96rem;
    border: 1px solid var(--ink);
    margin-bottom: 1rem;
  }
  .fl-table-disparity th {
    background: var(--ink);
    color: var(--newsprint);
    text-align: left;
    padding: 0.6rem 0.9rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 500;
  }
  .fl-table-disparity th.num { text-align: right; }
  .fl-table-disparity td {
    padding: 0.65rem 0.9rem;
    border-top: 1px solid var(--hairline);
    vertical-align: middle;
  }
  .fl-table-disparity td.feature {
    font-family: var(--mono);
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    color: var(--ink);
    width: 22%;
  }
  .fl-table-disparity td.num {
    text-align: right;
    font-family: var(--mono);
    font-feature-settings: "tnum" 1;
    color: var(--ink);
  }
  .fl-table-disparity td.num.high {
    color: var(--alarm);
    font-weight: 600;
  }
  .fl-table-disparity td.num.low { color: var(--muted); }
  .fl-table-disparity tr:hover td { background: var(--newsprint-tint); }
  .fl-bar-cell { width: 24%; }
  .fl-bar-track {
    height: 6px;
    background: var(--newsprint-tint);
    border: 1px solid var(--hairline);
    position: relative;
  }
  .fl-bar-fill {
    height: 100%;
    background: var(--alarm);
  }
  .fl-bar-fill.muted { background: var(--ink-soft); }

  /* ---- About-tab editorial block ---- */
  .fl-essay {
    max-width: 68ch;
    font-family: var(--serif-body);
    font-size: 1.08rem;
    line-height: 1.65;
    color: var(--ink);
  }
  .fl-essay h3 { font-family: var(--serif-display); font-weight: 600;
                 font-size: 1.4rem; margin-top: 2rem; margin-bottom: 0.6rem; }
  .fl-essay p { margin: 0 0 1rem 0; }
  .fl-essay p:first-of-type::first-letter {
    font-family: var(--serif-display);
    font-size: 3.4rem;
    font-weight: 600;
    float: left;
    line-height: 0.86;
    margin: 0.3rem 0.5rem -0.2rem 0;
    color: var(--alarm);
  }
  .fl-essay strong { color: var(--ink); font-weight: 600; }

  /* ---- Caption ---- */
  .stCaption, [data-testid="stCaptionContainer"] {
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.04em !important;
  }

  /* ---- Plotly chart heading row ---- */
  .fl-chart-grid-head {
    font-family: var(--mono);
    font-size: 0.74rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--ink);
    border-bottom: 1px solid var(--ink);
    padding-bottom: 0.3rem;
    margin-bottom: 0.5rem;
  }
  .fl-chart-meta {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
  }
  .fl-chart-meta .fl-dpd-high { color: var(--alarm); font-weight: 600; }

  /* Hide noisy Streamlit-default rules between widgets */
  hr { border-color: var(--hairline) !important; }
</style>
"""
    )
