# data/ (local only, never committed)

Put the survey file here on **your own machine**:

```
data/BuildFest_EveryMind_Survey_Data_FULL.xlsx
```

- The data is **confidential**. Everything in this folder except this README is
  gitignored, and so is every `*.xlsx` / `*.csv` anywhere in the repo.
- Get the file from the official BuildFest source. Do **not** share it through
  GitHub, Slack, email attachments or AI chat tools.
- Any `.xlsx` filename works. If several are here, the scripts use the **most
  recently modified** one. To force a specific file:
  `DATA_FILE=path/to/file.xlsx python -m src.clean`
- Updated export? Replace the file here. The dashboard picks it up on its own. Or upload it
  with **Use a different survey export** in the dashboard sidebar (read in memory, never saved).
- No data yet? `python scripts/make_fake_data.py` writes a FAKE file to
  `outputs/FAKE_survey.xlsx` for testing (see the main README).
