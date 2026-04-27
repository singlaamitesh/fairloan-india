# FairLoan India

> **Bias audit + vernacular counterfactual explanations for Indian digital lending.**
> Submitted to [Google Solution Challenge 2026 — India](https://hack2skill.com/event/solution-challenge-2026) · Theme 4 (Unbiased AI Decision) · SDG 5 + 10 + 16.

Indian digital-lending apps approve or deny instant loans in seconds using ML
classifiers. RBI's 2021 Working Group on Digital Lending and several public
investigations have documented systematic disparities by gender, region, and
socioeconomic class — and denied applicants get no explanation. FairLoan India
is a public-interest dashboard that (a) audits a representative credit-risk
classifier on real public data for slice-level bias, (b) exposes those
disparities visually for journalists, regulators, and NGOs, and (c) renders a
respectful counterfactual explanation in the citizen's own language via Gemini.

## What it shows

| Tab | What you see |
|---|---|
| **Audit** | Slice-level approval-rate heatmap by sex, race, age band, education band, city tier. Each slice gets a Demographic Parity Difference and Equalized Odds Difference number. |
| **Citizen Lookup** | Pick a denied applicant. FairLoan finds single-feature changes that flip the model's decision (verified against the actual classifier — no hallucinated fixes), then asks Gemini to render a 2-4 sentence empathetic explanation in **Hindi, Tamil, Bengali, or English**. |
| **About** | Background, methodology, SDG mapping, stack. |

## Headline finding from the demo

On the universal fairness benchmark (UCI Adult Income, recast in Indian
context), the same family of model used by Indian fintechs approves men at
**~3× the rate of women** (Demographic Parity Difference = 17.7%) and
applicants over 35 at **~10× the rate of applicants under 26** (DPD = 32.0%).
The audit surfaces these numbers and the counterfactual layer tells each
denied citizen, in their own language, exactly which input change would have
flipped the decision.

## Stack

- **Python 3.12** · pandas · scikit-learn · LightGBM
- **[Fairlearn](https://fairlearn.org/)** for slice-level fairness metrics
- **[Streamlit](https://streamlit.io/)** for the dashboard
- **[Gemini 2.5 Flash](https://ai.google.dev/)** via the `google-genai` SDK for vernacular counterfactual rendering
- **Google Cloud Run** for the hosted MVP, **Docker** for the build
- **[UCI Adult Income](https://archive.ics.uci.edu/ml/datasets/adult)** as the public dataset (the universal fairness benchmark; ~45K rows after cleaning)

## Quick start (local)

```bash
# Clone
git clone https://github.com/<you>/fairloan-india.git
cd fairloan-india

# Python 3.12 venv (LightGBM + Streamlit don't have 3.14 wheels yet)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

# Train the baseline (downloads UCI Adult automatically, ~25s on a laptop)
python -m src.train

# Configure Gemini for vernacular counterfactuals (optional but recommended)
cp .env.example .env
# Edit .env and paste your Google AI Studio key

# Run the dashboard
streamlit run src/app.py
# Open http://localhost:8501
```

If `GEMINI_API_KEY` is not set, the Citizen Lookup tab falls back to a plain
English explanation — the audit dashboard works with no extra config.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Streamlit  (port 8080 on Cloud Run)                              │
│ ┌────────────────────────────────┬─────────────────────────────┐ │
│ │ Audit tab                      │ Citizen Lookup tab          │ │
│ │  - Plotly heatmap              │  - Persona picker           │ │
│ │  - Per-slice approval bars     │  - Counterfactual finder    │ │
│ │  - DPD / EOD scores            │  - Vernacular explanation   │ │
│ └──────────────┬─────────────────┴───────────────┬─────────────┘ │
│                ▼                                 ▼                │
│         src/audit.py                     src/counterfactual.py    │
│         (Fairlearn MetricFrame)          (validates flips,        │
│                                           calls Gemini)           │
│                ▲                                 ▲                │
│                └────────── src/train.py ────────┘                 │
│                            (LightGBM model +                      │
│                             holdout parquet)                      │
│                                  ▲                                │
│                       src/data_loader.py                          │
│                  (UCI Adult + Indian-context overlay)             │
└──────────────────────────────────────────────────────────────────┘
```

## Why UCI Adult? Why not a "real" Indian credit dataset?

The Adult dataset is the **most-cited benchmark in algorithmic-fairness
research** — every reviewer recognizes it, the demographic disparities are
well-documented, and it is downloadable directly from the UCI archive with
no auth. The bias signal it produces (gender × region × age × education
disparities) is the textbook fairness signal. The audit methodology and
Streamlit dashboard are dataset-agnostic; swapping in a real Indian credit
dataset requires only changing `src/data_loader.py`.

We chose this transparently rather than auditing a synthetic in-house model
on synthetic data ("auditing your own homework"). Roadmap items for v2 are
the Home Credit Default Risk India subset and a partnership with a microfinance
NGO to audit a real production classifier under MoU.

## Counterfactual integrity

The Citizen Lookup tab does **not** let Gemini invent feature changes.
The `find_counterfactuals` function in `src/counterfactual.py`:

1. Tries deterministic single-feature deltas (numeric: education years,
   hours per week, capital gains, age; categorical: occupation, education,
   marital status).
2. Each candidate is scored against the actual LightGBM model.
3. Only candidates whose model output crosses the 0.5 approval threshold
   are kept.
4. The validated changes are passed to Gemini with a system prompt that
   forbids invention of any other change.

This means the explanations Gemini renders are **all model-verified** —
the user never sees a hallucinated "fix."

## Deploy to Cloud Run

```bash
gcloud auth login
gcloud config set project <your-gcp-project>
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Build + push + deploy in one command
gcloud run deploy fairloan-india \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 3 \
  --port 8080
```

Cold start is ~2 seconds with `--min-instances 1` (recommended for the demo
window).

## SDG mapping

- **SDG 5 — Gender Equality** — surfacing and explaining gender disparities in algorithmic credit decisions.
- **SDG 10 — Reduced Inequalities** — extending the same audit to caste, region, age, and class slices.
- **SDG 16 — Strong Institutions** — providing the explainability layer (vernacular counterfactual explanations) that Indian banking regulation now requires of digital lenders.

## License

MIT. See `LICENSE`.

## Acknowledgments

- The fairness research community for the UCI Adult benchmark and the
  Fairlearn toolkit.
- RBI's 2021 Working Group on Digital Lending for the policy framing.
- The Google Solution Challenge 2026 India organizers.
