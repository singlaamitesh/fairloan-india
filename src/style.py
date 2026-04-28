"""Editorial / public-interest dossier theme for FairLoan India.

Visual reference: ProPublica, The Markup, Rest of World, FT data desk,
classic Indian Express op-eds. Single accent rule — alarm-red is reserved
exclusively for disparity signals; everything else lives in ink, newsprint,
hairlines, and a faint paper-grain.
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
    """Plotly layout shared by every chart in the app.

    Charts speak the same typographic language as the body: Newsreader for
    axis labels, JetBrains Mono for tabular tick values.
    """
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family='"Newsreader", Georgia, serif',
            color=INK,
            size=13,
        ),
        margin=dict(l=18, r=14, t=8, b=18),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=INK,
            linewidth=1.2,
            tickfont=dict(
                family='"JetBrains Mono", monospace',
                size=10.5, color=INK_SOFT,
            ),
            ticklen=4,
        ),
        yaxis=dict(
            gridcolor=HAIRLINE,
            gridwidth=0.6,
            zeroline=False,
            tickfont=dict(
                family='"JetBrains Mono", monospace',
                size=10, color=MUTED,
            ),
            title=dict(
                font=dict(
                    family='"Newsreader", Georgia, serif',
                    size=11, color=MUTED,
                ),
                text="approval %",
                standoff=4,
            ),
        ),
        height=height,
        showlegend=False,
        hoverlabel=dict(
            bgcolor=INK,
            bordercolor=INK,
            font=dict(
                family='"JetBrains Mono", monospace',
                size=11, color=NEWSPRINT,
            ),
        ),
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


# A faint paper-grain overlay built from an SVG turbulence filter. The SVG
# is URL-encoded so its literal <...> tags don't trigger Streamlit's
# DOMPurify sanitizer (which would strip the entire surrounding <style>
# block when it sees raw HTML-like markup inside a CSS url()).
_PAPER_GRAIN_SVG = (
    "data:image/svg+xml;utf8,"
    "%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%20600%20600%22%3E"
    "%3Cfilter%20id%3D%22n%22%3E"
    "%3CfeTurbulence%20type%3D%22fractalNoise%22%20baseFrequency%3D%220.85%22%20numOctaves%3D%222%22%20stitchTiles%3D%22stitch%22/%3E"
    "%3CfeColorMatrix%20values%3D%220%200%200%200%200.05%20%200%200%200%200%200.04%20%200%200%200%200%200.03%20%200%200%200%200.55%200%22/%3E"
    "%3C/filter%3E"
    "%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20filter%3D%22url(%23n)%22/%3E"
    "%3C/svg%3E"
)


def inject_css() -> None:
    """Inject the editorial theme. Call once at the top of main().

    Uses st.html() rather than st.markdown(unsafe_allow_html=True) because
    the latter runs the markdown parser, which mangles CSS attribute
    selectors like ``[class*="stApp"]`` (treats them as markdown link syntax).
    """
    st.html(
        f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Newsreader:ital,opsz,wght@0,6..72,300..800;1,6..72,300..800&family=JetBrains+Mono:ital,wght@0,300..800;1,300..800&family=Noto+Serif+Devanagari:wght@400..700&family=Noto+Serif+Tamil:wght@400..700&family=Noto+Serif+Bengali:wght@400..700&display=swap">
<style>
  :root {{
    --ink: #0d0d0c;
    --ink-soft: #3a3530;
    --muted: #6c655d;
    --hairline: #cfc8be;
    --hairline-soft: #e2dccf;
    --newsprint: #fbf9f4;
    --newsprint-tint: #f3eee5;
    --alarm: #c1272d;
    --alarm-soft: #e6b5b6;
    --safe: #1b4d3e;
    --highlight: #f0d367;
    --serif-display: "Fraunces", "Noto Serif Devanagari", "Noto Serif Tamil",
                     "Noto Serif Bengali", Georgia, serif;
    --serif-body: "Newsreader", "Noto Serif Devanagari", "Noto Serif Tamil",
                  "Noto Serif Bengali", Georgia, "Iowan Old Style", serif;
    --mono: "JetBrains Mono", "Fira Code", "Menlo", monospace;
    --paper-grain: url("{_PAPER_GRAIN_SVG}");
  }}

  /* ---- App shell ---- */
  html, body, [class*="stApp"], .stMain, .main {{
    background-color: var(--newsprint) !important;
    background-image: var(--paper-grain) !important;
    background-repeat: repeat !important;
    background-size: 320px 320px !important;
    color: var(--ink) !important;
    font-family: var(--serif-body) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    font-feature-settings: "kern" 1, "liga" 1, "calt" 1;
  }}
  /* Hide the floating Deploy / hamburger chrome */
  header[data-testid="stHeader"] {{ background: transparent !important; }}
  div[data-testid="stToolbar"] {{ display: none !important; }}
  #MainMenu {{ visibility: hidden; }}
  footer {{ visibility: hidden; }}
  .stDeployButton {{ display: none !important; }}

  /* Wider, more disciplined column rhythm */
  .block-container {{
    padding-top: 2.6rem !important;
    padding-bottom: 5rem !important;
    max-width: 1240px !important;
  }}

  /* ---- Typography ---- */
  h1, h2, h3, h4, h5 {{
    font-family: var(--serif-display) !important;
    color: var(--ink) !important;
    letter-spacing: -0.014em !important;
  }}
  h1 {{ font-weight: 600 !important; }}
  h2 {{ font-weight: 500 !important; font-style: italic; }}
  p, li, label, .stMarkdown {{
    font-family: var(--serif-body) !important;
    font-feature-settings: "kern" 1, "liga" 1, "onum" 1;
  }}
  code, pre, .stCodeBlock {{
    font-family: var(--mono) !important;
    font-size: 0.86rem !important;
  }}

  /* ---- Editorial header ---- */
  .fl-masthead {{
    border-bottom: 4px solid var(--ink);
    padding-bottom: 1.4rem;
    margin-bottom: 2.4rem;
    position: relative;
  }}
  .fl-masthead::after {{
    content: "";
    position: absolute;
    left: 0; right: 0;
    bottom: -8px;
    height: 1px;
    background: var(--ink);
  }}
  .fl-eyebrow {{
    font-family: var(--mono);
    font-size: 0.74rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--alarm);
    margin: 0 0 0.55rem 0;
    font-weight: 500;
  }}
  .fl-title {{
    font-family: "Fraunces", Georgia, serif;
    font-weight: 600;
    font-size: clamp(3rem, 6vw, 4.6rem);
    line-height: 0.94;
    letter-spacing: -0.034em;
    color: var(--ink);
    margin: 0 0 0.35rem 0;
    font-variation-settings: "opsz" 144, "SOFT" 30;
    font-feature-settings: "kern" 1, "liga" 1, "ss01" 1;
  }}
  .fl-kicker {{
    font-family: var(--serif-body);
    font-style: italic;
    font-size: 1.22rem;
    color: var(--ink-soft);
    line-height: 1.5;
    max-width: 60ch;
    margin: 0.2rem 0 1.6rem 0;
    font-variation-settings: "opsz" 24;
  }}
  .fl-byline {{
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.4rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.9rem;
    align-items: baseline;
  }}
  .fl-byline .fl-byline-rule {{
    flex: 1; height: 1px; background: var(--hairline); min-width: 1rem;
  }}
  .fl-dateline {{ color: var(--ink); font-weight: 600; }}

  /* ---- KPI strip ---- */
  .fl-kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-top: 2px solid var(--ink);
    border-bottom: 1px solid var(--ink);
    margin: 0 0 2.6rem 0;
    background: rgba(255,255,255,0.35);
  }}
  .fl-kpi {{
    padding: 1.1rem 1.4rem 1.15rem 1.4rem;
    border-right: 1.5px solid var(--ink);
    position: relative;
  }}
  .fl-kpi:first-child {{ padding-left: 0; }}
  .fl-kpi:last-child  {{ border-right: 0; padding-right: 0; }}
  .fl-kpi-label {{
    font-family: var(--mono); font-size: 0.7rem;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.4rem;
    font-weight: 500;
  }}
  .fl-kpi-value {{
    font-family: "Fraunces", Georgia, serif; font-size: 2.2rem;
    font-weight: 500; color: var(--ink);
    font-variation-settings: "opsz" 144;
    font-feature-settings: "tnum" 1, "lnum" 1;
    letter-spacing: -0.022em;
    line-height: 1.05;
  }}
  .fl-kpi-value.scripts {{
    font-family: "Fraunces", "Noto Serif Devanagari", "Noto Serif Tamil",
                 "Noto Serif Bengali", serif;
    font-size: 1.85rem;
    letter-spacing: 0;
  }}

  /* ---- Section heads ---- */
  .fl-section-head {{
    margin-top: 1.2rem;
    margin-bottom: 1.6rem;
  }}
  .fl-section-eyebrow {{
    font-family: var(--mono); font-size: 0.7rem;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--alarm); margin-bottom: 0.45rem;
    font-weight: 500;
  }}
  .fl-section-eyebrow::before {{
    content: "§ ";
    color: var(--alarm);
    margin-right: 0.18rem;
    font-style: italic;
  }}
  .fl-section-title {{
    font-family: var(--serif-display); font-weight: 600;
    font-size: 2rem; line-height: 1.04;
    letter-spacing: -0.022em; margin: 0;
    font-variation-settings: "opsz" 96;
  }}
  .fl-section-deck {{
    font-family: var(--serif-body); font-style: italic;
    color: var(--ink-soft); max-width: 75ch;
    margin-top: 0.55rem; line-height: 1.55;
    font-size: 1.02rem;
    font-variation-settings: "opsz" 24;
  }}

  /* ---- Tabs ---- */
  div[data-baseweb="tab-list"] {{
    border-bottom: 1px solid var(--ink) !important;
    gap: 0 !important;
    margin-bottom: 1.8rem !important;
  }}
  div[data-baseweb="tab"] {{
    background: transparent !important;
    padding: 0.95rem 1.9rem !important;
    border: none !important;
    border-radius: 0 !important;
  }}
  div[data-baseweb="tab"]:not(:last-child) {{
    border-right: 1px solid var(--hairline) !important;
  }}
  div[data-baseweb="tab"] p {{
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    margin: 0 !important;
    font-weight: 500 !important;
  }}
  div[data-baseweb="tab"]:hover p {{ color: var(--ink) !important; }}
  div[data-baseweb="tab"][aria-selected="true"] p {{
    color: var(--ink) !important;
    font-weight: 600 !important;
  }}
  div[data-baseweb="tab-highlight"] {{
    background: var(--alarm) !important;
    height: 3px !important;
  }}
  div[data-baseweb="tab-border"] {{ display: none !important; }}

  /* ---- Buttons ---- */
  .stButton > button, .stDownloadButton > button {{
    background: var(--ink) !important;
    color: var(--newsprint) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    padding: 0.78rem 1.4rem !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: background 0.16s ease, color 0.16s ease;
  }}
  .stButton > button:hover, .stDownloadButton > button:hover {{
    background: var(--alarm) !important;
    border-color: var(--alarm) !important;
    color: var(--newsprint) !important;
  }}
  .stButton > button[kind="primary"] {{
    background: var(--alarm) !important;
    border-color: var(--alarm) !important;
  }}
  .stButton > button[kind="primary"]:hover {{
    background: var(--ink) !important;
    border-color: var(--ink) !important;
  }}

  /* ---- Selects + inputs ---- */
  div[data-baseweb="select"] > div {{
    background: var(--newsprint) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    font-family: var(--serif-body) !important;
  }}
  label, .stSelectbox label, .stTextInput label {{
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
  }}

  /* ---- Tables (Streamlit default; we mostly use custom HTML) ---- */
  div[data-testid="stDataFrame"] {{
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
  }}
  div[data-testid="stDataFrame"] [role="columnheader"] {{
    background: var(--ink) !important;
    color: var(--newsprint) !important;
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
  }}
  div[data-testid="stDataFrame"] [role="row"]:hover {{
    background: var(--newsprint-tint) !important;
  }}

  /* ---- Applicant card ---- */
  .fl-applicant {{
    border: 1px solid var(--ink);
    background: rgba(255,255,255,0.55);
    padding: 1.5rem 1.7rem;
    margin: 1.1rem 0 1.6rem 0;
    position: relative;
  }}
  .fl-applicant::before {{
    content: "DOSSIER · 005307";
    position: absolute;
    top: -0.6rem; left: 1.2rem;
    background: var(--newsprint);
    padding: 0 0.55rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    color: var(--alarm);
    font-weight: 600;
  }}
  .fl-applicant-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.15rem 2.2rem;
  }}
  .fl-applicant-grid.cols-5 {{ grid-template-columns: repeat(5, 1fr); }}
  .fl-field-label {{
    font-family: var(--mono); font-size: 0.66rem;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.22rem;
    font-weight: 500;
  }}
  .fl-field-value {{
    font-family: var(--serif-body); font-size: 1.02rem;
    color: var(--ink); line-height: 1.3;
  }}
  .fl-applicant-rule {{
    border-top: 1px dashed var(--hairline);
    margin: 1.35rem 0 1.15rem 0;
  }}

  /* ---- Decision badge with pulsing dot ---- */
  .fl-decision {{
    display: inline-flex;
    align-items: baseline;
    gap: 0.7rem;
    margin-top: 0.4rem;
    padding: 0.6rem 1.1rem;
    border: 1.5px solid var(--alarm);
    background: var(--newsprint);
    font-family: var(--mono);
    font-size: 0.82rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--alarm);
    font-weight: 600;
  }}
  .fl-decision .fl-dot {{
    width: 0.55rem; height: 0.55rem;
    background: var(--alarm); border-radius: 50%;
    display: inline-block;
    animation: fl-pulse 1.6s ease-in-out infinite;
    box-shadow: 0 0 0 0 rgba(193, 39, 45, 0.55);
  }}
  .fl-decision-meta {{
    color: var(--muted);
    font-weight: 400;
    letter-spacing: 0.14em;
  }}
  @keyframes fl-pulse {{
    0%   {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(193, 39, 45, 0.55); }}
    70%  {{ transform: scale(1.4); box-shadow: 0 0 0 7px rgba(193, 39, 45, 0); }}
    100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(193, 39, 45, 0); }}
  }}

  /* ---- Pull-quote (the Gemini hero shot) ---- */
  .fl-quote {{
    border-left: 3px solid var(--alarm);
    padding: 1.4rem 1rem 1.4rem 1.8rem;
    margin: 1.6rem 0 1rem 0;
    font-family: "Fraunces", "Noto Serif Devanagari", "Noto Serif Tamil",
                 "Noto Serif Bengali", Georgia, serif;
    font-style: italic;
    font-weight: 400;
    font-size: 1.62rem;
    line-height: 1.45;
    color: var(--ink);
    font-variation-settings: "opsz" 96, "SOFT" 30;
    background: linear-gradient(
      to right,
      rgba(193, 39, 45, 0.05) 0%,
      rgba(193, 39, 45, 0) 78%
    );
    text-indent: 0;
  }}
  .fl-quote::before {{
    content: "\\201C";
    color: var(--alarm);
    font-size: 2.6rem;
    line-height: 0;
    margin-right: 0.22rem;
    vertical-align: -0.45rem;
  }}
  .fl-quote-attr {{
    display: block;
    margin-top: 1.3rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    font-style: normal;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
  }}

  /* ---- Disparity inline rules in the table ---- */
  .fl-table-disparity {{
    width: 100%;
    border-collapse: collapse;
    font-family: var(--serif-body);
    font-size: 0.98rem;
    border: 1px solid var(--ink);
    margin-bottom: 1rem;
    background: rgba(255,255,255,0.5);
  }}
  .fl-table-disparity th {{
    background: var(--ink);
    color: var(--newsprint);
    text-align: left;
    padding: 0.65rem 0.95rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 500;
  }}
  .fl-table-disparity th.num {{ text-align: right; }}
  .fl-table-disparity td {{
    padding: 0.7rem 0.95rem;
    border-top: 1px solid var(--hairline);
    vertical-align: middle;
  }}
  .fl-table-disparity td.feature {{
    font-family: var(--mono);
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    color: var(--ink);
    width: 22%;
  }}
  .fl-table-disparity td.num {{
    text-align: right;
    font-family: var(--mono);
    font-feature-settings: "tnum" 1;
    color: var(--ink);
  }}
  .fl-table-disparity td.num.high {{
    color: var(--alarm);
    font-weight: 600;
  }}
  .fl-table-disparity td.num.low {{ color: var(--muted); }}
  .fl-table-disparity tr:hover td {{ background: var(--newsprint-tint); }}
  .fl-bar-cell {{ width: 24%; }}
  .fl-bar-track {{
    height: 7px;
    background: var(--newsprint-tint);
    border: 1px solid var(--hairline);
    position: relative;
  }}
  .fl-bar-fill {{
    height: 100%;
    background: var(--alarm);
  }}
  .fl-bar-fill.muted {{ background: var(--ink-soft); opacity: 0.45; }}

  /* ---- About-tab editorial block ---- */
  .fl-essay {{
    max-width: 68ch;
    font-family: var(--serif-body);
    font-size: 1.09rem;
    line-height: 1.68;
    color: var(--ink);
    font-variation-settings: "opsz" 24;
  }}
  .fl-essay h3 {{
    font-family: var(--serif-display); font-weight: 600;
    font-size: 1.45rem; margin-top: 2rem; margin-bottom: 0.6rem;
    letter-spacing: -0.012em;
  }}
  .fl-essay p {{ margin: 0 0 1rem 0; }}
  .fl-essay p:first-of-type::first-letter {{
    font-family: "Fraunces", Georgia, serif;
    font-size: 3.6rem;
    font-weight: 600;
    float: left;
    line-height: 0.86;
    margin: 0.32rem 0.55rem -0.2rem 0;
    color: var(--alarm);
    font-variation-settings: "opsz" 144;
  }}
  .fl-essay strong {{ color: var(--ink); font-weight: 600; }}
  .fl-essay em {{ font-style: italic; color: var(--ink-soft); }}

  /* ---- Caption ---- */
  .stCaption, [data-testid="stCaptionContainer"] {{
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    color: var(--muted) !important;
    letter-spacing: 0.05em !important;
  }}

  /* ---- Plotly chart heading row ---- */
  .fl-chart-grid-head {{
    font-family: var(--mono);
    font-size: 0.74rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink);
    border-bottom: 1px solid var(--ink);
    padding-bottom: 0.32rem;
    margin-bottom: 0.55rem;
    font-weight: 500;
  }}
  .fl-chart-meta {{
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.06em;
    margin-top: 0.35rem;
  }}
  .fl-chart-meta .fl-dpd-high {{ color: var(--alarm); font-weight: 600; }}

  /* Indian-script body lines should pick up the matched serif weight */
  :lang(hi), :lang(ta), :lang(bn) {{
    font-family: "Noto Serif Devanagari", "Noto Serif Tamil",
                 "Noto Serif Bengali", "Newsreader", serif !important;
  }}

  /* Hide noisy Streamlit-default rules between widgets */
  hr {{ border-color: var(--hairline) !important; }}

  /* Selection color matches the alarm rule */
  ::selection {{ background: var(--alarm); color: var(--newsprint); }}
</style>
"""
    )
