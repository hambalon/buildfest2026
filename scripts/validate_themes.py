"""Check the keyword theme coder against human coding (for humans only).

Step 1, make a blind sample (50 random answers per open-text question):
    python scripts/validate_themes.py sample
  -> outputs/theme_validation.xlsx   (one sheet per question, gitignored)
  Open it locally. For each answer, put 1 in every theme column that applies
  (leave blank otherwise). Do NOT paste these answers into any AI tool.

Step 2, score agreement once the sheet is filled in:
    python scripts/validate_themes.py score
  Prints, per theme: % agreement, precision and recall of the coder vs the
  human. Aggregates only, so the output is safe to share and to quote in the
  AI appendix.

The sample is reproducible (fixed seed), and the coder's own labels are not in
the sheet, so the human coding is blind.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src import config as C  # noqa: E402
from src import text_themes as T  # noqa: E402
from src.clean import load_and_clean  # noqa: E402

SHEET = C.OUTPUT_DIR / "theme_validation.xlsx"
SEED, N = 988, 50


def sample(res) -> None:
    C.OUTPUT_DIR.mkdir(exist_ok=True)
    with pd.ExcelWriter(SHEET, engine="openpyxl") as xw:
        for col in res.text_cols:
            answered = res.df[col].dropna()
            pick = answered.sample(min(N, len(answered)), random_state=SEED)
            themes = list(T.themes_for(col))
            sheet = pd.DataFrame({"row_id": pick.index, "answer": pick.values})
            for t in themes:
                sheet[t] = pd.NA
            sheet["notes"] = ""
            sheet.to_excel(xw, sheet_name=col[:31], index=False)
    print(f"Wrote blind sample ({N} per question) to {SHEET}.")
    print("Fill in 1s locally, then run: python scripts/validate_themes.py score")


def score(res) -> int:
    if not SHEET.exists():
        print("No sheet yet. Run the 'sample' step first.")
        return 1
    rows = []
    for col in res.text_cols:
        human = pd.read_excel(SHEET, sheet_name=col[:31]).set_index("row_id")
        coded = T.code_responses(res.df.loc[human.index, col], col)
        filled = human.drop(columns=["answer", "notes"], errors="ignore")
        if filled.isna().all().all():
            print(f"{col}: sheet not filled in yet.")
            continue
        for theme in T.themes_for(col):
            h = filled[theme].fillna(0).astype(float).astype(bool)
            c = coded[theme]
            tp, fp, fn = int((h & c).sum()), int((~h & c).sum()), int((h & ~c).sum())
            rows.append({"question": col, "theme": theme, "n_coded_by_human": int(h.sum()),
                         "agreement_pct": round((h == c).mean() * 100, 1),
                         "precision_pct": round(tp / (tp + fp) * 100, 1) if tp + fp else float("nan"),
                         "recall_pct": round(tp / (tp + fn) * 100, 1) if tp + fn else float("nan")})
    if not rows:
        return 1
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))
    for q, g in out.groupby("question"):
        print(f"{q}: mean agreement {g['agreement_pct'].mean():.1f}% across {len(g)} themes (n = {N} answers)")
    print("\nPrecision = when the coder says a theme is present, how often the human agrees.")
    print("Recall = of the answers the human tagged with a theme, how many the coder found.")
    print("Improve patterns with low precision (too broad) or low recall (missing keywords).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate keyword themes against human coding.")
    ap.add_argument("step", choices=["sample", "score"])
    ap.add_argument("--file", help="Survey .xlsx (default: newest in data/)")
    a = ap.parse_args()
    res = load_and_clean(a.file)
    if a.step == "sample":
        sample(res)
        return 0
    return score(res)


if __name__ == "__main__":
    sys.exit(main())
