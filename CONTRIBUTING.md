# Contributing

Keep it simple: one branch per person per task, small pull requests, and **no data
or identifying info, ever**.

## Workflow

1. **Pull before you start**, every time:
   ```bash
   git checkout main
   git pull
   ```
2. **Make a branch named `<your-handle>/<task>`**:
   ```bash
   git checkout -b jsmith/county-chart
   ```
   Use your GitHub handle or initials, not your full name.
3. Commit small, clear changes:
   ```bash
   git add src/analyze.py
   git commit -m "Add % likely to call 988 by county"
   ```
   Use `git add <file>`, not `git add .`, so nothing slips in by accident.
4. Push and open a **pull request into `main`**:
   ```bash
   git push -u origin jsmith/county-chart
   ```
   Ask one teammate to look at it, then merge. Don't push straight to `main`.
5. After merging, go back to step 1 before your next task.

If `main` moved while you worked: `git checkout main && git pull && git checkout - && git merge main`.

## Privacy rules (non-negotiable)

- **Never commit data.** No `.xlsx`, `.csv`, exports, screenshots of raw rows, or
  copied survey responses. `.gitignore` blocks the common file types, but check
  `git status` before every commit anyway.
- **No personal names anywhere**: not in commits, code, comments, docs, slides,
  file names or branch names. Judging is anonymous, so leave out team member
  names, school names, emails and anything else that identifies us. Use the team
  number only where the deliverable requires it.
- **No identifying info about respondents.** Report groups only with n ≥ 10
  (enforced by `MIN_N` in `src/config.py`). Don't quote open-text answers that
  could identify someone (names, places, specific events). Paraphrase instead.
- **Notebooks:** clear all outputs before committing (Jupyter: *Edit → Clear All
  Outputs*; VS Code: *Clear All Outputs*), because outputs can contain data.
- **AI tools:** never paste raw survey rows or open-text answers into ChatGPT,
  Claude or similar tools. Share column headers, code, error messages or
  aggregate tables only. Log every meaningful AI use in [docs/AI_LOG.md](docs/AI_LOG.md).
- **Secrets** go in `.env` (gitignored), never in code.

If something sensitive gets committed by mistake, **tell the team right away**.
Don't just delete it in a new commit, because it stays in the git history.

## Pre-commit check

The repo ships a guard hook. Turn it on once per clone:
```bash
git config core.hooksPath .githooks
```
It blocks commits of `.xlsx`/`.csv`/other data files, anything in `data/` or `outputs/`,
and notebooks with saved outputs. Still look before every commit:

```bash
git status                 # only expected files?
git diff --cached --stat   # no .xlsx/.csv/outputs?
```
