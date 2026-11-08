# Methods and Definitions

How the 988 Training Insights tool turns the survey export into results. The dashboard
shows this page under **Data quality & methods**. Settings live in `src/config.py`.

## 1. Data and cleaning (`src/clean.py`)

| Step | What happens |
|---|---|
| Find the file | The newest `.xlsx` or `.csv` in `data/`, or a file uploaded in the dashboard (read in memory, never saved) |
| Detect columns | By header text and answer values, so a re-ordered or re-exported form still works. Platform columns (Id, Start/Completion time) are ignored. The result is printed in the cleaning report |
| Normalize text | Unicode normalization; non-breaking spaces, invisible direction marks and repeated spaces removed; trailing semicolons on multi-select roles removed |
| Missing values | Blank, "None", "N/A", "-" and similar are treated as missing, **except** in the two open-text questions, where "None"/"N/A" mean "nothing to add" and are kept as answers |
| Agree/disagree → numbers | Strongly disagree 1, Disagree 2, Neither 3, Agree 4, Strongly agree 5 (English and Spanish labels). Two non-standard labels found on the delivery items ("Very agree", "Satisfied", about 2% of those answers, likely an older form version) are treated as missing (team decision D1) |
| 0–10 questions | "Recommend" and "likely to call 988" are read as numbers 0–10 |
| Dates | Real Excel dates, Excel serial numbers and text dates are all accepted |
| County | Spelling variants are merged ("Montgomery County" = "Montgomery"). Counties with fewer than 10 responses are pooled as "Other (n<10)" |
| Role and audience | Roles are multi-select. **Audience** = "Students" if any chosen role contains "student", otherwise "Adults" |
| Item names | `outcome_01–03`: knowledge statements rated for *after*; `before_01–03`: the same statements rated for *before* (retrospective); `aspect_01–03`: delivery (presenter engagement, presenter knowledge, organization) |

## 2. Measures

| Measure | Definition |
|---|---|
| **% agree** | Share answering Agree or Strongly agree (4–5) among those who answered the item |
| **Knowledge after / before** | Average % agree across the three knowledge statements, after vs. before |
| **Before → after change** | Each person's after rating minus their before rating (1–5 scale), averaged over the three statements; "% rated higher" = share whose average change is above 0 |
| **Net Promoter Score (NPS)** | % scoring 9–10 minus % scoring 0–6 on "How likely are you to recommend…". Range −100 to +100 |
| **% likely to call 988** | Share scoring 7–10 on the 0–10 question (team decision D2) |
| **Delivery rating** | Average % agree across the three delivery items |
| **Session** | One training date in one county. Used for the session scorecard |
| **Flagged session** | A session with 10+ responses where NPS < 0, knowledge % agree after < 85%, or delivery % agree < 80% (adjustable in `config.py`) |

## 3. Statistical tests (`src/analyze.py`)

- **Before vs. after:** Wilcoxon signed-rank test on each person's paired ratings.
- **Group differences:** rank-based tests that suit survey scales. Mann-Whitney U for two
  groups (effect size: rank-biserial *r*) and Kruskal-Wallis H for three or more (effect size:
  epsilon²). Groups with fewer than 10 answers and pooled "Other"/"Not reported" groups are left
  out. "Likely a real difference" means p < 0.05. The effect size says whether it is also
  large enough to matter. Roles overlap (multi-select), so role p-values are approximate.
- **Knowledge vs. intent:** Spearman rank correlation between each knowledge rating and the
  0–10 likelihood to call 988, among people who answered both.
- **Robustness:** results are re-run without "straight-line" responders (identical answers to
  every agree/disagree item). People who answered the 988 question are compared with everyone
  else. The share already at the top before the training is reported (ceiling).
- **Independent cross-check:** `scripts/crosscheck.py` recomputes 12 headline numbers from the
  raw Excel with separate, simple code and compares them with the pipeline.

## 4. Automatic takeaways (`src/insights.py`)

The Summary tab's "What the data says" is generated from the same aggregate tables, so it
updates with new data and filters. It only uses groups of 10+, labels results under 30 as
*thin*, only calls a group difference real when its test gives p < 0.05 (and states the
effect size), compares sessions within the same audience, and pairs each gap with a
suggested action for staff to discuss.

## 5. Open-ended answers (`src/text_themes.py`)

Each answer is matched against transparent keyword rules (regular expressions, English and
Spanish) for its question. One answer can carry several themes; answers that match nothing
are "Other / uncoded". The rules were written from **word and phrase counts only**: ordinary
dictionary words that appear in at least 10 different answers. No individual answer was shown
to an AI tool. Accuracy is checked against a blind, human-coded sample with
`scripts/validate_themes.py`. Individual answers are never displayed or exported.

## 6. Privacy rules

- **Small-group rule:** any group, and any measure within a group, based on fewer than
  **10** answers is hidden and shown as "<10". This applies to every chart, table, filter
  combination and download.
- **Thin results:** results based on 10–29 answers (`THIN_N` = 30) are shown but labelled
  *thin*: in group charts, on the 988 tile and in the automatic takeaways.
- Only aggregate results are displayed or exported. No row-level data, no open-text answers.
- The data file stays on the user's computer. Uploads are read in memory and not saved.

## 7. Limitations to keep in mind

- **Retrospective self-report:** "before" ratings are given after the training. This avoids
  some biases of a separate pre-test, but recall and social-desirability bias can inflate
  gains. It measures *perceived* learning, not tested knowledge, and there is no comparison group.
- **988 question coverage:** the likelihood-to-call question was added to the form later
  (first answered April 2026) and has about 23% coverage. Results describe that subset.
- **Ceiling effects:** 14–22% were already at "Strongly agree" before, so they could not show a gain.
- **Audience mix:** students dominate later periods and some counties. Compare within audience
  before reading county or time differences as quality differences.
- **Small groups:** the Spanish-language survey (n = 19) and several counties are too small for
  firm conclusions.
- **Keyword themes** miss sarcasm, negation and unusual wording. About 30% of answers are uncoded.

## 8. Charts

Colors were checked for color-vision deficiency with a palette validator: before = orange,
after = blue; students = violet, adults = aqua. Every chart has a table view and value labels,
so color is never the only cue. Value labels switch between dark and light ink to match the
dashboard theme.
