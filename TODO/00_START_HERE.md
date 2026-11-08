# START HERE: Project Brief for Humans and AI Assistants

> **If you are an AI assistant:** read this whole file before any other TODO file.
> It holds the context, data dictionary and rules every stage depends on. Then open
> the stage file you were asked to work on and follow its steps in order.
> (AI coding tools working inside the repo also get the rules from `/AGENTS.md`.)

## 1. The project in one paragraph

BuildFest 2026 is a team competition. Our task is to analyze the **EveryMind
"Understanding 988" training survey**: about 1,300 participant evaluations of a
training about 988, the U.S. Suicide & Crisis Lifeline. We submit five deliverables:
a memo, an AI-use appendix, a slide deck, a 2-minute demo video and a technical
artifact (this repo and its Streamlit dashboard). **Deadline: Sunday, November 8,
2026, 9:00 AM ET.** Judging is **anonymous**.

## 2. Where things live

| Folder | Holds | Rule |
|---|---|---|
| `TODO/` | **Instructions**: what to do, in what order, how to check it | Tick boxes as you go. Don't write deliverable content here |
| `docs/` | **Deliverable drafts**: memo, AI appendix, deck outline, AI log, submission checklist | The single source for each deliverable's content |
| `src/` | Pipeline code. `src/config.py` holds every setting and team decision | Change settings only in `config.py` |
| `data/` | The confidential survey file (local only, gitignored) | Never commit, upload or share |
| `outputs/` | Generated tables and reports (gitignored) | Regenerate; don't commit |
| `notebooks/` | Scratch exploration | Clear outputs before committing (the hook enforces it) |

## 3. Stage map

| Stage | File | Depends on | Output |
|---|---|---|---|
| 01 | [01_setup_and_data_intake.md](01_setup_and_data_intake.md) | – | Working environment, data in place, hook on |
| 02 | [02_cleaning_and_validation.md](02_cleaning_and_validation.md) | 01 | Verified clean data + recorded decisions |
| 03 | [03_quantitative_analysis.md](03_quantitative_analysis.md) | 02 | Result tables + findings note in `docs/memo.md` |
| 04 | [04_open_text_themes.md](04_open_text_themes.md) | 02 | Validated theme counts for 2 open-text questions |
| 05 | [05_dashboard.md](05_dashboard.md) | 03, 04 | Polished Streamlit dashboard |
| 06 | [06_memo.md](06_memo.md) | 03, 04 | `Team#_Memo.pdf` from `docs/memo.md` |
| 07 | [07_ai_appendix.md](07_ai_appendix.md) | all (ongoing) | `Team#_AIAppendix.pdf` from `docs/ai_appendix.md` |
| 08 | [08_presentation_deck.md](08_presentation_deck.md) | 03, 04, 06 | `Team#_Presentation.pptx` from `docs/deck_outline.md` |
| 09 | [09_demo_video.md](09_demo_video.md) | 05 | `Team#_Demo.mp4` (≤ 2:00) |
| 10 | [10_submission.md](10_submission.md) | all | Everything submitted per `docs/SUBMISSION_CHECKLIST.md` |

03 and 04 can run in parallel. So can 06, 08 and 09 once 03–05 are stable.
**Suggested timeline:** 01–02 first; 03/04 next; 05 + 06 in parallel; 08/09 in the
morning; 10 by 8:00 AM ET to leave a buffer.

## 4. Non-negotiable rules (apply to every stage)

1. **The data is confidential.** `data/*.xlsx` and everything in `outputs/` is
   gitignored, and the pre-commit hook blocks data files. Never commit, upload,
   email or paste the data anywhere.
2. **AI assistants must never see raw survey rows or open-text answers.** Share
   only code, column headers, error messages, and aggregate tables with n ≥ 10.
   When an AI writes code that touches data, the human runs it locally and shares
   back aggregated output only. `scripts/verify_pipeline.py` output is safe to share.
3. **Small-group rule:** never report a group or metric where fewer than **10**
   people answered (`MIN_N` in `src/config.py`). Write "n<10" instead.
4. **Anonymity:** no personal names (team members, school, emails) in code, commits,
   docs, slides, file metadata, video or branch names. Use "Team #" only.
5. **No identifying quotes:** don't quote open-text answers that name a person,
   place, organization or specific incident. Paraphrase.
6. **Log AI use** as you go in [../docs/AI_LOG.md](../docs/AI_LOG.md): the prompt
   summary, what was produced, the errors, and what a human verified.
7. **Every number carries its n.** Questions have very different response counts.

## 5. Data dictionary (verified against the real file on 2026-11-07)

Source: `data/BuildFest_EveryMind_Survey_Data_FULL.xlsx`. A Microsoft Forms export:
1 sheet, about 1,300 rows × 20 columns. After `src/clean.py`, columns get these names
(run `python scripts/verify_pipeline.py` for current counts):

| Clean column | Question (sub-item text) | Type | Answered | Notes |
|---|---|---|---|---|
| *(ignored)* | Id, Start time, Completion time | – | – | Platform metadata |
| `language`, `language_grp` | Survey language | text | all | English (US) or Español (México) |
| `role`, `role_list` | "Are you a....?" | text; list | all | Multi-select (4 roles; 14 people chose >1) |
| `audience` | Derived from role | Students / Adults | all | Students = role contains "student" (~83%). The main comparison in every view |
| `training_date` | Date of the training | date | nearly all | |
| `county`, `county_grp` | County the training was affiliated with | text | all | Spelling variants merged → 7 counties; 3 with n<10 are pooled as "Other (n<10)" in `county_grp` |
| `outcome_01` | I can identify mental health challenges and crises. | 1–5 | all | After-training rating |
| `outcome_02` | I can describe 988 and how it works. | 1–5 | all | |
| `outcome_03` | I know when to use 988. | 1–5 | all | |
| `before_01` | I could identify mental health challenges and crises. | 1–5 | all | Retrospective "before"; paired with `outcome_01` |
| `before_02` | I could describe 988 and how it works. | 1–5 | all | Paired with `outcome_02` |
| `before_03` | I knew when to use 988. | 1–5 | all | Paired with `outcome_03` |
| `aspect_01` | The presenter(s) engaged the participants. | 1–5 | ~87% | Training quality; has non-standard labels (stage 02) |
| `aspect_02` | The presenter(s) knew the subject matter well. | 1–5 | ~86% | |
| `aspect_03` | The training was well organized. | 1–5 | ~86% | |
| `recommend`, `nps_group` | Likelihood to recommend the training | 0–10; category | ~97% | NPS = %9–10 − %0–6 |
| `call_988` | Likelihood to call 988 if they or someone else is in crisis | **0–10** | **~23% (≈290)** | Probably added to the form later. Always show n |
| `text_valuable` | What was the most valuable thing you learned during the training? | text | ~82% (1,063) | Open text |
| `text_improve` | How can we improve this training in the future? | text | ~50% (651) | Open text. "None"/"N/A" count as answers ("nothing to change") |

Current results (2026-11-08): see `docs/memo.md`. Headline: knowledge goals met (90–92% agree after);
students (83%) rate the training far lower than adults (NPS −2 vs +80), and student scores fell each quarter.

Naming rule: an agree/disagree item with a "before" version is `outcome_NN` and its
before version is `before_NN` (same NN). Agree items without one are `aspect_NN`.
Coding: Strongly disagree 1 … Strongly agree 5. "% agree" means 4 or 5.

## 6. Repo map

```
AGENTS.md / CLAUDE.md   Rules for AI coding tools (auto-read by Claude Code, Cursor, Copilot, etc.)
src/config.py           Section 1 = TEAM DECISIONS; section 2 = how to read the file
src/clean.py            load_and_clean(path | bytes) -> CleanResult(df, column_map, likert_cols, retro_pairs,
                        text_cols, call_988_scale, report); res.label(col) = question text
src/analyze.py          overall, retro_change, by_group(res, "audience"|"county"|"role"|"language", split=),
                        group_tests, trend, intent_gap, session_scorecard, quality_checks, sensitivity,
                        subset_988, ceiling; run_all(); safe_table()/export_tables() for sharing
src/text_themes.py      VALUABLE / IMPROVE theme rules (THEMES_BY_COLUMN); theme_summary; theme_by_group
src/insights.py         Plain-language takeaways for the dashboard Summary tab
app.py                  Streamlit dashboard, 7 tabs (streamlit run app.py, or start_dashboard.command/.bat)
docs/METHODS.md         Definitions, tests, privacy rules, limitations (also shown in the dashboard)
scripts/verify_pipeline.py  Structural checks only. Output is safe to share
scripts/crosscheck.py       Independent recomputation of 12 headline numbers from the raw Excel
scripts/validate_themes.py  Blind human check of the theme coder (sample / score)
scripts/build_deliverables.py  Builds TeamN_Memo.pdf, TeamN_AIAppendix.pdf, TeamN_TechnicalArtifact.zip with checks
scripts/make_fake_data.py   Fake file with the same layout. Use it for AI-assisted dev
tests/                  pytest suite on fake data (python -m pytest -q)
.githooks/pre-commit    Blocks data files and notebook outputs from being committed
```

All commands run from the repo root with the virtual environment active.

## 7. How to hand a stage to an AI chatbot

Paste, in this order: (1) this file, (2) the stage file, (3) the relevant source
file(s), and (4) any **aggregate** output the stage asks for. Then say:
*"Follow the stage file. Do not ask for raw data. Tell me which commands to run
locally and what aggregate output to paste back."* For development, the AI can
assume the layout produced by `scripts/make_fake_data.py`.
