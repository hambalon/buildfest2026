# Stage 05: Streamlit Dashboard (Technical Artifact)

> **Status (2026-11-08): rebuilt as the final artifact.** 7 tabs (Summary with auto-takeaways, Knowledge
> gains, Intent to call 988, Audiences & communities, Trends & sessions, Participant voice, Data quality &
> methods), upload box, date filter, audience split, session scorecard, Excel+CSV download (aggregates only).
> Tested: every control on Python 3.9 and 3.14, real and fake data, 0 exceptions. **Remaining human
> task:** one visual pass of the final version in light and dark mode (the earlier review covered the
> previous version).
>
> **Update 2 (2026-11-08):** a *Filtered view* note lists active filters, and the download records
> them; analysis and download are cached per file + filters (reruns ~5x faster); session scorecard
> lists flagged sessions first (shaded) and marks *thin* sessions (n < 30).
>
> **Update (2026-11-08):** chart value labels now follow the light/dark theme; the Summary tab opens
> with a guide to every tab, and each tab starts with its purpose; "What the data says" is grouped
> (working / gaps / watch / caveats) with n, *thin* flags (n < 30) and suggested actions; CSV
> exports accepted; 14 altered exports pass end to end (see tests/test_pipeline.py).

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
- [x] **Visual review** in a browser, light and dark theme (Settings → Theme). Check
      label overlap, long question labels and empty charts. *(Done 2026-11-07 on fake data: all
      tabs, both themes, a county filter and the download button.)*
- [x] **Shorten labels:** `res.label()` already strips the matrix stem. Long sub-items may
      still wrap. Consider a `SHORT_LABELS` dict in `config.py` (e.g., `outcome_02` → "Can describe 988").
      *(Done: `SHORT_LABELS` in config.py section 3; full question stays in tooltips.)*
- [x] **Retro tab:** add "% improved" per item as a second small chart or tile.
- [x] **988 tile:** the n is only ~293. Make it visible under the tile, not just in the tooltip.
      *(n is now shown under the NPS and retro tiles too.)*
- [x] **By group:** make sure the per-metric n is shown next to the chosen metric
      (`n_988` when the metric is `pct_likely_988`, etc.) and hide bars where the metric is blank.
- [x] **Themes tab:** hide themes with < 10 mentions or mark them.
- [x] **Optional:** a "Download summary tables (CSV)" button that exports aggregates only.
      **Never offer row-level downloads.** *(Sidebar button: zip of aggregate CSVs, small counts as "<10".)*
- [x] **Optional:** an upload widget (`st.file_uploader`) as an alternative to `data/`.
      If added, keep the uploaded file in memory only.
- [x] Never show raw open-text answers or row-level tables anywhere in the app.
- [x] After changes: `python scripts/verify_pipeline.py` (includes the dashboard smoke test).

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
