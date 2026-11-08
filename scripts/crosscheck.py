"""Independent cross-check of the headline numbers.

Usage (from the repo root):
    python scripts/crosscheck.py               # newest .xlsx in data/
    python scripts/crosscheck.py --file x.xlsx

Recomputes key results straight from the raw Excel file with deliberately simple,
separate code (plain string matching, no src/clean.py), then compares them with
what the pipeline/dashboard report. Any mismatch beyond rounding is a FAIL.
Prints aggregates only (whole-sample percentages and counts), never rows or text.

This guards against a whole class of errors in the AI-assisted pipeline (wrong
column detection, wrong label mapping, wrong denominators). It is written for the
current Microsoft Forms layout; if the questions change, update the KEYS below.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src import analyze  # noqa: E402
from src import config as C  # noqa: E402
from src.clean import find_data_file, load_and_clean  # noqa: E402

# Header fragments (lowercase) for each question in the current form.
KEYS = {
    "after_identify": ("statements", "identify mental health"),
    "after_describe": ("statements", "describe 988"),
    "after_when": ("statements", "when to use 988"),
    "before_identify": ("think back", "identify mental health"),
    "before_describe": ("think back", "describe 988"),
    "before_when": ("think back", "when to use 988"),
    "recommend": ("recommend",),
    "call_988": ("call 988",),
    "role": ("are you a",),
}
AGREE = {"agree", "strongly agree", "de acuerdo", "totalmente de acuerdo", "muy de acuerdo"}
ANSWERED_AGREE_SCALE = AGREE | {"disagree", "strongly disagree", "neither agree nor disagree",
                                "en desacuerdo", "totalmente en desacuerdo",
                                "ni de acuerdo ni en desacuerdo", "muy en desacuerdo"}


def simple(v) -> str:
    """Minimal independent normalization: lowercase, drop invisible characters."""
    if pd.isna(v):
        return ""
    s = str(v).replace(" ", " ").replace("‎", "").replace("‏", "")
    return " ".join(s.split()).strip().strip(";").lower()


def find(cols, parts) -> str | None:
    hits = [c for c in cols if all(p in simple(c) for p in parts)]
    return hits[0] if len(hits) == 1 else None


def independent(path: Path) -> dict[str, float]:
    raw = pd.read_excel(path, sheet_name=0, dtype=object)
    cols = {k: find(raw.columns, v) for k, v in KEYS.items()}
    missing = [k for k, v in cols.items() if v is None]
    if missing:
        raise SystemExit(f"Cross-check can't find these questions (update KEYS): {missing}")
    out = {"Responses": float(len(raw))}
    for k in ("after_identify", "after_describe", "after_when", "before_identify",
              "before_describe", "before_when"):
        vals = raw[cols[k]].map(simple)
        answered = vals.isin(ANSWERED_AGREE_SCALE)
        out[f"% agree {k}"] = vals[answered].isin(AGREE).mean() * 100
    rec = pd.to_numeric(raw[cols["recommend"]], errors="coerce").dropna()
    out["Recommend n"] = float(len(rec))
    out["NPS"] = ((rec >= 9).mean() - (rec <= 6).mean()) * 100
    c988 = pd.to_numeric(raw[cols["call_988"]], errors="coerce").dropna()
    out["988 n"] = float(len(c988))
    out["% likely to call 988"] = (c988 >= C.CALL_988_LIKELY_MIN_0_10).mean() * 100
    out["% students"] = raw[cols["role"]].map(simple).str.contains("student").mean() * 100
    return out


def pipeline(path: Path) -> dict[str, float]:
    res = load_and_clean(path)
    df = res.df
    ov = analyze.overall(res).set_index("metric")["value"]
    rc = analyze.retro_change(res).set_index("item")
    names = {"outcome_01": "identify", "outcome_02": "describe", "outcome_03": "when"}
    out = {"Responses": float(len(df))}
    for item, short in names.items():
        out[f"% agree after_{short}"] = analyze.top_box(df[item])
        before = [r for r, l in res.retro_pairs.items() if l == item][0]
        out[f"% agree before_{short}"] = analyze.top_box(df[before])
        assert abs(rc.loc[item, "top_box_after"] - out[f"% agree after_{short}"]) < 0.01
    out["Recommend n"] = float(ov["Recommend: n answered"])
    out["NPS"] = float(ov["Net Promoter Score"])
    out["988 n"] = float(ov["Likely to call 988: n answered"])
    out["% likely to call 988"] = float(ov["Likely to call 988: % likely"])
    out["% students"] = (df["audience"] == "Students").mean() * 100
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    path = find_data_file(ap.parse_args().file)
    a, b = independent(path), pipeline(path)
    print(f"{'Metric':<28}{'Independent':>13}{'Pipeline':>11}  Result")
    fails = 0
    for k in a:
        tol = 0.0 if k.endswith(" n") or k == "Responses" else 0.11  # pipeline rounds to 0.1
        ok = abs(a[k] - b[k]) <= tol
        fails += not ok
        print(f"{k:<28}{a[k]:>13.1f}{b[k]:>11.1f}  {'PASS' if ok else 'FAIL'}")
    print(f"\n{len(a) - fails} of {len(a)} headline numbers match an independent recomputation.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
