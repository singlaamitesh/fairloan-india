# Solution Overview (≤ 2056 chars for the Hack2skill form)

---

**FairLoan India** audits Indian digital-lending classifiers for slice-level bias and gives every denied citizen a respectful, vernacular explanation of what would have flipped the decision.

**The problem.** Indian fintech lending apps (KreditBee, Dhani, ZestMoney) deny instant loans in seconds using ML classifiers. RBI's 2021 Working Group on Digital Lending and multiple investigations document systematic disparities by gender, region, and class. Denied applicants get one line: *"Your application could not be processed."* No reason. No recourse.

**What we built.**
1. **Audit dashboard** — slice-level approval heatmaps with Demographic Parity Difference and Equalized Odds Difference via Fairlearn. On the universal fairness benchmark (UCI Adult, ~45K rows, recast in Indian context) the audit surfaces a **17.7% gender gap, 32% age-band gap, 74% education gap**.
2. **Citizen Lookup** — pick a denied applicant, FairLoan finds single-feature changes that flip the model (each verified — no hallucinated fixes), then **Gemini 2.5 Flash** renders a 2-4 sentence empathetic explanation in **Hindi / Tamil / Bengali / English**: *"Sarita ji, aapka credit history sirf 2 mahine ka hai. Agar yeh 6 mahine hota, toh approval mil jaata."*

**Stack.** Python 3.12 · LightGBM · Fairlearn · Streamlit · Gemini 2.5 Flash · Docker · **Google Cloud Run** (asia-south1).

**Why it's unique.** No prior Solution Challenge entry in 4 years has tackled algorithmic fairness for Indian credit. Fairlearn auditing exists at IBM and academic labs; vernacular counterfactuals via Gemini are emerging in research — neither is in production for Indian citizens. FairLoan India unifies them in a deployable tool any journalist, regulator, or NGO can use today.

**SDG mapping.** SDG 5 · SDG 10 · SDG 16.

**Roadmap.** v2 partners with Sa-Dhan / Bharat Inclusion Initiative to audit a real microfinance classifier; add Home Credit Default Risk India; add caste slicing under consented-data MoU.
