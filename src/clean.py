"""Load and clean the EveryMind 988 training survey.

Usage (from the repo root):
    python -m src.clean                 # cleans the newest .xlsx in data/
    python -m src.clean --file path.xlsx

What it does:
  1. Finds the newest .xlsx in data/ (or uses --file / the DATA_FILE env var).
  2. Normalizes text: Unicode NFKC, non-breaking spaces, repeated whitespace,
     stray/trailing semicolons, and placeholder values like "None" -> missing.
  3. Detects what each column is from headers and values, and names it:
       outcome_NN  agree item that has a "before" version (after-training rating)
       before_NN   the retrospective "before the training" version of outcome_NN
       aspect_NN   agree item without a "before" version (training quality)
       text_valuable / text_improve   the open-text questions
       language, role, training_date, county, recommend, call_988
     Fix wrong guesses with COLUMN_OVERRIDES in src/config.py.
  4. Converts Likert / likelihood answers to 1-5, recommend to 0-10, dates to dates.
  5. Builds *_grp columns where missing -> "Not reported" and groups with fewer
     than MIN_N responses -> "Other (n<MIN_N)".
  6. Writes outputs/survey_clean.csv, outputs/clean_meta.json and
     outputs/cleaning_report.md (all gitignored).

Privacy: the console shows only counts and column headers, never response values.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src import config as C

NOT_REPORTED = "Not reported"
SMALL_GROUP = f"Other (n<{C.MIN_N})"


# --------------------------------------------------------------------------- #
# Result container
# --------------------------------------------------------------------------- #
@dataclass
class CleanResult:
    df: pd.DataFrame
    source_file: str
    column_map: dict[str, str] = field(default_factory=dict)   # clean col -> raw header
    likert_cols: list[str] = field(default_factory=list)       # outcome_* then aspect_*
    retro_pairs: dict[str, str | None] = field(default_factory=dict)  # before_NN -> outcome_NN
    text_cols: list[str] = field(default_factory=list)
    call_988_scale: str = "1-5"                                # "1-5" labels or "0-10" numeric
    report: list[str] = field(default_factory=list)            # safe to print
    private_report: list[str] = field(default_factory=list)    # file only

    def label(self, col: str) -> str:
        """Short question text for a cleaned column (matrix stem removed)."""
        return short_label(self.column_map.get(col, col))


# --------------------------------------------------------------------------- #
# Finding and loading the file
# --------------------------------------------------------------------------- #
def find_data_file(path: str | Path | None = None) -> Path:
    """Explicit path > DATA_FILE env var > newest .xlsx in data/."""
    if path:
        return Path(path)
    if os.environ.get("DATA_FILE"):
        return Path(os.environ["DATA_FILE"])
    files = [p for p in C.DATA_DIR.glob("*.xlsx") if not p.name.startswith("~$")]
    if not files:
        raise FileNotFoundError(
            f"No .xlsx file found in {C.DATA_DIR}. See data/README.md for where to put it."
        )
    return max(files, key=lambda p: p.stat().st_mtime)


# --------------------------------------------------------------------------- #
# Text normalization
# --------------------------------------------------------------------------- #
_WS = re.compile(r"\s+")
_INVISIBLE = re.compile("[​-‏‪-‮⁠-⁩﻿]")
_MATRIX_SPLIT = re.compile(r"[.?:]\s?\.(?=\S)")  # Forms matrix header "Question?.Sub-item"


def short_label(header: str) -> str:
    """'Please tell us ... statements..I know when to use 988.' -> 'I know when to use 988.'"""
    parts = _MATRIX_SPLIT.split(header)
    return parts[-1].strip() if len(parts) > 1 else header


def norm_text(value, missing_tokens=None):
    """Normalize one cell. Returns a clean string or pd.NA."""
    missing_tokens = C.MISSING_TOKENS if missing_tokens is None else missing_tokens
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NA
    if not isinstance(value, str):
        return value  # numbers / datetimes pass through untouched
    s = unicodedata.normalize("NFKC", value)          # \xa0 -> space, fancy forms -> plain
    s = _INVISIBLE.sub("", s)  # zero-width, BOM, left-to-right marks (Forms adds ‎)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = _WS.sub(" ", s).strip()
    s = re.sub(r"\s*;\s*", ";", s).strip(";").strip()  # "A ; B;" -> "A;B"
    if s.lower() in missing_tokens:
        return pd.NA
    return s


_COUNTY_AFFIX = re.compile(r"\s+(county|co\.?)$|^condado de\s+")


def county_key(value: str) -> str:
    """'Montgomery County' / 'montgomery' / 'Condado de Montgomery' -> 'montgomery'."""
    key = _COUNTY_AFFIX.sub("", value.strip().lower()).strip()
    return C.COUNTY_ALIASES.get(key, key)


def standardize_county(series: pd.Series) -> pd.Series:
    """Merge spelling variants; each merged group shows its most common original spelling."""
    s = series.astype("string")
    keys = s.map(county_key, na_action="ignore")
    pairs = pd.DataFrame({"key": keys, "value": s}).dropna()
    display = pairs.groupby("key")["value"].agg(lambda v: v.value_counts().index[0])
    return keys.map(display).astype("string")


def norm_header(h) -> str:
    s = _INVISIBLE.sub("", unicodedata.normalize("NFKC", str(h)))
    return _WS.sub(" ", s).strip()


def _scale_key(s) -> str | None:
    """Lowercase key used to look a value up in an ordinal scale."""
    if s is pd.NA or s is None:
        return None
    s = str(s).lower().strip()
    s = re.sub(r"^\d+\s*[-–.:)]\s*", "", s)  # "5 - Strongly agree" -> "strongly agree"
    return s.strip(" .!")


# --------------------------------------------------------------------------- #
# Column detection
# --------------------------------------------------------------------------- #
def _best_scale(series: pd.Series) -> tuple[str | None, float]:
    """Which ordinal scale (if any) matches the values, and what share match."""
    vals = series.dropna()
    if vals.empty:
        return None, 0.0
    keys = vals.map(_scale_key)
    best, best_share = None, 0.0
    for name, mapping in C.SCALES.items():
        share = keys.isin(mapping.keys()).mean()
        if share > best_share:
            best, best_share = name, share
    return best, best_share


def _is_retro(header: str) -> bool:
    h = header.lower()
    return any(k in h for k in C.RETRO_KEYWORDS)


def detect_columns(df: pd.DataFrame) -> dict[str, str]:
    """Return {raw header: role}."""
    roles: dict[str, str] = {}
    taken: set[str] = set()

    for raw in df.columns:
        if raw in C.COLUMN_OVERRIDES:
            roles[raw] = C.COLUMN_OVERRIDES[raw]
            taken.add(C.COLUMN_OVERRIDES[raw])

    for raw in df.columns:
        if raw in roles:
            continue
        h = raw.lower()
        if h in C.IGNORE_HEADERS:
            roles[raw] = "ignore"
            continue
        scale, share = _best_scale(df[raw])
        is_scale = share >= C.SCALE_MATCH_THRESHOLD

        # 988 likelihood and recommend are checked before generic Likert
        if "call_988" not in taken and any(k in h for k in C.HEADER_KEYWORDS["call_988"]):
            roles[raw] = "call_988"
        elif "recommend" not in taken and any(k in h for k in C.HEADER_KEYWORDS["recommend"]):
            roles[raw] = "recommend"
        elif is_scale and scale == "agree":
            roles[raw] = "retro" if _is_retro(raw) else "likert"
        elif "call_988" not in taken and is_scale and scale == "likely":
            roles[raw] = "call_988"
        else:
            for role in ("language", "county", "training_date", "role"):
                if role not in taken and any(k in h for k in C.HEADER_KEYWORDS[role]):
                    roles[raw] = role
                    break
        if raw in roles and roles[raw] not in ("likert", "retro"):
            taken.add(roles[raw])

    # Open text: remaining string columns with long answers
    n_text = sum(1 for r in roles.values() if r.startswith("text_"))
    for raw in df.columns:
        if raw in roles:
            continue
        vals = df[raw].dropna()
        vals = vals[vals.map(lambda v: isinstance(v, str))]
        if not len(vals) or n_text >= 2:
            continue
        looks_like_dates = pd.to_datetime(vals, errors="coerce", format="mixed").notna().mean() > 0.8
        by_header = any(k in raw.lower() for k in C.TEXT_KEYWORDS)
        if not looks_like_dates and (by_header or vals.str.len().mean() >= C.TEXT_MIN_AVG_LEN):
            n_text += 1
            roles[raw] = f"text_{n_text}"
    return roles


def assign_names(columns, roles: dict[str, str]) -> tuple[dict[str, str], dict[str, str | None]]:
    """Give each detected column its clean name. Returns ({raw header: clean name},
    {before col: outcome col or None})."""
    likert = [c for c in columns if roles.get(c) == "likert"]
    retro = [c for c in columns if roles.get(c) == "retro"]
    raw_pairs = pair_retro_items({r: r for r in retro}, {l: l for l in likert})
    after_to_before = {l: r for r, l in raw_pairs.items() if l}

    names: dict[str, str] = {}
    pairs: dict[str, str | None] = {}
    k = a = u = 0
    for col in likert:  # keep survey order
        if col in after_to_before:
            k += 1
            names[col] = f"outcome_{k:02d}"
            names[after_to_before[col]] = f"before_{k:02d}"
            pairs[f"before_{k:02d}"] = f"outcome_{k:02d}"
        else:
            a += 1
            names[col] = f"aspect_{a:02d}"
    for col in retro:
        if col not in names:  # a before item with no matching after item
            u += 1
            names[col] = f"before_unpaired_{u:02d}"
            pairs[names[col]] = None
    used: set[str] = set()
    for col in columns:
        role = roles.get(col)
        if role and role.startswith("text_"):
            name = next((n for n, kws in C.TEXT_COLUMNS.items()
                         if n not in used and any(k in col.lower() for k in kws)), role)
            names[col] = name
            used.add(name)
        elif role and role not in ("likert", "retro", "ignore"):
            names[col] = role
    return names, pairs


def pair_retro_items(retro: dict[str, str], likert: dict[str, str]) -> dict[str, str | None]:
    """Match each retro item to its most similar 'after' Likert item by header text.

    retro / likert: {clean col: raw header}. Returns {retro col: likert col or None}.
    """
    raw_to_clean = {v: k for k, v in likert.items()}
    pairs: dict[str, str | None] = {}

    def strip_retro(h: str) -> str:
        h = short_label(h).lower()  # compare the sub-item text, not the shared question stem
        for k in C.RETRO_KEYWORDS:
            h = h.replace(k, "")
        return re.sub(r"[^a-z0-9áéíóúñ ]", " ", h)

    for rcol, rraw in retro.items():
        if rraw in C.RETRO_PAIR_OVERRIDES:
            pairs[rcol] = raw_to_clean.get(C.RETRO_PAIR_OVERRIDES[rraw])
            continue
        best, best_score = None, 0.0
        for lcol, lraw in likert.items():
            score = difflib.SequenceMatcher(None, strip_retro(rraw), strip_retro(lraw)).ratio()
            if score > best_score:
                best, best_score = lcol, score
        pairs[rcol] = best if best_score >= C.RETRO_PAIR_MIN_SIMILARITY else None
    return pairs


# --------------------------------------------------------------------------- #
# Value conversion
# --------------------------------------------------------------------------- #
def to_scale(series: pd.Series, scale: str) -> tuple[pd.Series, set[str]]:
    mapping = C.SCALES[scale]
    keys = series.map(_scale_key)
    out = keys.map(mapping)
    # Accept bare numbers 1-5 as already-coded answers
    numeric = pd.to_numeric(series, errors="coerce")
    out = out.fillna(numeric.where(numeric.between(1, 5)))
    unmapped = set(series[out.isna() & series.notna()].astype(str).unique())
    return out.astype("Float64"), unmapped


def is_numeric_0_10(series: pd.Series) -> bool:
    vals = series.dropna()
    num = pd.to_numeric(vals, errors="coerce")
    return len(vals) > 0 and num.between(0, 10).mean() >= C.SCALE_MATCH_THRESHOLD


def to_recommend(series: pd.Series) -> pd.Series:
    num = pd.to_numeric(series, errors="coerce")
    extracted = pd.to_numeric(series.astype("string").str.extract(r"(\d+(?:\.\d+)?)")[0], errors="coerce")
    num = num.fillna(extracted)
    return num.where(num.between(0, 10)).astype("Float64")


def to_date(series: pd.Series) -> pd.Series:
    """Handles real Excel dates, Excel serial numbers, and date strings."""
    def one(v):
        if v is pd.NA or v is None:
            return pd.NaT
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return (pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(v))
                    if 30000 <= v <= 60000 else pd.NaT)
        return pd.to_datetime(v, errors="coerce")  # datetime, Timestamp or string
    return pd.to_datetime(series.map(one), errors="coerce").dt.normalize()


def group_small(series: pd.Series, min_n: int = C.MIN_N) -> pd.Series:
    s = series.astype("string").fillna(NOT_REPORTED)
    counts = s.value_counts()
    small = counts[(counts < min_n) & (counts.index != NOT_REPORTED)].index
    return s.where(~s.isin(small), SMALL_GROUP)


# --------------------------------------------------------------------------- #
# Main pipeline
# --------------------------------------------------------------------------- #
def load_and_clean(path: str | Path | None = None) -> CleanResult:
    src = find_data_file(path)
    raw = pd.read_excel(src, sheet_name=0, dtype=object)
    report: list[str] = []
    private: list[str] = []

    report.append(f"Source file: {src.name}")
    report.append(f"Raw shape: {raw.shape[0]} rows x {raw.shape[1]} columns")

    raw.columns = [norm_header(c) for c in raw.columns]
    junk = raw.columns.str.match(r"^Unnamed: \d+$") & raw.isna().all().to_numpy()
    raw = raw.loc[:, ~junk]  # drop blank spacer columns Excel sometimes adds
    df = raw.apply(lambda col: col.map(norm_text))

    empty = df.isna().all(axis=1)
    df = df[~empty].reset_index(drop=True)
    raw = raw[~empty].reset_index(drop=True)  # kept aligned for open-text re-reading
    report.append(f"Dropped {int(empty.sum())} completely empty rows -> {len(df)} responses")
    report.append(f"Exact duplicate rows (kept, review manually): {int(df.duplicated().sum())}")

    roles = detect_columns(df)
    names, retro_pairs = assign_names(list(df.columns), roles)
    out = pd.DataFrame(index=df.index)
    column_map: dict[str, str] = {}
    text_cols: list[str] = []

    report.append("")
    report.append("Column detection (fix in src/config.py COLUMN_OVERRIDES if wrong):")
    call_988_scale = "1-5"
    for rawcol in df.columns:
        role = roles.get(rawcol)
        if rawcol not in names:
            report.append(f"  {'[unused]':<17} {rawcol}")
            continue
        name = names[rawcol]
        column_map[name] = rawcol
        report.append(f"  {name:<17} {rawcol}")

        s = df[rawcol]
        if role in ("likert", "retro"):
            out[name], bad = to_scale(s, "agree")
        elif role == "call_988":
            if is_numeric_0_10(s):
                out[name] = to_recommend(s)  # same 0-10 parsing as recommend
                call_988_scale, bad = "0-10", set()
                report.append("      (0-10 numeric scale)")
            else:
                out[name], bad = to_scale(s, "likely")
        elif role == "recommend":
            out[name] = to_recommend(s)
            bad = set()
        elif role == "training_date":
            out[name] = to_date(s)
            bad = set()
        elif role.startswith("text_"):
            # "None" / "N/A" are real answers here ("nothing to change"), so keep them
            keep = raw[rawcol].map(lambda v: norm_text(v, C.MISSING_TOKENS - C.TEXT_ANSWER_TOKENS))
            n_kept = int(keep.notna().sum() - s.notna().sum())
            out[name] = keep.astype("string")
            text_cols.append(name)
            bad = set()
            if n_kept:
                report.append(f"      kept {n_kept} 'none'/'n/a' answers as responses")
        elif role == "county":
            out[name] = standardize_county(s)
            bad = set()
            n_before, n_after = s.nunique(), out[name].nunique()
            if n_before != n_after:
                report.append(f"      merged spelling variants: {n_before} -> {n_after} distinct names")
        else:  # language, role
            out[name] = s.astype("string")
            bad = set()

        n_missing = int(out[name].isna().sum())
        if n_missing:
            report.append(f"      missing/unparseable: {n_missing}")
        if bad:
            report.append(f"      {len(bad)} distinct values did not match the scale (see report file)")
            private.append(f"Unmatched values in {name}: {sorted(bad)[:10]}")

    for expected in ("language", "role", "training_date", "county", "recommend", "call_988"):
        if expected not in out.columns:
            report.append(f"  WARNING: no column detected for '{expected}'")

    # Roles can be multi-select ("A;B"); keep the list for exploding later
    if "role" in out.columns:
        out["role_list"] = out["role"].map(
            lambda v: [p.strip() for p in str(v).split(";") if p.strip()] if pd.notna(v) else []
        )
        report.append(f"Respondents selecting more than one role: {int((out['role_list'].map(len) > 1).sum())}")

    # Recommend -> NPS category
    if "recommend" in out.columns:
        out["nps_group"] = pd.cut(out["recommend"].astype(float), bins=[-0.1, 6, 8, 10],
                                  labels=["Detractor", "Passive", "Promoter"])

    # Date sanity
    if "training_date" in out.columns:
        d = out["training_date"]
        today = pd.Timestamp.today().normalize()
        odd = int(((d > today) | (d < pd.Timestamp("2020-01-01"))).sum())
        if d.notna().any():
            report.append(f"Training dates: {d.min().date()} to {d.max().date()}; "
                          f"{odd} outside 2020-today (check)")

    # Grouping columns with small-group rule
    for col in ("county", "language"):
        if col in out.columns:
            out[f"{col}_grp"] = group_small(out[col])
            n_small = int((out[f"{col}_grp"] == SMALL_GROUP).sum())
            n_groups = out[col].nunique()
            report.append(f"{col}: {n_groups} distinct values; {n_small} responses folded "
                          f"into '{SMALL_GROUP}'")

    if retro_pairs:
        report.append("")
        report.append("Before/after pairs (VERIFY by reading the question text; override in config):")
        for b, o in retro_pairs.items():
            report.append(f"  {b} <-> {o or 'NO MATCH'}")
            report.append(f"      before: {short_label(column_map[b])}")
            if o:
                report.append(f"      after:  {short_label(column_map[o])}")

    likert_cols = sorted([c for c in out.columns if c.startswith("outcome_")]) + \
        sorted([c for c in out.columns if c.startswith("aspect_")])
    return CleanResult(df=out, source_file=src.name, column_map=column_map,
                       likert_cols=likert_cols, retro_pairs=retro_pairs,
                       text_cols=text_cols, call_988_scale=call_988_scale, report=report, private_report=private)


def save_outputs(res: CleanResult) -> None:
    C.OUTPUT_DIR.mkdir(exist_ok=True)
    df = res.df.copy()
    if "role_list" in df.columns:
        df["role_list"] = df["role_list"].map(lambda xs: ";".join(xs))
    df.to_csv(C.OUTPUT_DIR / "survey_clean.csv", index=False)
    meta = {"source_file": res.source_file, "column_map": res.column_map,
            "likert_cols": res.likert_cols, "retro_pairs": res.retro_pairs,
            "text_cols": res.text_cols, "call_988_scale": res.call_988_scale}
    (C.OUTPUT_DIR / "clean_meta.json").write_text(json.dumps(meta, indent=2))
    body = "\n".join(res.report + ["", "## Details (do not paste into AI tools)"] + res.private_report)
    (C.OUTPUT_DIR / "cleaning_report.md").write_text("# Cleaning report\n\n```\n" + body + "\n```\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", help="Path to an .xlsx file (default: newest in data/)")
    args = ap.parse_args()
    res = load_and_clean(args.file)
    save_outputs(res)
    print("\n".join(res.report))
    print(f"\nWrote cleaned data and report to {C.OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
