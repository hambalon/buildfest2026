"""Check that the pipeline works on the data file WITHOUT producing results.

Usage (from the repo root):
    python scripts/verify_pipeline.py            # newest .xlsx in data/
    python scripts/verify_pipeline.py --no-app   # skip the dashboard smoke test

Runs every step in memory and prints only structural checks: column headers,
counts, parse/match rates and PASS/WARN/FAIL. It prints no response values and
no analysis results, and writes nothing to outputs/. The output is safe to
share with teammates or paste into an AI tool when debugging.
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src import analyze, text_themes  # noqa: E402
from src import config as C  # noqa: E402
from src.clean import SMALL_GROUP, _best_scale, find_data_file, load_and_clean, norm_text  # noqa: E402

results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool | None, detail: str = "") -> None:
    status = "PASS" if ok else ("WARN" if ok is None else "FAIL")
    results.append((status, name, detail))
    print(f"[{status}] {name}" + (f": {detail}" if detail else ""))


def safe_error(e: BaseException) -> str:
    """Exception type + code location only; the message could contain data values."""
    tb = traceback.extract_tb(e.__traceback__)
    loc = next((f"{Path(f.filename).name}:{f.lineno}" for f in reversed(tb)
                if "site-packages" not in f.filename), "?")
    return f"{type(e).__name__} at {loc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--no-app", action="store_true")
    args = ap.parse_args()

    # ---- 1. File ------------------------------------------------------------
    path = find_data_file(args.file)
    xl = pd.ExcelFile(path)
    check("File found", True, path.name)
    check("Single sheet", len(xl.sheet_names) == 1 or None, f"{len(xl.sheet_names)} sheet(s)")
    raw = pd.read_excel(path, sheet_name=0, dtype=object)
    check("Shape", True, f"{raw.shape[0]} rows x {raw.shape[1]} columns")
    check("20 columns as expected", raw.shape[1] == 20 or None, str(raw.shape[1]))

    # Messiness counts (counts only)
    strs = raw.stack().map(lambda v: isinstance(v, str))
    cells = raw.stack()[strs]
    nbsp = int(cells.str.contains(" ").sum())
    semi = int(cells.str.contains(r";\s*$").sum())
    none_tok = int(cells.str.strip().str.lower().isin(C.MISSING_TOKENS).sum())
    cleaned = cells.map(norm_text)
    left_nbsp = int(cleaned.dropna().astype(str).str.contains(" ").sum())
    left_semi = int(cleaned.dropna().astype(str).str.contains(r";$").sum())
    check("Non-breaking spaces removed", left_nbsp == 0, f"{nbsp} cells before, {left_nbsp} after")
    check("Trailing semicolons removed", left_semi == 0, f"{semi} cells before, {left_semi} after")
    check("Placeholder tokens ('None', 'N/A'...) -> missing", True, f"{none_tok} cells")

    # ---- 2. Cleaning --------------------------------------------------------
    try:
        res = load_and_clean(path)
    except Exception as e:  # noqa: BLE001
        check("load_and_clean runs", False, safe_error(e))
        return 1
    check("load_and_clean runs", True)
    df = res.df
    print("\nColumn detection (header -> role):")
    for name, header in res.column_map.items():
        print(f"    {name:<17} <- {header}")
    unused = [h for h in raw.columns.map(lambda h: " ".join(str(h).split())) if h not in res.column_map.values()]
    for h in unused:
        print(f"    {'[unused]':<17} <- {h}")
    print()

    expected = {"language", "role", "training_date", "county", "recommend", "call_988"}
    missing = expected - set(res.column_map)
    check("Single-value columns detected", not missing, f"missing: {sorted(missing)}" if missing else "all 6")
    n_out = sum(c.startswith("outcome_") for c in res.likert_cols)
    n_asp = sum(c.startswith("aspect_") for c in res.likert_cols)
    check("3 outcome items (have a before version)", n_out == 3, str(n_out))
    check("3 aspect items (training quality)", n_asp == 3, str(n_asp))
    n_retro = len(res.retro_pairs)
    check("3 before (retrospective) items", n_retro == 3, str(n_retro))
    check("2 open-text columns", len(res.text_cols) == 2, str(len(res.text_cols)))
    check("Open-text columns named by question", set(res.text_cols) == {"text_valuable", "text_improve"} or None,
          ", ".join(res.text_cols))
    meta_only = all(h.lower() in C.IGNORE_HEADERS for h in unused)
    check("Unused columns are platform metadata only", meta_only or None, f"{len(unused)} unused")

    # Scale coverage per ordinal column (rates only)
    raw_norm = raw.copy()
    raw_norm.columns = [" ".join(str(c).split()) for c in raw.columns]
    raw_norm = raw_norm.apply(lambda c: c.map(norm_text))
    for col in res.likert_cols + list(res.retro_pairs) + (["call_988"] if "call_988" in df else []):
        rawcol = raw_norm[res.column_map[col]]
        answered = int(rawcol.notna().sum())
        mapped = int(df[col].notna().sum())
        scale, share = _best_scale(rawcol)
        label = "0-10" if col == "call_988" and res.call_988_scale == "0-10" else "1-5"
        unmapped_share = 1 - mapped / answered if answered else 0
        check(f"{col} answers mapped to {label}",
              True if mapped == answered else (None if unmapped_share <= 0.05 else False),
              f"{mapped}/{answered} mapped, scale={scale}, unmapped distinct="
              f"{rawcol[df[col].isna() & rawcol.notna()].nunique()}")

    if "recommend" in df:
        answered = int(raw_norm[res.column_map["recommend"]].notna().sum())
        mapped = int(df["recommend"].notna().sum())
        check("recommend parsed as 0-10", mapped == answered, f"{mapped}/{answered}")
    if "training_date" in df:
        answered = int(raw_norm[res.column_map["training_date"]].notna().sum())
        d = df["training_date"]
        odd = int(((d > pd.Timestamp.today()) | (d < pd.Timestamp("2020-01-01"))).sum())
        check("training_date parsed", int(d.notna().sum()) == answered, f"{int(d.notna().sum())}/{answered}")
        check("Dates within 2020-today", odd == 0 or None, f"{odd} outside")
    if "role_list" in df:
        multi = int((df["role_list"].map(len) > 1).sum())
        check("Role multi-select split", True, f"{df['role_list'].explode().nunique()} distinct roles, "
              f"{multi} respondents with >1 role")
    for g in ("county", "language"):
        if g in df:
            vc = df[g].value_counts()
            check(f"{g} grouping", True, f"{len(vc)} distinct, {int((vc < C.MIN_N).sum())} with n<{C.MIN_N}, "
                  f"{int((df[g + '_grp'] == SMALL_GROUP).sum())} responses folded")

    print("\nBefore/after pairs (confirm by reading the question text):")
    for r, l in res.retro_pairs.items():
        print(f"    {res.label(r)}\n      -> {res.label(l) if l else 'NO MATCH'}")
    check("All before items paired", all(res.retro_pairs.values()))
    after = [l for l in res.retro_pairs.values() if l]
    check("Retro pairs are one-to-one", len(after) == len(set(after)))
    print()

    # ---- 3. Analysis (shapes only) -----------------------------------------
    try:
        tables = analyze.run_all(res)
        check("analyze.run_all runs", True,
              ", ".join(f"{k}: {len(t)} rows" for k, t in tables.items()))
        for k, t in tables.items():
            if "suppressed" in t:
                check(f"{k} suppression applied", True, f"{int(t['suppressed'].sum())} of {len(t)} rows suppressed")
    except Exception as e:  # noqa: BLE001
        check("analyze.run_all runs", False, safe_error(e))

    # ---- 4. Text themes (coverage only) ------------------------------------
    try:
        for col in res.text_cols:  # the two questions (run_all also has *_by_audience tables)
            t = text_themes.theme_summary(res.df[col], col)
            unc = float(t.loc[t["theme"] == text_themes.UNCODED, "pct_of_answered"].iloc[0])
            check(f"themes for {col}", unc <= 40 or None,
                  f"{int(t['n_answered'].iloc[0])} answered, {unc:.0f}% uncoded (aim for <=40%)")
    except Exception as e:  # noqa: BLE001
        check("text_themes runs", False, safe_error(e))

    # ---- 5. Dashboard smoke test -------------------------------------------
    if not args.no_app:
        import logging
        logging.getLogger("streamlit").setLevel(logging.ERROR)
        from streamlit.testing.v1 import AppTest
        import os
        os.environ["DATA_FILE"] = str(path)
        at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=120).run()
        errs = len(at.exception)
        compare = [s for s in at.selectbox if s.label == "Compare by"]
        for i in range(len(compare[0].options) if compare else 0):  # every grouping
            [s for s in at.selectbox if s.label == "Compare by"][0].select_index(i)
            at.run()
            errs += len(at.exception)
        check("Dashboard renders all tabs/groups", errs == 0 and len(at.tabs) == 7,
              f"{errs} exception(s), {len(at.tabs)} tabs")

    n_fail = sum(s == "FAIL" for s, *_ in results)
    n_warn = sum(s == "WARN" for s, *_ in results)
    print(f"\nSummary: {len(results) - n_fail - n_warn} pass, {n_warn} warn, {n_fail} fail")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
