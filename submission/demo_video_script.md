# Demo Video Script — FairLoan India

**Length:** ~90 seconds (cap is 3 minutes for the submission, but tight wins)
**Recording tool:** macOS QuickTime Player → File → New Screen Recording (or Cmd+Shift+5)
**Voiceover:** Record in QuickTime separately, or use the screen-recording mic
**Resolution:** 1920×1080, 30fps, MP4
**Upload:** YouTube, set to **Unlisted**

---

## Pre-flight checklist

```bash
cd /Volumes/Amitesh/Google/fairloan-india
source .venv/bin/activate
set -a; source .env; set +a
streamlit run src/app.py --server.headless=false --server.port=8501
```

Open http://localhost:8501 — verify both tabs render.

Before recording, do a dry run of the click-flow once so you know exactly where to click without hesitating on screen.

---

## Shot list

### 0:00 – 0:15 — Open with Sarita

**Visual:** A still slide. Plain white background. Centered text:

> A woman in Bhilwara applies for a ₹50,000 loan.
> She is denied in 4 seconds.
> No reason. No human. No recourse.

Hold for 6 seconds.

**Voiceover:**
> "Forty percent of women applicants in tier-3 India see the same screen — denial in 4 seconds with no explanation. RBI has documented this pattern for 5 years. No Indian fintech today gives the citizen a reason."

(If filming a real screen-grab of a fintech app's denial flow is too risky for branding, use the still slide. The slide is more universal and avoids defamation.)

---

### 0:15 – 0:35 — The Audit dashboard

**Visual:**
1. Cut to the FairLoan India dashboard. Audit tab.
2. Pause on the disparity table for 3 seconds — viewer sees `demographic_parity_difference` of **0.747 (education), 0.320 (age), 0.177 (sex)**.
3. Pan to the Sex bar chart. Highlight the **8.8% female approval vs 26.5% male approval** with a callout circle (post-edit in iMovie).
4. Pan to the Age band bar chart. Highlight the gradient.

**Voiceover:**
> "FairLoan India audits the same kind of model on the universal fairness benchmark. The result: women are approved at one-third the rate of men. Applicants under 25 are approved at one-tenth the rate of those over 35. The dashboard surfaces this in two clicks."

---

### 0:35 – 1:05 — Citizen Lookup (the hero shot)

**Visual:**
1. Click the "Citizen Lookup" tab.
2. Select language dropdown: choose **Hindi**.
3. Pick the first denied applicant (Tier-3 woman archetype).
4. Show the applicant profile card.
5. Click the **"Why was I denied?"** button.
6. Pause 2 seconds while the spinner runs.
7. The validated counterfactuals table appears — read 1.5 seconds.
8. The Hindi explanation renders in the green success box.
9. **Hold on the Hindi explanation for 6 seconds.** This is the emotional payoff.

**Voiceover (over the 30-second segment):**
> "FairLoan finds three single-feature changes that would have flipped the model's decision — every one verified against the actual classifier, no hallucinated fixes. Then Gemini renders an empathetic explanation in the citizen's language."

When the Hindi text appears, **stop talking** and let the viewer read it. Silence is the punch.

---

### 1:05 – 1:20 — Stack and SDG callout

**Visual:** Cut to a still slide showing:

| | |
|---|---|
| **Modeling** | LightGBM + Fairlearn |
| **LLM** | Gemini 2.5 Flash (Hindi · Tamil · Bengali · English) |
| **Hosting** | Google Cloud Run · asia-south1 |
| **SDG** | 5 · 10 · 16 |
| **Source** | github.com/singlaamitesh/fairloan-india |

**Voiceover:**
> "Built end-to-end on Google AI tooling — Gemini 2.5 Flash for the vernacular layer, Cloud Run for hosting, Fairlearn for the metrics. SDG 5, 10, and 16. MIT license. The same engine becomes an Equity Dashboard for school-scholarship and government-scheme decisions."

---

### 1:20 – 1:30 — Close

**Visual:** Final still slide:

> **FairLoan India**
> *Indian credit decisions affect 1.4 billion people.*
> *They deserve to know why.*
>
> Submitted to Google Solution Challenge 2026 · India

Hold 4 seconds.

**Voiceover (optional):**
> "Submitted to Google Solution Challenge 2026 India. Thank you."

---

## After recording

1. Edit in iMovie or DaVinci Resolve Free.
2. Add the highlight callouts on the Audit-tab pan.
3. Render to MP4, 1080p, ≤ 30 MB if possible.
4. Upload to YouTube as **Unlisted**.
5. Copy the YouTube URL into `submission/links.txt`.

---

## Voiceover tips

- Record the voiceover in a separate audio pass; sync in editor. Easier than live narration.
- Keep volume +5 dB above background.
- One re-take per shot is normal. More than three on the same line means the script is wrong, not your delivery.
- Pause for 1 full second when the Hindi text appears. Let the viewer read.

## What NOT to do

- Don't show real fintech app screenshots that could imply defamation. Use the still slide for the open.
- Don't oversell — judges see hundreds of pitches. Understated + concrete > hyped + vague.
- Don't include the word "revolutionary," "AI-powered," or "disruptive."
- Don't pan / zoom for visual effect. The content carries the demo.
