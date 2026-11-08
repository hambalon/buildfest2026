"""Summary statistics for the cleaned survey.

Usage (from the repo root):
    python -m src.analyze            # writes CSV tables + outputs/summary_report.xlsx

Every table is aggregate-only. Small-group rule: any group with n < MIN_N
(src/config.py, default 10) has its metrics blanked and `suppressed = True`, and
each metric is also blanked when fewer than MIN_N people in the group answered it.
`export_tables()` additionally replaces every count below MIN_N with "<10", and is
what the dashboard download and summary_report.xlsx use.

Main tables (see docs/METHODS.md for definitions):
    overall            headline numbers
    retro_change       before (retrospective) vs after, per outcome item
    by_<group>         metrics by audience / county / role / language
    county_by_audience metrics for each county x audience cell
    group_tests        are differences between groups larger than chance?
    trend[_by_audience] metrics per quarter (or month)
    intent_gap         likelihood to call 988 by self-rated knowledge
    sessions           session scorecard (training date x county) with alert flags
    quality            data-quality checks
    sensitivity        before/after results with and without straight-line responders
    subset_988         are the people who answered the 988 question different? (stage 03)
    ceiling            share already at the top before; change among everyone else (stage 03)
"""
from __future__ import annotations

import pandas as pd

from src import config as C
from src.clean import NOT_REPORTED, SMALL_GROUP, CleanResult, group_small, load_and_clean, save_outputs

try:
    from scipy import stats
except ImportError:  # scipy is optional; tests and p-values are skipped without it
    stats = None

SMALL = f"<{C.MIN_N}"
NAN = float("nan")


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def top_box(s: pd.Series) -> float:
    s = s.dropna().astype(float)
    return float((s >= C.TOP_BOX_MIN).mean() * 100) if len(s) else NAN


def pct_likely_988(res: CleanResult, s: pd.Series) -> float:
    """% likely to call 988: 4-5 on a 1-5 label scale, or >= CALL_988_LIKELY_MIN_0_10 on 0-10."""
    if res.call_988_scale == "0-10":
        s = s.dropna().astype(float)
        return float((s >= C.CALL_988_LIKELY_MIN_0_10).mean() * 100) if len(s) else NAN
    return top_box(s)


def is_likely_988(res: CleanResult, s: pd.Series) -> pd.Series:
    cut = C.CALL_988_LIKELY_MIN_0_10 if res.call_988_scale == "0-10" else C.TOP_BOX_MIN
    return s.astype(float) >= cut


def nps(s: pd.Series) -> float:
    """Net Promoter Score: % 9-10 minus % 0-6."""
    s = s.dropna().astype(float)
    if not len(s):
        return NAN
    return float(((s >= 9).mean() - (s <= 6).mean()) * 100)


def person_retro_change(res: CleanResult, df: pd.DataFrame) -> pd.Series:
    """Each respondent's average (after - before) across all paired items."""
    diffs = [df[l].astype(float) - df[r].astype(float)
             for r, l in res.retro_pairs.items() if l]
    if not diffs:
        return pd.Series(NAN, index=df.index)
    return pd.concat(diffs, axis=1).mean(axis=1)


def outcome_cols(res: CleanResult) -> list[str]:
    return [c for c in res.likert_cols if c.startswith("outcome_")]


def delivery_cols(res: CleanResult) -> list[str]:
    return [c for c in res.likert_cols if c.startswith("aspect_")]


def _avg_top_box(df: pd.DataFrame, cols: list[str]) -> tuple[float, int]:
    """Average % agree across items, and the smallest number answering any one item."""
    if not cols:
        return NAN, 0
    vals = [top_box(df[c]) for c in cols]
    n = min(int(df[c].notna().sum()) for c in cols)
    vals = [v for v in vals if v == v]
    return (sum(vals) / len(vals) if vals else NAN), n


def straight_liners(res: CleanResult, df: pd.DataFrame) -> pd.Series:
    """True for people who gave the identical answer to every agree/disagree item."""
    cols = res.likert_cols + list(res.retro_pairs)
    if not cols:
        return pd.Series(False, index=df.index)
    block = df[cols]
    return block.notna().all(axis=1) & block.nunique(axis=1).eq(1)


def _mask(value, n):
    return value if n >= C.MIN_N else NAN


# --------------------------------------------------------------------------- #
# Headline + before/after
# --------------------------------------------------------------------------- #
def overall(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Headline numbers. A metric answered by fewer than MIN_N people is blanked
    (its "n answered" row stays, so callers can show "n<10")."""
    df = res.df if df is None else df
    rows = [("Responses", len(df))]

    def block(n_name, n, metrics):
        ok = n >= C.MIN_N
        return [(n_name, n)] + [(name, fn() if ok else NAN) for name, fn in metrics]

    if "recommend" in df:
        s = df["recommend"]
        rows += block("Recommend: n answered", int(s.notna().sum()), [
            ("Recommend: mean (0-10)", lambda: round(s.astype(float).mean(), 2)),
            ("Net Promoter Score", lambda: round(nps(s), 1))])
    if "call_988" in df:
        s = df["call_988"]
        metrics = [("Likely to call 988: % likely", lambda: round(pct_likely_988(res, s), 1))]
        if res.call_988_scale == "0-10":
            metrics += [("Likely to call 988: mean (0-10)", lambda: round(s.astype(float).mean(), 2))]
        rows += block("Likely to call 988: n answered", int(s.notna().sum()), metrics)
    if res.retro_pairs:
        ch = person_retro_change(res, df)
        rows += block("Retro change: n with any pair", int(ch.notna().sum()), [
            ("Retro change: mean points (1-5 scale)", lambda: round(ch.mean(), 2)),
            ("Retro change: % who improved on average",
             lambda: round((ch.dropna() > 0).mean() * 100, 1))])
    oc = outcome_cols(res)
    if oc:
        after, n_after = _avg_top_box(df, oc)
        before, _ = _avg_top_box(df, [r for r, l in res.retro_pairs.items() if l])
        rows += block("Knowledge: n answered", n_after, [
            ("Knowledge: % agree after (avg of outcome items)", lambda: round(after, 1)),
            ("Knowledge: % agree before (avg, retrospective)", lambda: round(before, 1))])
    dc = delivery_cols(res)
    if dc:
        dv, n_dv = _avg_top_box(df, dc)
        rows += block("Delivery: n answered", n_dv, [
            ("Delivery: % agree (avg of presenter/organization items)", lambda: round(dv, 1))])
    return pd.DataFrame(rows, columns=["metric", "value"])


def retro_change(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Before (retrospective) vs after for each paired item. Uses only people who
    answered both halves of the pair."""
    df = res.df if df is None else df
    rows = []
    for rcol, lcol in res.retro_pairs.items():
        if not lcol:
            continue
        pair = df[[rcol, lcol]].dropna().astype(float)
        n = len(pair)
        d = pair[lcol] - pair[rcol]
        row = {
            "item": lcol,
            "question_after": res.label(lcol),
            "question_before": res.label(rcol),
            "n": n,
            "suppressed": n < C.MIN_N,
            "before_mean": pair[rcol].mean(),
            "after_mean": pair[lcol].mean(),
            "change": d.mean(),
            "pct_improved": (d > 0).mean() * 100 if n else NAN,
            "pct_same": (d == 0).mean() * 100 if n else NAN,
            "pct_declined": (d < 0).mean() * 100 if n else NAN,
            "top_box_before": top_box(pair[rcol]),
            "top_box_after": top_box(pair[lcol]),
            "pct_at_ceiling_before": (pair[rcol] == 5).mean() * 100 if n else NAN,
            "wilcoxon_p": NAN,
        }
        if stats is not None and n >= C.MIN_N and (d != 0).any():
            row["wilcoxon_p"] = float(stats.wilcoxon(d[d != 0]).pvalue)
        if row["suppressed"]:
            for k in row:
                if k not in ("item", "question_after", "question_before", "n", "suppressed"):
                    row[k] = NAN
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    num = out.columns.difference(["item", "question_after", "question_before", "n", "suppressed", "wilcoxon_p"])
    out[num] = out[num].round(3)
    return out  # wilcoxon_p left unrounded: tiny values would show as 0


# --------------------------------------------------------------------------- #
# Groups
# --------------------------------------------------------------------------- #
GROUPS = ("audience", "county", "role", "language")


def _metrics(res: CleanResult, g: pd.DataFrame) -> dict:
    """Metrics for one group. Each metric is blanked if fewer than MIN_N people in
    the group answered that question (its n_* column says how many did)."""
    m = {}

    def put(name, n, value):
        m[name] = value if n >= C.MIN_N else NAN

    if "recommend" in g:
        n = int(g["recommend"].notna().sum())
        m["n_recommend"] = n
        put("recommend_mean", n, g["recommend"].astype(float).mean())
        put("nps", n, nps(g["recommend"]))
    if "call_988" in g:
        n = int(g["call_988"].notna().sum())
        m["n_988"] = n
        put("pct_likely_988", n, pct_likely_988(res, g["call_988"]))
    if res.retro_pairs:
        ch = person_retro_change(res, g)
        n = int(ch.notna().sum())
        m["n_retro"] = n
        put("retro_change_mean", n, ch.mean())
    for col in res.likert_cols:
        n = int(g[col].notna().sum())
        m[f"n_agree_{col}"] = n
        put(f"pct_agree_{col}", n, top_box(g[col]))
    return m


def _grouped_frame(df: pd.DataFrame, group: str) -> pd.DataFrame | None:
    """df with a 'group' column for the requested grouping (roles exploded)."""
    if group == "role":
        if "role_list" not in df:
            return None
        ex = df.explode("role_list")
        ex["group"] = group_small(ex["role_list"].replace("", pd.NA))
        return ex.reset_index().drop_duplicates(["index", "group"]).set_index("index")
    col = "audience" if group == "audience" else f"{group}_grp"
    if col not in df:
        return None
    return df.assign(group=df[col].astype("string").fillna(NOT_REPORTED))


def by_group(res: CleanResult, group: str, df: pd.DataFrame | None = None,
             split: str | None = None) -> pd.DataFrame:
    """Metrics per group with n and suppression.

    group: 'audience', 'county', 'role' or 'language'.
    split: optional second grouping ('audience' is the useful one), giving one row
           per group x split cell. Every cell follows the n >= MIN_N rule.
    """
    df = res.df if df is None else df
    ex = _grouped_frame(df, group)
    if ex is None:
        return pd.DataFrame()
    keys = ["group"]
    if split:
        if split not in ex:
            return pd.DataFrame()
        ex = ex.assign(split=ex[split].astype("string").fillna(NOT_REPORTED))
        keys.append("split")

    rows = []
    for name, g in ex.groupby(keys, observed=True):
        name = name if isinstance(name, tuple) else (name,)
        row = dict(zip(keys, name))
        row.update({"n": len(g), "suppressed": len(g) < C.MIN_N})
        metrics = _metrics(res, g)
        if row["suppressed"]:  # hide everything, including the per-metric n's
            metrics = {k: NAN for k in metrics}
        rows.append({**row, **metrics})
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).sort_values(keys[:1] + ["n"], ascending=[True, False]) if split \
        else pd.DataFrame(rows).sort_values("n", ascending=False)
    return out.round(2).reset_index(drop=True)


def _effect_label(kind: str, value: float) -> str:
    if value != value:
        return ""
    v = abs(value)
    cuts = (0.1, 0.3, 0.5) if kind == "r" else (0.01, 0.06, 0.14)  # rank-biserial r / epsilon^2
    return "negligible" if v < cuts[0] else "small" if v < cuts[1] else "medium" if v < cuts[2] else "large"


def group_tests(res: CleanResult, group: str | None = None, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Are differences between groups bigger than chance?

    Uses groups with at least MIN_N answers (pooled "Other"/"Not reported" groups
    excluded). Two groups: Mann-Whitney U with rank-biserial r. Three or more:
    Kruskal-Wallis H with epsilon-squared. Both are rank-based, which suits 0-10
    and 1-5 survey scales. For roles, multi-role respondents appear in several
    groups, so treat role p-values as approximate.
    """
    df = res.df if df is None else df
    if stats is None:
        return pd.DataFrame()
    if group is None:  # every grouping, stacked, with a 'grouping' column
        parts = [group_tests(res, g, df).assign(grouping=g) for g in GROUPS]
        parts = [p for p in parts if not p.empty]
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    ex = _grouped_frame(df, group)
    if ex is None:
        return pd.DataFrame()
    ex = ex.assign(_change=person_retro_change(res, ex))
    metrics = [("recommend", "Likelihood to recommend (0-10)"),
               ("_change", "Before → after change (points)"),
               ("call_988", "Likelihood to call 988")]
    if delivery_cols(res):
        ex = ex.assign(_delivery=ex[delivery_cols(res)].astype(float).mean(axis=1))
        metrics.append(("_delivery", "Delivery rating (avg of presenter/organization items, 1-5)"))
    rows = []
    for col, label in metrics:
        if col not in ex:
            continue
        samples = {}
        for name, g in ex.groupby("group", observed=True):
            if name in (SMALL_GROUP, NOT_REPORTED):
                continue
            vals = g[col].dropna().astype(float)
            if len(vals) >= C.MIN_N:
                samples[name] = vals
        if len(samples) < 2:
            continue
        names, vals = list(samples), list(samples.values())
        n_total = sum(len(v) for v in vals)
        if len(vals) == 2:
            u = stats.mannwhitneyu(vals[0], vals[1], alternative="two-sided")
            effect = 1 - 2 * u.statistic / (len(vals[0]) * len(vals[1]))
            test, stat, kind = "Mann-Whitney U", float(u.statistic), "r"
            p = float(u.pvalue)
        else:
            h = stats.kruskal(*vals)
            k = len(vals)
            effect = (h.statistic - k + 1) / (n_total - k) if n_total > k else NAN
            test, stat, kind = "Kruskal-Wallis H", float(h.statistic), "e2"
            p = float(h.pvalue)
        rows.append({
            "metric": label, "groups_compared": ", ".join(map(str, names)),
            "n": n_total, "test": test, "statistic": round(stat, 2), "p_value": p,
            "effect_size": round(effect, 3), "effect": _effect_label(kind, effect),
            "verdict": ("Likely a real difference" if p < 0.05 else "Could be chance"),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Robustness checks (stage 03, added by a teammate; kept unchanged)
# --------------------------------------------------------------------------- #
def _p(test, a: pd.Series, b: pd.Series) -> float:
    a, b = a.dropna().astype(float), b.dropna().astype(float)
    if test is None or len(a) < C.MIN_N or len(b) < C.MIN_N:
        return float("nan")
    try:
        return float(test(a, b).pvalue)
    except ValueError:  # e.g. all values identical
        return float("nan")


def subset_988(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Are the people who answered the 988 question (added to the form later) different
    from everyone else? Compares recommend and retro change; Mann-Whitney U p-values."""
    df = res.df if df is None else df
    if "call_988" not in df:
        return pd.DataFrame()
    answered = df["call_988"].notna()
    ch = person_retro_change(res, df)
    parts = {"Answered 988 question": answered, "Did not answer 988 question": ~answered}
    rows = []
    for name, m in parts.items():
        g, c = df[m], ch[m]
        row = {"subset": name, "n": int(m.sum())}
        if "recommend" in g:
            r = g["recommend"].astype(float)
            n_r = int(r.notna().sum())
            row |= {"n_recommend": n_r,
                    "recommend_mean": round(r.mean(), 2) if n_r >= C.MIN_N else float("nan"),
                    "nps": round(nps(r), 1) if n_r >= C.MIN_N else float("nan")}
        n_c = int(c.notna().sum())
        row |= {"n_retro": n_c,
                "retro_change_mean": round(c.mean(), 2) if n_c >= C.MIN_N else float("nan"),
                "pct_improved": round((c.dropna() > 0).mean() * 100, 1) if n_c >= C.MIN_N else float("nan")}
        rows.append(row)
    out = pd.DataFrame(rows)
    a, b = answered, ~answered
    p = {"p_recommend": _p(stats.mannwhitneyu if stats else None, df.loc[a, "recommend"], df.loc[b, "recommend"])
         if "recommend" in df else float("nan"),
         "p_retro_change": _p(stats.mannwhitneyu if stats else None, ch[a], ch[b])}
    for k, v in p.items():
        out[k] = v  # same p on both rows (it compares the two)
    return out


def ceiling(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Share already at the top (5) before the training, who can't improve, and the
    change among everyone else."""
    df = res.df if df is None else df
    rows = []
    for rcol, lcol in res.retro_pairs.items():
        if not lcol:
            continue
        pair = df[[rcol, lcol]].dropna().astype(float)
        below = pair[pair[rcol] < 5]
        d = below[lcol] - below[rcol]
        ok = len(below) >= C.MIN_N
        rows.append({
            "item": lcol, "question_after": res.label(lcol), "n": len(pair),
            "pct_at_5_before": round((pair[rcol] == 5).mean() * 100, 1) if len(pair) >= C.MIN_N else float("nan"),
            "n_below_5_before": len(below),
            "change_mean_below_5": round(d.mean(), 2) if ok else float("nan"),
            "pct_improved_below_5": round((d > 0).mean() * 100, 1) if ok else float("nan"),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Trends, intent, sessions
# --------------------------------------------------------------------------- #
def _period_metrics(res: CleanResult, g: pd.DataFrame) -> dict:
    n = len(g)
    agree, n_agree = _avg_top_box(g, outcome_cols(res))
    deliv, n_deliv = _avg_top_box(g, delivery_cols(res))
    ch = person_retro_change(res, g)
    n_rec = int(g["recommend"].notna().sum()) if "recommend" in g else 0
    n_988 = int(g["call_988"].notna().sum()) if "call_988" in g else 0
    m = {
        "n": n,
        "pct_students": (g["audience"].eq("Students").mean() * 100) if "audience" in g else NAN,
        "n_recommend": n_rec,
        "recommend_mean": _mask(g["recommend"].astype(float).mean(), n_rec) if n_rec else NAN,
        "nps": _mask(nps(g["recommend"]), n_rec) if n_rec else NAN,
        "pct_agree_after": _mask(agree, n_agree),
        "retro_change_mean": _mask(ch.mean(), int(ch.notna().sum())),
        "pct_delivery": _mask(deliv, n_deliv),
        "n_988": n_988,
        "pct_likely_988": _mask(pct_likely_988(res, g["call_988"]), n_988) if n_988 else NAN,
    }
    if n < C.MIN_N:
        m = {k: (v if k == "n" else NAN) for k, v in m.items()}
    return m


def trend(res: CleanResult, df: pd.DataFrame | None = None, period: str | None = None,
          by: str | None = None) -> pd.DataFrame:
    """Metrics per time period (default config.TREND_PERIOD), optionally split by
    a column such as 'audience'. Rows without a training date are left out."""
    df = res.df if df is None else df
    if "training_date" not in df or (by and by not in df):
        return pd.DataFrame()
    period = period or C.TREND_PERIOD
    d = df[df["training_date"].notna()]
    d = d.assign(period=d["training_date"].dt.to_period(period).astype(str))
    keys = ["period"] + ([by] if by else [])
    rows = []
    for name, g in d.groupby(keys, observed=True):
        name = name if isinstance(name, tuple) else (name,)
        rows.append({**dict(zip(keys, name)), **_period_metrics(res, g)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["suppressed"] = out["n"] < C.MIN_N
    return out.sort_values(keys).round(2).reset_index(drop=True)


def intent_gap(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Among people who answered the 988 question: % likely to call 988 for those
    who agree vs don't agree with each knowledge item, plus Spearman's rho."""
    df = res.df if df is None else df
    if "call_988" not in df:
        return pd.DataFrame()
    k = df[df["call_988"].notna()]
    rows = []
    for col in outcome_cols(res):
        sub = k[k[col].notna()]
        rho = p = NAN
        if stats is not None and len(sub) >= C.MIN_N and sub[col].nunique() > 1:
            r = stats.spearmanr(sub[col].astype(float), sub["call_988"].astype(float))
            rho, p = float(r.statistic), float(r.pvalue)
        for status, part in (("Agrees (4-5)", sub[sub[col] >= C.TOP_BOX_MIN]),
                             ("Does not agree (1-3)", sub[sub[col] < C.TOP_BOX_MIN])):
            n = len(part)
            rows.append({
                "item": col, "question": res.label(col), "knowledge": status, "n": n,
                "pct_likely_988": _mask(pct_likely_988(res, part["call_988"]), n),
                "mean_988": _mask(part["call_988"].astype(float).mean(), n),
                "spearman_rho": round(rho, 3) if rho == rho else NAN, "spearman_p": p,
            })
    return pd.DataFrame(rows).round({"pct_likely_988": 1, "mean_988": 2})


def session_scorecard(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per session (training date x county) with at least MIN_N responses.

    Flags sessions that need follow-up (thresholds in config); flagged sessions come
    first. `thin` marks sessions under THIN_N responses, where a flag is more likely
    to be chance. `attrs` carries how
    many sessions / responses were too small to show.
    """
    df = res.df if df is None else df
    if "training_date" not in df:
        return pd.DataFrame()
    d = df[df["training_date"].notna()]
    county = d["county_grp"] if "county_grp" in d else pd.Series("All", index=d.index)
    rows, hidden_sessions, hidden_resp = [], 0, 0
    for (date, cty), g in d.groupby([d["training_date"].dt.date, county], observed=True):
        if len(g) < C.MIN_N:
            hidden_sessions += 1
            hidden_resp += len(g)
            continue
        m = _period_metrics(res, g)
        flags = []
        if m["nps"] == m["nps"] and m["nps"] < C.SESSION_ALERT_NPS_BELOW:
            flags.append("Low recommend score")
        if m["pct_agree_after"] == m["pct_agree_after"] and m["pct_agree_after"] < C.SESSION_ALERT_AGREE_BELOW:
            flags.append("Low knowledge after training")
        if m["pct_delivery"] == m["pct_delivery"] and m["pct_delivery"] < C.SESSION_ALERT_DELIVERY_BELOW:
            flags.append("Low delivery rating")
        rows.append({"date": pd.Timestamp(date), "county": cty, **m,
                     "flags": "; ".join(flags), "needs_follow_up": bool(flags),
                     "thin": len(g) < C.THIN_N})  # small session: a flag may be chance, read with care
    out = pd.DataFrame(rows)
    if not out.empty:
        # Flagged sessions first (what staff act on), then newest first.
        out = (out.sort_values(["needs_follow_up", "date"], ascending=[False, False])
               .round(1).reset_index(drop=True))
    out.attrs.update(hidden_sessions=hidden_sessions, hidden_responses=hidden_resp)
    return out


# --------------------------------------------------------------------------- #
# Data quality and robustness
# --------------------------------------------------------------------------- #
def quality_checks(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = res.df if df is None else df
    n = len(df)
    pct = lambda k: round(k / n * 100, 1) if n else NAN
    rows = [("Responses", n, "")]
    sl = straight_liners(res, df)
    rows.append(("Same answer to every agree/disagree item", f"{pct(int(sl.sum()))}%",
                 "Possible low-effort responding; results are re-run without them in the sensitivity table"))
    if res.retro_pairs:
        d = pd.concat([df[l].astype(float) - df[r].astype(float)
                       for r, l in res.retro_pairs.items() if l], axis=1)
        rows.append(("Rated themselves lower after than before (any item)",
                     f"{pct(int((d < 0).any(axis=1).sum()))}%",
                     "Often a misread retrospective question; kept in all results"))
        before = df[[r for r, l in res.retro_pairs.items() if l]]
        rows.append(("Already 'Strongly agree' before on every item",
                     f"{pct(int((before == 5).all(axis=1).sum()))}%",
                     "Ceiling: these people cannot show improvement"))
    for col, label in (("call_988", "Answered the 988 likelihood question"),
                       ("recommend", "Answered the recommend question"),
                       ("training_date", "Has a usable training date")):
        if col in df:
            rows.append((label, f"{pct(int(df[col].notna().sum()))}%", ""))
    for col in delivery_cols(res)[:1]:
        rows.append(("Answered the delivery items", f"{pct(int(df[col].notna().sum()))}%",
                     "Non-standard labels are counted as missing (config.NONSTANDARD_AGREE_LABELS)"))
    return pd.DataFrame(rows, columns=["check", "value", "note"]).astype({"value": "string"})


def sensitivity(res: CleanResult, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Before/after results for everyone vs excluding straight-line responders."""
    df = res.df if df is None else df
    sl = straight_liners(res, df)
    parts = []
    for name, sub in (("All respondents", df), ("Excluding same-answer responders", df[~sl])):
        rc = retro_change(res, sub)
        if rc.empty:
            continue
        parts.append(rc[["item", "n", "top_box_before", "top_box_after", "change"]].assign(sample=name))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


# --------------------------------------------------------------------------- #
# Everything, and privacy-safe export
# --------------------------------------------------------------------------- #
def run_all(res: CleanResult, df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    df = res.df if df is None else df
    out = {"overall": overall(res, df), "retro_change": retro_change(res, df)}
    for g in GROUPS:
        out[f"by_{g}"] = by_group(res, g, df)
    out["county_by_audience"] = by_group(res, "county", df, split="audience")
    out["group_tests"] = group_tests(res, None, df)
    out["subset_988"] = subset_988(res, df)
    out["ceiling"] = ceiling(res, df)
    out["trend"] = trend(res, df)
    out["trend_monthly"] = trend(res, df, period="M")
    out["trend_by_audience"] = trend(res, df, by="audience")
    out["intent_gap"] = intent_gap(res, df)
    out["sessions"] = session_scorecard(res, df)
    out["quality"] = quality_checks(res, df)
    out["sensitivity"] = sensitivity(res, df)
    return out


def safe_table(t: pd.DataFrame) -> pd.DataFrame:
    """Copy of an aggregate table where every count below MIN_N reads "<10" and
    suppressed rows show no counts at all. Use for anything shown or exported."""
    if t is None or t.empty:
        return t
    t = t.copy()
    for c in [c for c in t.columns if c == "n" or c.startswith("n_") or c == "count"]:
        num = pd.to_numeric(t[c], errors="coerce")
        out = num.round().astype("Int64").astype("string")
        out[num < C.MIN_N] = SMALL
        if "suppressed" in t:
            out[t["suppressed"].astype(bool)] = SMALL if c == "n" else pd.NA
        t[c] = out
    return t


def safe_overall(ov: pd.DataFrame) -> pd.DataFrame:
    ov = ov.copy()
    ov["value"] = ov["value"].astype(object)
    is_n = ov["metric"].str.contains(": n ") | (ov["metric"] == "Responses")
    small = is_n & (pd.to_numeric(ov["value"], errors="coerce") < C.MIN_N)
    ov.loc[small, "value"] = SMALL
    return ov


def export_tables(res: CleanResult, df: pd.DataFrame | None = None,
                  extra: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    """All aggregate tables, made safe for sharing (no counts below MIN_N, no rows)."""
    tables = run_all(res, df)
    tables.update(extra or {})
    return safe_tables(tables)


def safe_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply safe_table / safe_overall to a dict of already-computed tables."""
    safe = {}
    for name, t in tables.items():
        if t is None or t.empty:
            continue
        safe[name] = safe_overall(t) if name == "overall" else safe_table(t)
    return safe


def write_excel(tables: dict[str, pd.DataFrame], path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, t in tables.items():
            t2 = t.copy()
            for c in t2.columns:  # Excel can't store tz-aware or Period types
                if str(t2[c].dtype).startswith(("period", "datetime64[ns,")):
                    t2[c] = t2[c].astype(str)
            t2.to_excel(xw, sheet_name=name[:31], index=False)


def main() -> None:
    from src import text_themes

    res = load_and_clean()
    save_outputs(res)
    raw_tables = run_all(res)
    for name, t in raw_tables.items():
        if t is not None and not t.empty:
            t.to_csv(C.OUTPUT_DIR / f"{name}.csv", index=False)
    themes = {f"themes_{c}": t for c, t in text_themes.run_all(res).items()}
    safe = export_tables(res, extra=themes)
    write_excel(safe, C.OUTPUT_DIR / "summary_report.xlsx")
    n_supp = sum(int(t["suppressed"].sum()) for t in raw_tables.values()
                 if t is not None and "suppressed" in t)
    print(f"Analyzed {len(res.df)} responses from {res.source_file}")
    print(f"Wrote {len(raw_tables)} tables to {C.OUTPUT_DIR}/ ({n_supp} rows suppressed for n<{C.MIN_N})")
    print(f"Shareable workbook (counts <{C.MIN_N} hidden): {C.OUTPUT_DIR / 'summary_report.xlsx'}")


if __name__ == "__main__":
    main()
