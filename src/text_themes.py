"""Keyword-based theme coding for the two open-text questions.

Usage (from the repo root):
    python -m src.text_themes        # writes outputs/themes_<question>.csv (+ by audience)

How it works: THEMES_BY_COLUMN holds, per question, an ordered dict of
theme -> regex patterns (English + Spanish). Each answer is checked against every
pattern; one answer can get several themes. Answers matching nothing count as
"Other / uncoded". Coverage and accuracy are checked with
`python scripts/validate_themes.py` (hand-coded sample vs. this coder).

How the themes were built (privacy-preserving): the team never pasted answers into
an AI tool. Instead, word and two-word-phrase counts were computed locally, keeping
only ordinary dictionary words that appear in at least 10 different answers (so no
names or one-off details), and themes were written from those counts. Edit the
patterns here when new data brings new topics; rerun the validator after changes.
"""
from __future__ import annotations

import re

import pandas as pd

from src import config as C
from src.clean import CleanResult, load_and_clean

UNCODED = "Other / uncoded"

# ---- "What was the most valuable thing you learned during the training?" -----
VALUABLE: dict[str, list[str]] = {
    "Anyone can call (any age, any reason)": [
        r"\bany ?one (can|could|is able)\b", r"\beveryone\b", r"\beverybody\b", r"\bany age\b",
        r"\b(for|to) (all|anyone|everyone)\b", r"\bany (person|reason|situation|problem|issue)\b",
        r"\bnot (just|only) (for )?(suicid|people|those|when)", r"\beven if\b",
        r"\bdoesn'?t have to be\b", r"\bdon'?t have to be\b", r"\b(any|other) (mental|emotional)\b",
        r"\bcualquier(a| persona)?\b", r"\btodos\b",
    ],
    "Always available (24/7, call or text)": [
        r"\b24 ?/ ?7\b", r"\b24 hours\b", r"\balways\b", r"\bany ?time\b", r"\bwhenever\b",
        r"\b(is|always|stays) open\b", r"\bday or night\b", r"\bavailable\b", r"\bsiempre\b",
        r"\btext(ing|ed)?\b", r"\bchat\b", r"\bmensaje",
    ],
    "How 988 works (vs. 911, who answers, what happens)": [
        r"\bhow (988|it) works\b", r"\b988 works\b", r"\bwhat (988|it) (is|does)\b",
        r"\bwhat happens\b", r"\b911\b", r"\bdifference\b", r"\bpolice\b", r"\bcops?\b",
        r"\bcounsel(or|ors|ing)\b", r"\btrained\b", r"\bconfidential\b", r"\banonymous\b",
        r"\bfree\b", r"\bwho (answers|picks up|you talk)\b", r"\breal (person|people)\b",
        r"\bc[oó]mo funciona\b",
    ],
    "988 exists / the number to call": [
        r"\b(can|could|should|to|you) call\b", r"\bcall(ing)? 988\b", r"\b988 is\b",
        r"\bthe number\b", r"\bphone number\b", r"\b3 digit", r"\bthree digit", r"\beasy to remember\b",
        r"\b(didn'?t|did not|never) know\b", r"\bthere is\b", r"\bexists?\b", r"\bllamar\b",
    ],
    "Calling for someone else / helping others": [
        r"\bsomeone else\b", r"\b(for|about|on behalf of) (someone|somebody|a friend|friends|others|"
        r"other people|a loved one|family|a family member)\b", r"\bhelp (others|a friend|someone|"
        r"people|my friends?)\b", r"\bif (someone|a friend|somebody)\b", r"\botra persona\b",
    ],
    "It's okay to reach out / talk": [
        r"\bok(ay)? to\b", r"\breach(ing)? out\b", r"\b(ask|asking) for help\b", r"\bget(ting)? help\b",
        r"\bneed(s|ed)? help\b", r"\bnot alone\b", r"\btalk (to|with) (someone|somebody|people)\b",
        r"\bsomeone to talk\b", r"\bpedir ayuda\b", r"\bno (estas|estás) sol",
    ],
    "Mental health and crisis awareness": [
        r"\bmental health\b", r"\bsuicid", r"\bcrisis\b", r"\bwarning signs?\b", r"\bsigns?\b",
        r"\bstigma\b", r"\bmatters?\b", r"\bsalud mental\b", r"\bse[ñn]ales\b",
    ],
    "Resources and support options": [
        r"\bresources?\b", r"\brecursos\b", r"\bsupport\b", r"\bservices?\b", r"\bhotline\b",
        r"\blifeline\b", r"\bhandouts?\b",
    ],
    "Everything / all of it": [
        r"^\s*(everything|all of it|all|the whole (thing|training)|todo)\b",
    ],
}

# ---- "How can we improve this training in the future?" ------------------------
IMPROVE: dict[str, list[str]] = {
    "No changes / it was good": [
        r"^\s*(nothing|nada|no|n/?a|none|nope|idk|i don'?t know|not sure|no changes?|"
        r"no suggestions?|all good|it'?s good|it was good|good|great|perfect|fine)\W*$",
        r"^\s*(nothing|none|nada|not really|no|honestly nothing)\b",
        r"\b(it was|everything was|this was|was|very|really|so) (great|perfect|excellent|good|wonderful|"
        r"amazing|awesome|informative|helpful|fun|well done)\b",
        r"\bgood job\b", r"\bgreat job\b", r"\bkeep (it|doing|up)\b", r"\bnothing (to|i would|needs)\b",
        r"\b(todo|muy) bien\b", r"^\s*bien\b", r"\bexcelente\b", r"\bno (changes|suggestions)\b",
    ],
    # A question mark is the objective marker (checked: 177 of the first 226 matches had
    # one). Openings like "do..." / "can..." / "how..." are NOT used: they are often
    # suggestions ("Do more activities").
    "Asked a question about 988": [
        r"\?", r"^\s*(what|why|who|where|does|is|are)\b", r"\bhow (many|much|long|do|does|did)\b",
        r"\bwhat happens\b", r"\bi (have|had) a question\b", r"\bwonder(ing)?\b", r"\bcurious\b",
    ],
    "More engaging / interactive": [
        r"\binteractive\b", r"\binteract", r"\bengag", r"\bactivit", r"\bgames?\b", r"\bfun(ner)?\b",
        r"\bboring\b", r"\bvideos?\b", r"\brole[- ]?plays?\b", r"\bscenarios?\b", r"\bexamples?\b",
        r"\bstories\b", r"\bhands[- ]on\b", r"\bkahoot\b", r"\bpractice\b", r"\bejemplos?\b",
    ],
    "More information / depth": [
        r"\bmore (info|information|details?|about|facts|statistics|stats|depth|content)\b",
        r"\bexplain\b", r"\bstatistics\b", r"\bstats\b", r"\breal (stories|life|examples|calls)\b",
        r"\bmore on\b", r"\bdeeper\b", r"\bm[aá]s informaci[oó]n\b",
    ],
    "Length / pacing": [
        r"\blonger\b", r"\bshorter\b", r"\bmore time\b", r"\btoo (long|short|fast|slow|much)\b",
        r"\brushed\b", r"\bpac(e|ing)\b", r"\bquicker\b", r"\bfaster\b", r"\bm[aá]s tiempo\b",
    ],
    "Presenter / delivery": [
        r"\bpresenters?\b", r"\bspeakers?\b", r"\bfacilitators?\b", r"\btrainers?\b",
        r"\blouder\b", r"\bspeak(ing)?\b", r"\bvoice\b", r"\benergy\b", r"\benthusias",
        r"\bmonoton", r"\bread(ing)? (off|from) the\b",
    ],
    "Reach more people / promote 988": [
        r"\b(spread|share|promote|advertis\w*|post|tell)\b.*\b(word|988|people|everyone|schools?)\b",
        r"\b(more|other|every) (schools?|classes|places|communities|students)\b",
        r"\beveryone should\b", r"\bmore often\b", r"\bsocial media\b", r"\bposters?\b",
        r"\bflyers?\b", r"\breach (more|out to)\b",
    ],
    "Logistics / tech / format": [
        r"\bzoom\b", r"\bvirtual\b", r"\bin[- ]person\b", r"\baudio\b", r"\bsound\b", r"\bmic\b",
        r"\bslides?\b", r"\btechnical\b", r"\broom\b", r"\bschedul", r"\bpowerpoint\b", r"\bscreen\b",
    ],
    "Language / accessibility": [
        r"\bspanish\b", r"\bespa[ñn]ol\b", r"\btranslat", r"\binterpret", r"\blanguages?\b",
        r"\bcultur", r"\baccessib", r"\bcaptions?\b",
    ],
    "Resources / handouts": [
        r"\bresources?\b", r"\bhandouts?\b", r"\bmaterials?\b", r"\bpamphlets?\b", r"\bcards?\b",
        r"\bmagnets?\b", r"\bstickers?\b", r"\brecursos\b",
    ],
}

THEMES_BY_COLUMN: dict[str, dict[str, list[str]]] = {
    "text_valuable": VALUABLE,
    "text_improve": IMPROVE,
}
# Columns not listed (e.g. a new open-text question) use every theme from both sets.
ALL_THEMES: dict[str, list[str]] = {**VALUABLE, **IMPROVE}

_COMPILED: dict[str, dict[str, list[re.Pattern]]] = {
    col: {t: [re.compile(p, re.IGNORECASE) for p in ps] for t, ps in themes.items()}
    for col, themes in {**THEMES_BY_COLUMN, "_all": ALL_THEMES}.items()
}


def themes_for(column: str | None) -> dict[str, list[re.Pattern]]:
    return _COMPILED.get(column or "", _COMPILED["_all"])


def code_responses(series: pd.Series, column: str | None = None) -> pd.DataFrame:
    """Boolean DataFrame: one row per response, one column per theme, plus
    UNCODED and 'answered'."""
    text = series.astype("string")
    out = pd.DataFrame(index=series.index)
    for theme, patterns in themes_for(column).items():
        out[theme] = text.map(
            lambda s: bool(pd.notna(s) and any(p.search(s) for p in patterns))
        ).astype(bool)
    answered = text.notna()
    out[UNCODED] = answered & ~out.any(axis=1)
    out["answered"] = answered
    return out


def theme_summary(series: pd.Series, column: str | None = None) -> pd.DataFrame:
    """Count and % of answered responses per theme (multi-label, so % can sum >100).
    `under_min_n` marks themes with fewer than MIN_N mentions (don't report alone)."""
    coded = code_responses(series, column)
    n = int(coded.pop("answered").sum())
    counts = coded.sum()
    df = pd.DataFrame({"theme": counts.index, "count": counts.values.astype(int)})
    df["pct_of_answered"] = (df["count"] / n * 100).round(1) if n else float("nan")
    df["n_answered"] = n
    df["under_min_n"] = df["count"] < C.MIN_N
    # Keep "Other / uncoded" last regardless of size
    df["_last"] = df["theme"].eq(UNCODED)
    df = df.sort_values(["_last", "count"], ascending=[True, False]).drop(columns="_last")
    return df.reset_index(drop=True)


def theme_by_group(df: pd.DataFrame, column: str, group: str = "audience") -> pd.DataFrame:
    """Theme % per group (e.g. Students vs Adults). Groups with fewer than MIN_N
    answers are dropped; themes with fewer than MIN_N mentions in a group are blanked."""
    if group not in df:
        return pd.DataFrame()
    parts = []
    for name, g in df.groupby(group, observed=True):
        t = theme_summary(g[column], column)
        if not len(t) or int(t["n_answered"].iloc[0]) < C.MIN_N:
            continue
        t.loc[t["under_min_n"], ["count", "pct_of_answered"]] = float("nan")
        parts.append(t.assign(group=name))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def run_all(res: CleanResult, df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    df = res.df if df is None else df
    out = {col: theme_summary(df[col], col) for col in res.text_cols}
    for col in res.text_cols:
        out[f"{col}_by_audience"] = theme_by_group(df, col, "audience")
    return out


def main() -> None:
    res = load_and_clean()
    C.OUTPUT_DIR.mkdir(exist_ok=True)
    for name, table in run_all(res).items():
        table.to_csv(C.OUTPUT_DIR / f"themes_{name}.csv", index=False)
    for col in res.text_cols:
        t = theme_summary(res.df[col], col)
        unc = float(t.loc[t["theme"] == UNCODED, "pct_of_answered"].iloc[0])
        print(f"{col}: {int(t['n_answered'].iloc[0])} answered; {unc:.1f}% uncoded "
              f"-> outputs/themes_{col}.csv")


if __name__ == "__main__":
    main()
