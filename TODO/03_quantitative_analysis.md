# Stage 03: Quantitative Analysis

**Starting point (2026-11-07):** code built and runs on the real file. **Results have not been generated
or reviewed yet.** **Depends on:** 02 (decisions D1–D2 made).
**Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
Produce defensible numbers for the memo and deck. How much did self-rated knowledge
change? How likely are people to call 988 and to recommend the training? Do
results differ by county, role or language? Every number has its n, and n<10 is suppressed.

## What exists (`src/analyze.py`)
| Function | Output file | Contents |
|---|---|---|
| `overall(res)` | `outputs/overall.csv` | Responses; recommend n, mean, NPS; 988 n, % likely, mean; retro change n, mean, % improved |
| `retro_change(res)` | `outputs/retro_change.csv` | Per pair: n, before/after mean, mean change, % improved/same/declined, % agree before/after, Wilcoxon p |
| `by_group(res, "county")` | `outputs/by_county.csv` | Per `county_grp`: n, n_recommend, recommend mean, NPS, n_988, % likely 988, n_retro, mean retro change, `pct_agree_outcome_*` / `pct_agree_aspect_*` |
| `by_group(res, "role")` | `outputs/by_role.csv` | Same, per role. Multi-select respondents count in each role |
| `by_group(res, "language")` | `outputs/by_language.csv` | Same, per language |

Suppression: a whole group is blanked if n<10. Each metric is also blanked if fewer than
10 people in that group answered it. **Expect `pct_likely_988` to be blank for small groups.
Only 293 people answered 988 overall.**

## Tasks
- [x] Run: `python -m src.analyze` (also reruns cleaning).
- [x] Read all five CSVs. Write a 5–10 bullet **findings note** in `docs/memo.md`
      under "Key findings", each with its n.
- [x] **Retro change:** report mean change (1–5 scale), % improved, and % agree
      before vs after for each of the 3 outcome items. Cite the Wilcoxon p as "p < 0.001"
      style, never as 0.
- [x] **988 subset check:** only ~23% answered `call_988`. Compare that subset to
      everyone else on recommend mean and retro change (a quick script or notebook,
      output aggregates only). If they differ, say so in limitations.
- [x] **Group differences:** for county, role and language, note the largest and smallest
      values among *non-suppressed* groups. With n differences this large, describe them
      as descriptive, not significant, unless you add a test. Optional test: Kruskal-Wallis
      on retro change across groups with n≥10 (`scipy.stats.kruskal`).
- [x] **Training quality (`aspect_01`–`03`):** % agree for presenter engagement, knowledge
      and organization. Each has its own n (about 1,120–1,150).
- [x] **Optional: trend over time.** Monthly n and mean retro change by `training_date`.
      Use only months with n≥10.
- [x] **Optional: ceiling check.** Share of people already at 5 "before". They can't
      improve, so mean change understates the effect for them.
- [ ] Sanity-check 3 numbers by hand in Excel (e.g., overall % agree for `outcome_03` and
      NPS). Record this in `docs/AI_LOG.md`.

*Done 2026-11-07: findings 1–7 are in `docs/memo.md`. New tables from `python -m src.analyze`:
`subset_988.csv` (Mann-Whitney), `ceiling.csv`, `trend_monthly.csv` (months n≥10 only) and
`group_tests.csv` (Kruskal-Wallis, pooled "Other"/"Not reported" excluded).*

## Interpretation rules (put these in the memo methods/limitations)
- **Retrospective pre-test:** "before" ratings were given *after* the training.
  This avoids response-shift bias but is subject to recall and social-desirability
  bias. No control group, so don't claim causation; say "participants reported…".
- Likert data is ordinal. Lead with "% agree" and "% improved"; mean change is secondary.
- NPS = % promoters (9–10) − % detractors (0–6), from −100 to +100.
- Role groups overlap (multi-select), so they don't sum to the total.
- "Other (n<10)" pools 6 small counties. Don't interpret it as one place.

## Acceptance criteria
- Findings note in `docs/memo.md` with n on every number.
- 3 hand-checked numbers match.
- No suppressed value appears anywhere in the docs.

## AI prompt template
> Using 00_START_HERE.md and 03_quantitative_analysis.md, here are the aggregate
> output tables (all groups n≥10): `<paste overall.csv, retro_change.csv, by_*.csv>`.
> Draft 5–10 plain-language findings for a nonprofit audience. Include n for each, flag
> limitations, and don't claim causation or significance the tables don't support.
