"""Simple keyword-based theme coding for the two open-text questions.

Usage (from the repo root):
    python -m src.text_themes        # writes outputs/themes_<question>.csv

How it works: THEMES is a library of theme -> regex patterns. THEMES_BY_COLUMN
picks which themes apply to each question (text_valuable / text_improve).
Each response is checked against those patterns, and a response can get several themes. Responses that match
nothing are counted as "Uncoded"; skim a sample of those by hand and add
keywords to improve coverage. Record what you checked in docs/AI_LOG.md.

These themes are a starting point written BEFORE seeing the responses.
Expect to edit them once the team has read a sample of answers.
Never paste raw responses into an AI tool (they may contain names).
"""
from __future__ import annotations

import re

import pandas as pd

from src import config as C
from src.clean import CleanResult, load_and_clean

# Theme -> regex patterns (English + Spanish). \b = word boundary.
THEMES: dict[str, list[str]] = {
    "Everything / all of it": [
        r"^\s*(everything|all of it|all|the whole (thing|training)|todo)\b",
    ],
    "Nothing / no changes": [
        r"^\s*(nothing|nada|no|n/?a|all good|none needed|no changes?|no suggestions?)\W*$",
        r"^\s*(nothing|none|nada|not really|no)\b[\s,.!-]*(really|at all|else|comes to mind|i can think of|it was|everything|great|good|perfect|excellent)",
        r"\b(it was|everything was) (great|perfect|excellent|good|wonderful)\b", r"\bkeep (it|doing)\b",
        r"\bnothing (to|i would) (change|add|improve)\b", r"\bno (changes|suggestions)\b",
    ],
    "Knowledge of 988 / what it is": [
        r"\b988\b", r"\bhotline\b", r"\blifeline\b", r"\bcrisis line\b", r"\bl[ií]nea\b",
        r"\bwhat happens when\b", r"\bhow (it|988) works\b",
    ],
    "Warning signs / how to help": [
        r"\bwarning signs?\b", r"\bsigns?\b", r"\bse[ñn]ales\b", r"\bhow to (help|respond|talk|ask)\b",
        r"\bask(ing)? (directly|about suicide)\b", r"\bintervene\b",
    ],
    "Resources / referrals": [
        r"\bresources?\b", r"\brecursos\b", r"\breferrals?\b", r"\bservices?\b",
        r"\bhandouts?\b", r"\bmaterials?\b", r"\bpamphlets?\b", r"\bflyers?\b",
    ],
    "Practice / role-play / examples": [
        r"\brole[- ]?plays?\b", r"\bpractice\b", r"\bscenarios?\b", r"\bexamples?\b",
        r"\bcase stud(y|ies)\b", r"\bejemplos?\b", r"\binteractive\b",
    ],
    "Presenter / facilitator": [
        r"\bpresenters?\b", r"\bfacilitators?\b", r"\btrainers?\b", r"\bspeakers?\b",
        r"\binstructors?\b", r"\bknowledgeable\b", r"\bpresentadora?\b",
    ],
    "Stigma / comfort talking about suicide": [
        r"\bstigma\b", r"\bcomfortable\b", r"\bconfiden(t|ce)\b", r"\bnormaliz",
        r"\bopen(ly)? (talk|discuss)", r"\bestigma\b",
    ],
    "Youth / schools / family": [
        r"\byouth\b", r"\bteens?\b", r"\bstudents?\b", r"\bkids\b", r"\bchildren\b",
        r"\bschools?\b", r"\bparents?\b", r"\bfamil(y|ies|ia)\b", r"\bj[oó]venes\b",
    ],
    "Length / time / pacing": [
        r"\blonger\b", r"\bshorter\b", r"\bmore time\b", r"\btoo (long|short|fast)\b",
        r"\brushed\b", r"\bpac(e|ing)\b", r"\bm[aá]s tiempo\b",
    ],
    "Language / accessibility / culture": [
        r"\bspanish\b", r"\bespa[ñn]ol\b", r"\btranslat", r"\binterpret", r"\blanguages?\b",
        r"\bcultur", r"\baccessib", r"\bcaptions?\b",
    ],
    "Logistics / tech / format": [
        r"\bzoom\b", r"\bvirtual\b", r"\bin[- ]person\b", r"\baudio\b", r"\bvideo\b",
        r"\bslides?\b", r"\bsound\b", r"\btechnical\b", r"\broom\b", r"\bschedul",
    ],
    "More training / follow-up": [
        r"\bmore (training|sessions|classes|info|information)\b", r"\bfollow[- ]?up\b",
        r"\badvanced\b", r"\brefresher\b", r"\bpart 2\b", r"\bm[aá]s (informaci[oó]n|capacitaci)",
    ],
}

# Which themes apply to which question. Columns not listed here use every theme.
THEMES_BY_COLUMN: dict[str, list[str]] = {
    "text_valuable": [  # "What was the most valuable thing you learned?"
        "Knowledge of 988 / what it is", "Warning signs / how to help", "Resources / referrals",
        "Practice / role-play / examples", "Presenter / facilitator",
        "Stigma / comfort talking about suicide", "Youth / schools / family", "Everything / all of it",
    ],
    "text_improve": [  # "How can we improve this training in the future?"
        "Nothing / no changes", "Length / time / pacing", "Practice / role-play / examples",
        "Resources / referrals", "Language / accessibility / culture", "Logistics / tech / format",
        "More training / follow-up", "Youth / schools / family", "Presenter / facilitator",
    ],
}

UNCODED = "Uncoded"
_COMPILED = {t: [re.compile(p, re.IGNORECASE) for p in ps] for t, ps in THEMES.items()}


def themes_for(column: str | None) -> list[str]:
    return THEMES_BY_COLUMN.get(column or "", list(THEMES))


def code_responses(series: pd.Series, column: str | None = None) -> pd.DataFrame:
    """Boolean DataFrame: one row per response, one column per theme."""
    text = series.astype("string")
    out = pd.DataFrame(index=series.index)
    for theme in themes_for(column):
        patterns = _COMPILED[theme]
        out[theme] = text.map(
            lambda s: bool(pd.notna(s) and any(p.search(s) for p in patterns))
        ).astype(bool)
    answered = text.notna()
    out[UNCODED] = answered & ~out.any(axis=1)
    out["answered"] = answered
    return out


def theme_summary(series: pd.Series, column: str | None = None) -> pd.DataFrame:
    """Count and % of answered responses per theme (multi-label, so % can sum >100).
    `column` (e.g. "text_improve") selects the theme set; default = all themes."""
    coded = code_responses(series, column)
    n = int(coded.pop("answered").sum())
    counts = coded[coded.index.isin(series.dropna().index)].sum()
    df = pd.DataFrame({"theme": counts.index, "count": counts.values.astype(int)})
    df["pct_of_answered"] = (df["count"] / n * 100).round(1) if n else float("nan")
    df["n_answered"] = n
    df["under_min_n"] = df["count"] < C.MIN_N  # too few mentions to report on its own
    return df.sort_values("count", ascending=False).reset_index(drop=True)


def run_all(res: CleanResult) -> dict[str, pd.DataFrame]:
    return {col: theme_summary(res.df[col], col) for col in res.text_cols}


def main() -> None:
    res = load_and_clean()
    C.OUTPUT_DIR.mkdir(exist_ok=True)
    for col, table in run_all(res).items():
        table.to_csv(C.OUTPUT_DIR / f"themes_{col}.csv", index=False)
        uncoded = table.loc[table["theme"] == UNCODED, "pct_of_answered"]
        print(f"{col}: {table['n_answered'].iloc[0]} answered; "
              f"{float(uncoded.iloc[0]) if len(uncoded) else 0:.1f}% uncoded "
              f"-> outputs/themes_{col}.csv")
        print(f"   question: {res.label(col)}")


if __name__ == "__main__":
    main()
