# notebooks/

Scratch exploration only. Anything that matters for results goes into `src/` so the
dashboard and the memo use the same code.

Rules:
- **Clear all outputs before committing** (Jupyter: *Edit → Clear All Outputs*; VS Code:
  *Clear All Outputs*). Outputs can contain survey rows. The pre-commit hook blocks
  notebooks that still have outputs.
- Load data the same way the pipeline does, so cleaning stays consistent:
  ```python
  import sys; sys.path.insert(0, "..")
  from src.clean import load_and_clean
  res = load_and_clean()          # res.df, res.label("outcome_01"), res.retro_pairs ...
  ```
- Never print raw open-text answers in a cell you intend to commit.
- Name notebooks by task, not person: `03_county_differences.ipynb`.
