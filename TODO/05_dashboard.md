# Stage 05: Streamlit Dashboard (Technical Artifact)

**Starting point (2026-11-07):** built; passes an automated smoke test on the real file (0 exceptions,
all tabs, all group selections). **Nobody has visually reviewed it yet.**
**Depends on:** 03, 04. **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
A clean dashboard that EveryMind staff could use with future exports. It reads
whatever `.xlsx` is in `data/` and needs no code changes. It's also what the demo video shows.

## What exists (`app.py`)
- Loads via `load_and_clean()`, cached by file path and modification time.
- Sidebar filters: Language, County, Role (any of). Shows a warning and hides results when the
  filtered n < 10.
- Tabs:
  1. **Overview:** stat tiles (Responses, NPS, % likely to call 988 with n in the tooltip,
     average before→after change), recommend 0–10 distribution, % agree per Likert item.
  2. **Before vs. after:** grouped bars per pair (orange = before, blue = after), plus a table.
  3. **By group:** pick county/role/language and a metric; bars for groups with n≥10,
     plus a table with "<10" in place of suppressed n.
  4. **Open-text themes:** % of answered per theme for each question.
  5. **Data quality:** the cleaning report (column detection, pairs, counts).
- Colors: categorical blue `#2a78d6` / orange `#eb6834` (a colorblind-safe validated pair).

## Run
```bash
streamlit run app.py                                   # real data
DATA_FILE=outputs/FAKE_survey.xlsx streamlit run app.py   # fake data (safe to screen-share)
```

## Tasks
- [ ] **Visual review** in a browser, light and dark theme (Settings → Theme). Check
      label overlap, long question labels and empty charts.
- [ ] **Shorten labels:** `res.label()` already strips the matrix stem. Long sub-items may
      still wrap. Consider a `SHORT_LABELS` dict in `config.py` (e.g., `outcome_02` → "Can describe 988").
- [ ] **Retro tab:** add "% improved" per item as a second small chart or tile.
- [ ] **988 tile:** the n is only ~293. Make it visible under the tile, not just in the tooltip.
- [ ] **By group:** make sure the per-metric n is shown next to the chosen metric
      (`n_988` when the metric is `pct_likely_988`, etc.) and hide bars where the metric is blank.
- [ ] **Themes tab:** hide themes with < 10 mentions or mark them.
- [ ] **Optional:** a "Download summary tables (CSV)" button that exports aggregates only.
      **Never offer row-level downloads.**
- [ ] **Optional:** an upload widget (`st.file_uploader`) as an alternative to `data/`.
      If added, keep the uploaded file in memory only.
- [ ] Never show raw open-text answers or row-level tables anywhere in the app.
- [ ] After changes: `python scripts/verify_pipeline.py` (includes the dashboard smoke test).

## Acceptance criteria
- 0 exceptions in `verify_pipeline.py`. Visually checked in both themes.
- No group or metric with n<10 visible under any filter combination.
- No row-level data or quotes visible anywhere.

## Pitfalls for AI assistants
- Streamlit ≥1.46: use `width="stretch"`, not `use_container_width` (deprecated).
- Keep data logic in `src/`. `app.py` should only call `analyze.*` / `text_themes.*`.
- Cache keys must include the file's mtime so updated data reloads.

## AI prompt template
> Using 00_START_HERE.md, 05_dashboard.md and the attached `app.py` + `src/analyze.py`,
> implement <task>. Develop against the layout of `scripts/make_fake_data.py`. Return
> the full updated `app.py`. Keep the n<10 suppression intact.
